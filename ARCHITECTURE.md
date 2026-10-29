# ARCHITECTURE.md — System Architecture

## Overview & System Stack

**Disease–Gene Research Explorer** is a production-grade bioinformatics platform for exploring disease–gene relationships, evidence records, and set-theoretic similarities using public data from **NCBI MedGen** and **NCBI ClinVar**.

---

## 1. System Architecture Diagram

```text
                    PUBLIC NCBI DATA
                  ┌─────────┴─────────┐
                  ↓                   ↓
               MedGen              ClinVar
                  └─────────┬─────────┘
                            ↓
                     Evidence Layer
                            ↓
                     Analysis Engine
                  ┌──────┬─┴─┬──────┐
                  ↓      ↓   ↓      ↓
                Genes  Compare Graph Similarity
                  └──────┬─┬─┬──────┘
                         ↓
                  Research Workspace
                         ↓
                   Research Reports
                         ↓
                 Reproducibility Layer
                    ┌────┼────┐
                    ↓    ↓    ↓
                 Manifest Citation Snapshot
                         ↓
                 Research Package (.ZIP)
```

---

## 2. Layer Responsibilities

### 2.1 Public NCBI Data Layer
- Connects directly to official **NCBI MedGen** and **NCBI ClinVar** E-utilities endpoints via Biopython (`Bio.Entrez`).
- Enforces request pacing delay (`NCBI_REQUEST_DELAY = 0.2s`) and retry logic with exponential backoff to ensure compliance with NCBI rate limits.

### 2.2 Evidence Layer (`src/evidence/`)
- Aggregates record-level evidence from MedGen XML summaries and ClinVar variant reports.
- Normalizes evidence items with UIDs, titles, concept IDs, associated gene symbols, chromosome locations, and official source URLs.

### 2.3 Analysis Engine (`src/analysis.py`, `src/graph.py`, `src/similarity.py`)
- **Disease & Gene Analysis**: Parses `<AssociatedGenes>` elements in MedGen XML to calculate record frequencies and percentage metrics.
- **Disease Comparison**: Calculates Jaccard set similarity ($|A \cap B| / |A \cup B| \times 100$) and overlap coefficients for disease gene sets.
- **Knowledge Graph Engine**: Constructs bounded D3-compatible node-link networks connecting diseases, genes, and MedGen records with deduplication safeguards.
- **Multi-Disease Similarity Engine**: Generates pairwise similarity matrices across 2 to 10 diseases.

### 2.4 Research Workspace (`src/context/WorkspaceContext.jsx`)
- Manages local client-side state for saved diseases, genes, evidence records, comparisons, and user research notes.
- Exports workspace snapshots to JSON and CSV formats.

### 2.5 Research Reports Layer (`src/reporting/`)
- Compiles structured research reports containing executive summaries, scope details, gene tables, evidence listings, limitations, and audit trails.
- 100% deterministic report generation without AI/LLM generative inference.

### 2.6 Reproducibility Layer (`src/reproducibility/`)
- **Snapshot Engine (`snapshot.py`)**: Computes canonical, deterministic SHA-256 hex hashes for frozen analysis payloads.
- **Manifest Builder (`manifest.py`)**: Builds environment audit trails including retrieval parameters, schema versions, software version, and timestamps.
- **Citation Provider (`citation.py`)**: Generates official NCBI URLs (`https://www.ncbi.nlm.nih.gov/medgen/{uid}`, `https://www.ncbi.nlm.nih.gov/clinvar/variation/{id}`).
- **Package Exporter (`package.py`)**: Compiles self-contained ZIP packages (`manifest.json`, `snapshot.json`, `report.json`, `publication_evidence.csv`, `genes.csv`, `evidence.csv`, `citations.csv`, `README.txt`).

---

## 3. Security & Data Hygiene

- **Path Traversal Protection**: Input paths and filenames are sanitized before file generation, preventing directory traversal attempts (`../../`).
- **HTML Sanitization**: Report and UI renderers escape user inputs and dataset fields to prevent script injection.
- **Secret Redaction**: Environment secrets (NCBI API keys, passwords) are filtered out of exported manifests and snapshots.
- **CORS Safeguards**: API endpoints enforce strict CORS origins (`ALLOWED_ORIGINS`).

---

## 4. Performance & Caching Strategy

- **In-Memory TTL Cache (`src/cache.py`)**: Thread-safe cache storing processed MedGen records for 3600 seconds (`CACHE_TTL`), avoiding redundant NCBI network requests.
- **Deterministic Keys**: Cache keys are generated based on normalized query parameters (e.g., `disease_workflow:limit=500&query=alzheimers_disease`).
