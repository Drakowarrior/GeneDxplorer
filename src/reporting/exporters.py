"""
GeneDxplorer — Phase 10 Report Exporters

Provides standalone HTML, JSON, and CSV exporters for ResearchReport models.
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional, Tuple

from src.utils import get_safe_export_path, sanitize_filename

logger = logging.getLogger("genedxplorer.reporting.exporters")


def generate_standalone_html(report: Dict[str, Any]) -> str:
    """Generate standalone HTML document string for a ResearchReport."""
    meta = report.get("metadata", {})
    scope = report.get("scope", {})
    quality = report.get("data_quality", {})
    genes = report.get("gene_analysis", [])
    evidence = report.get("evidence", [])
    comp = report.get("comparison")
    kg = report.get("knowledge_graph")
    summary = report.get("executive_summary", "")
    disclaimer = report.get("disclaimer", "")
    limitations = report.get("limitations", [])
    prov = report.get("provenance", {})

    # Build Genes Table Rows
    gene_rows_html = ""
    for g in genes[:25]:
        r_num = g.get("Rank", "-")
        sym = g.get("Gene") or g.get("symbol") or "-"
        ncbi_id = g.get("NCBI_Gene_ID") or g.get("ncbi_gene_id") or "N/A"
        cnt = g.get("Record Count") or g.get("Record_Count") or g.get("Matching_Diseases") or 0
        pct = g.get("Record_Percentage") or 0.0
        gene_rows_html += f"""
        <tr>
            <td>#{r_num}</td>
            <td><strong>{sym}</strong></td>
            <td><code>{ncbi_id}</code></td>
            <td>{cnt}</td>
            <td>{pct}%</td>
        </tr>
        """

    # Build Evidence Table Rows
    evidence_rows_html = ""
    for e in evidence[:25]:
        med_uid = e.get("medgen_uid") or e.get("record_id") or "N/A"
        title = e.get("disease_title") or e.get("title") or e.get("disease_name") or "-"
        rel = e.get("relationship") or "direct"
        ev_type = e.get("evidence_type") or "NCBI MedGen AssociatedGenes"
        evidence_rows_html += f"""
        <tr>
            <td><code>{med_uid}</code></td>
            <td>{title}</td>
            <td><span class="badge">{rel}</span></td>
            <td>{ev_type}</td>
        </tr>
        """

    # Limitations HTML List
    limitations_html = "".join([f"<li>{item}</li>" for item in limitations])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta.get('title', 'GeneDxplorer Research Report')}</title>
    <style>
        :root {{
            --bg-main: #f6f8fb;
            --card-bg: #ffffff;
            --surface-soft: #f0f4f9;
            --text-main: #252d3a;
            --text-muted: #5d6b80;
            --border-color: #dfe5ee;
            --primary: #526b85;
            --accent-purple: #40576f;
            --accent-cyan: #526b85;
            --accent-amber: #8a5b29;
        }}
        body {{
            font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            margin: 0;
            padding: 2rem 1rem;
            line-height: 1.6;
        }}
        h1, h2, h3, h4 {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: var(--text-main);
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-main);
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
            font-size: 0.85rem;
        }}
        .section {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .section h2 {{
            margin-top: 0;
            font-size: 1.25rem;
            color: var(--primary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.85rem;
        }}
        th, td {{
            padding: 0.6rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
            background: var(--surface-soft);
        }}
        code {{
            font-family: monospace;
            background: var(--surface-soft);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }}
        .badge {{
            background: var(--surface-soft);
            border: 1px solid var(--border-color);
            color: var(--primary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }}
        .disclaimer {{
            background: #fffdf5;
            border: 1px solid #fde68a;
            border-left: 4px solid #b45309;
            color: #78350f;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
        }}
        ul {{
            padding-left: 1.2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        .footer {{
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 3rem;
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge" style="background: var(--surface-soft); color: var(--primary);">
                DISEASE–GENE RESEARCH EXPLORER REPORT
            </span>
            <h1>{meta.get('title', 'Research Report')}</h1>
            <p style="color: var(--text-muted); margin: 0;">
                Report ID: <code>{meta.get('report_id', '')}</code> | Generated: {meta.get('generated_at', '')}
            </p>
        </div>

        <div class="meta-grid">
            <div><strong>Query:</strong> {meta.get('query', '')}</div>
            <div><strong>Source Database:</strong> {meta.get('source', 'NCBI MedGen')}</div>
            <div><strong>Records Analyzed:</strong> {scope.get('records_analyzed', 0)}</div>
            <div><strong>Software Version:</strong> {meta.get('software_version', '1.0.0')}</div>
        </div>

        <div class="section">
            <h2>1. Executive Summary</h2>
            <p style="font-size: 0.95rem; color: #f1f5f9; font-weight: 500;">
                {summary}
            </p>
        </div>

        <div class="section">
            <h2>2. Dataset Scope & Data Quality</h2>
            <table>
                <tr><th>Metric</th><th>Value</th><th>Details</th></tr>
                <tr><td>Total Search Matches Available</td><td>{scope.get('records_available', 0)}</td><td>NCBI MedGen query index count</td></tr>
                <tr><td>Records Retrieved & Analyzed</td><td>{scope.get('records_analyzed', 0)}</td><td>Examined DocumentSummary XML records</td></tr>
                <tr><td>Records with Direct Gene Annotations</td><td>{quality.get('records_with_genes', 0)}</td><td>Structured &lt;AssociatedGenes&gt; XML nodes</td></tr>
                <tr><td>Unique Reported Associated Genes</td><td>{quality.get('unique_genes', 0)}</td><td>Deduplicated gene symbols</td></tr>
            </table>
        </div>

        {"<div class='section'><h2>3. Top Reported Associated Genes</h2><table><thead><tr><th>Rank</th><th>Gene Symbol</th><th>NCBI Gene ID</th><th>Record Count</th><th>Record Percentage</th></tr></thead><tbody>" + gene_rows_html + "</tbody></table></div>" if gene_rows_html else ""}

        {"<div class='section'><h2>4. Supporting Evidence Record Provenance</h2><table><thead><tr><th>MedGen UID</th><th>Disease Title</th><th>Relationship</th><th>Evidence Type</th></tr></thead><tbody>" + evidence_rows_html + "</tbody></table></div>" if evidence_rows_html else ""}

        <div class="section">
            <h2>5. Scientific Limitations & Interpretation Safeguards</h2>
            <ul>
                {limitations_html}
            </ul>
        </div>

        <div class="disclaimer">
            <strong>🛡️ Scientific Interpretation Disclaimer:</strong><br>
            {disclaimer}
        </div>

        <div class="footer">
            Generated by <strong>GeneDxplorer</strong> v{meta.get('software_version', '1.0.0')} &bull; NCBI MedGen & ClinVar Data Layer &bull; Reproducible Scientific Pipeline
        </div>
    </div>
</body>
</html>
"""
    return html_content


def export_report_html(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Generate and save HTML report file safely."""
    html_str = generate_standalone_html(report)
    if not output_path:
        slug = sanitize_filename(report.get("metadata", {}).get("query", "report"))
        output_path = f"results/{slug}_research_report.html"

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    logger.info(f"Exported HTML Research Report to {safe_path}")
    return safe_path


def export_report_json(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Export machine-readable JSON research report."""
    if not output_path:
        slug = sanitize_filename(report.get("metadata", {}).get("query", "report"))
        output_path = f"results/{slug}_research_report.json"

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported JSON Research Report to {safe_path}")
    return safe_path


def export_report_genes_csv(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Export ranked genes table to CSV."""
    if not output_path:
        slug = sanitize_filename(report.get("metadata", {}).get("query", "report"))
        output_path = f"results/{slug}_report_genes.csv"

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    genes = report.get("gene_analysis", [])
    df = pd.DataFrame(genes)
    if not df.empty:
        df.to_csv(safe_path, index=False)
    else:
        pd.DataFrame(columns=["Rank", "Gene", "NCBI_Gene_ID", "Record Count", "Record_Percentage"]).to_csv(safe_path, index=False)

    logger.info(f"Exported Report Genes CSV to {safe_path}")
    return safe_path


def export_report_evidence_csv(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Export supporting evidence list to CSV."""
    if not output_path:
        slug = sanitize_filename(report.get("metadata", {}).get("query", "report"))
        output_path = f"results/{slug}_report_evidence.csv"

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    evidence = report.get("evidence", [])
    df = pd.DataFrame(evidence)
    if not df.empty:
        df.to_csv(safe_path, index=False)
    else:
        pd.DataFrame(columns=["medgen_uid", "disease_title", "gene_symbol", "relationship", "evidence_type", "source"]).to_csv(safe_path, index=False)

    logger.info(f"Exported Report Evidence CSV to {safe_path}")
    return safe_path
