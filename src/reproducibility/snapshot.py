import json
import hashlib
import os
import copy
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from src.config import config
from src.cache import cache
from src.reproducibility.models import AnalysisSnapshot
from src.reproducibility.validators import filter_secrets, sanitize_filename

SNAPSHOT_CACHE_PREFIX = "repro_snapshot:"
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "results", "snapshots")

def _ensure_snapshot_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def canonicalize_snapshot_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a canonical, stable dictionary representation of the scientific analysis content.
    Strips non-deterministic transient fields (such as runtime UUIDs, UI state) and sorts keys recursively.
    """
    # Deepcopy to avoid mutating original payload
    data = copy.deepcopy(payload)
    
    # Filter out secrets
    data = filter_secrets(data)
    
    def _canonicalize_value(val: Any) -> Any:
        if isinstance(val, dict):
            # Exclude transient runtime attributes
            transient_keys = {"session_id", "ui_state", "request_id", "client_ip"}
            cleaned_dict = {
                k: _canonicalize_value(v)
                for k, v in val.items()
                if k not in transient_keys
            }
            return {k: cleaned_dict[k] for k in sorted(cleaned_dict.keys())}
        elif isinstance(val, list):
            # Process list items recursively
            canonical_list = [_canonicalize_value(item) for item in val]
            # If list contains dicts with known sort keys, sort them deterministically
            if canonical_list and isinstance(canonical_list[0], dict):
                first_dict = canonical_list[0]
                sort_key = None
                for candidate in ["medgen_uid", "symbol", "ncbi_gene_id", "rank", "node_id", "disease"]:
                    if candidate in first_dict:
                        sort_key = candidate
                        break
                if sort_key:
                    canonical_list.sort(key=lambda x: str(x.get(sort_key, "")))
            return canonical_list
        else:
            return val

    return _canonicalize_value(data)

def compute_snapshot_hash(canonical_dict: Dict[str, Any]) -> str:
    """
    Compute a 64-character SHA-256 hex digest of the canonicalized snapshot JSON payload.
    Ensures identical scientific content produces identical hashes.
    """
    json_bytes = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(json_bytes).hexdigest()

def create_analysis_snapshot(
    report_data: Dict[str, Any],
    workspace_data: Optional[Dict[str, Any]] = None
) -> AnalysisSnapshot:
    """
    Create an immutable AnalysisSnapshot from a report dictionary or analysis payload.
    Calculates deterministic canonical snapshot SHA-256 hash.
    """
    meta = report_data.get("report_metadata", {})
    query = meta.get("query") or report_data.get("query") or "multi_analysis"
    report_type = meta.get("report_type") or report_data.get("report_type") or "analysis"
    report_id = meta.get("report_id") or report_data.get("report_id")
    
    scope = report_data.get("analysis_scope", {})
    search_strategy = scope.get("search_strategy") or report_data.get("search_strategy") or "NCBI MedGen E-utilities term search"
    
    # Extract records & gene associations
    gene_analysis = report_data.get("gene_analysis", {})
    ranked_genes = gene_analysis.get("ranked_genes", []) if isinstance(gene_analysis, dict) else (gene_analysis or [])
    evidence = report_data.get("evidence", [])
    
    # User notes from workspace if applicable
    user_notes = []
    if workspace_data and isinstance(workspace_data, dict):
        raw_notes = workspace_data.get("notes", [])
        for note in raw_notes:
            if isinstance(note, dict):
                user_notes.append({
                    "type": "User Research Note",
                    "id": note.get("id"),
                    "text": note.get("text"),
                    "created_at": note.get("created_at")
                })
            elif isinstance(note, str):
                user_notes.append({
                    "type": "User Research Note",
                    "text": note
                })

    # Prepare scientific payload for canonicalization & hashing
    scientific_payload = {
        "report_type": report_type,
        "query": query,
        "search_strategy": search_strategy,
        "analysis_scope": scope,
        "data_quality": report_data.get("data_quality", {}),
        "gene_associations": ranked_genes,
        "evidence": evidence,
        "comparison": report_data.get("comparison", {}),
        "knowledge_graph": report_data.get("knowledge_graph", {}),
        "provenance": report_data.get("provenance", {}),
        "user_notes": user_notes,
    }
    
    canonical_payload = canonicalize_snapshot_payload(scientific_payload)
    snapshot_hash = compute_snapshot_hash(canonical_payload)
    
    snapshot_id = f"SNAP-{snapshot_hash[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    snapshot = AnalysisSnapshot(
        snapshot_id=snapshot_id,
        snapshot_hash=snapshot_hash,
        created_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        report_id=report_id,
        report_type=report_type,
        source=meta.get("source") or "NCBI MedGen",
        query=query,
        search_strategy=search_strategy,
        parameters=scope,
        records=report_data.get("records", []),
        gene_associations=ranked_genes,
        evidence=evidence,
        analysis_results=scientific_payload,
        user_notes=user_notes,
        provenance=report_data.get("provenance", {})
    )
    
    store_snapshot(snapshot)
    return snapshot

def store_snapshot(snapshot: AnalysisSnapshot) -> None:
    """
    Store snapshot in cache and persist to results/snapshots/<snapshot_id>.json.
    """
    cache.set(f"{SNAPSHOT_CACHE_PREFIX}{snapshot.snapshot_id}", snapshot.model_dump(), ttl=86400)
    
    try:
        _ensure_snapshot_dir()
        safe_id = sanitize_filename(snapshot.snapshot_id)
        filepath = os.path.join(SNAPSHOT_DIR, f"{safe_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot.model_dump(), f, indent=2)
    except Exception as e:
        # Fallback to cache if filesystem write fails
        pass

def get_snapshot_by_id(snapshot_id: str) -> Optional[AnalysisSnapshot]:
    """
    Retrieve snapshot by ID from cache or results/snapshots/ directory.
    """
    if not snapshot_id:
        return None
        
    cache_data = cache.get(f"{SNAPSHOT_CACHE_PREFIX}{snapshot_id}")
    if cache_data:
        return AnalysisSnapshot(**cache_data)
        
    try:
        _ensure_snapshot_dir()
        safe_id = sanitize_filename(snapshot_id)
        filepath = os.path.join(SNAPSHOT_DIR, f"{safe_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                snapshot = AnalysisSnapshot(**data)
                cache.set(f"{SNAPSHOT_CACHE_PREFIX}{snapshot_id}", snapshot.model_dump(), ttl=86400)
                return snapshot
    except Exception:
        pass
        
    return None
