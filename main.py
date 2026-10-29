import os
import sys

# Import modules from src package
try:
    from src.medgen import (
        configure_ncbi,
        search_medgen,
        search_medgen_by_gene,
        fetch_medgen_records_xml,
    )
    from src.parser import parse_medgen_xml
    from src.analysis import (
        sanitize_filename,
        analyze_disease_genes,
        analyze_gene_to_disease,
        compare_diseases,
        export_disease_gene_csv,
        export_disease_gene_json,
        generate_bar_chart,
        export_gene_disease_csv,
        export_gene_disease_json,
        export_comparison_json,
        export_comparison_csv,
        generate_comparison_chart,
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.medgen import (
        configure_ncbi,
        search_medgen,
        search_medgen_by_gene,
        fetch_medgen_records_xml,
    )
    from src.parser import parse_medgen_xml
    from src.analysis import (
        sanitize_filename,
        analyze_disease_genes,
        analyze_gene_to_disease,
        compare_diseases,
        export_disease_gene_csv,
        export_disease_gene_json,
        generate_bar_chart,
        export_gene_disease_csv,
        export_gene_disease_json,
        export_comparison_json,
        export_comparison_csv,
        generate_comparison_chart,
    )

DEFAULT_ANALYSIS_LIMIT = int(os.environ.get("ANALYSIS_LIMIT", "500"))
BATCH_SIZE = 100


def run_disease_gene_mode():
    """Mode 1: Disease -> Gene Analysis"""
    print("\n==================================================")
    print("           DISEASE → GENE ANALYSIS")
    print("==================================================")

    try:
        disease_name = input("Enter disease name: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Operation cancelled.")
        return

    if not disease_name:
        print("\n[ERROR] Disease name cannot be empty.")
        return

    print("\nSearching NCBI MedGen...")
    total_search_results, title_count, combined_uids, search_strategy_desc = search_medgen(
        disease_name, max_limit=DEFAULT_ANALYSIS_LIMIT
    )

    if not combined_uids:
        print("\n[ERROR] No matching MedGen records were found.\n")
        print("Please try another disease name.")
        return

    print("✓ Search completed\n")
    print(f"Total matching MedGen records: {total_search_results}")

    print("\nRetrieving relevant records...")
    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=BATCH_SIZE)
    print(f"✓ {len(doc_elements)} records retrieved\n")

    print("Analyzing direct associated genes...")
    records, parser_metrics = parse_medgen_xml(doc_elements)
    df_counts, analysis_payload = analyze_disease_genes(records, disease_name, total_search_results)
    print("✓ Analysis completed\n")

    records_analyzed = parser_metrics["records_analyzed"]
    records_with_genes = parser_metrics["records_with_genes"]
    records_without_genes = parser_metrics["records_without_genes"]
    total_relationships = parser_metrics["total_relationships"]
    dup_removed = parser_metrics["duplicate_genes_removed"]
    unique_genes_count = analysis_payload["unique_genes"]

    print("==================================================")
    print("DATA QUALITY")
    print("==================================================")
    print(f"Search results available:       {total_search_results}")
    print(f"Records retrieved:               {len(doc_elements)}")
    print(f"Records analyzed:                {records_analyzed}")
    print(f"Records with direct genes:       {records_with_genes}")
    print(f"Records without direct genes:    {records_without_genes}")
    print(f"Gene-disease relationships:     {total_relationships}")
    print(f"Unique genes:                    {unique_genes_count}")
    print(f"Duplicate gene occurrences removed: {dup_removed}")

    if df_counts.empty:
        print("\n[WARNING] No directly associated genes were found")
        print("in the retrieved MedGen records.")
        return

    df_top10 = df_counts.head(10).copy()

    print("\n==================================================")
    print("TOP ASSOCIATED GENES")
    print("==================================================")
    print(f"\n{'Rank':<6}{'Gene':<12}{'NCBI Gene ID':<16}{'Records':<10}{'Percentage':<12}")
    print("-" * 56)

    for _, row in df_top10.iterrows():
        rank = int(row["Rank"])
        gene = str(row["Gene"])
        gene_id = str(row["NCBI_Gene_ID"]) if str(row["NCBI_Gene_ID"]) else "N/A"
        count = int(row["Record Count"])
        pct = f"{row['Record_Percentage']:.2f}%"
        print(f"{rank:<6}{gene:<12}{gene_id:<16}{count:<10}{pct:<12}")

    print("==================================================")

    disease_slug = sanitize_filename(disease_name)
    csv_path = f"results/{disease_slug}_gene_analysis.csv"
    json_path = f"results/{disease_slug}_disease_metadata.json"
    chart_path = f"results/{disease_slug}_top_genes.png"

    export_disease_gene_csv(df_top10, csv_path)
    export_disease_gene_json(
        query=disease_name,
        search_strategy=search_strategy_desc,
        total_search_results=total_search_results,
        records_retrieved=len(doc_elements),
        records_analyzed=records_analyzed,
        records_with_genes=records_with_genes,
        unique_genes=unique_genes_count,
        records=records,
        output_path=json_path
    )
    generate_bar_chart(df_top10, disease_name, chart_path)

    print("\n✓ Gene analysis CSV generated")
    print("✓ Disease metadata JSON generated")
    print("✓ Visualization generated\n")

    print("Outputs:\n")
    print(f"{csv_path}")
    print(f"{json_path}")
    print(f"{chart_path}\n")

    print("==================================================")
    print("Scientific Note:")
    print("These counts represent reporting frequency across")
    print("retrieved NCBI MedGen records and do not establish")
    print("causality, disease severity, clinical risk, or")
    print("medical importance.")
    print("==================================================\n")


def run_gene_disease_mode():
    """Mode 2: Gene -> Disease Analysis"""
    print("\n==================================================")
    print("           GENE → DISEASE ANALYSIS")
    print("==================================================")

    try:
        gene_symbol = input("Enter gene symbol: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Operation cancelled.")
        return

    if not gene_symbol:
        print("\n[ERROR] Gene symbol cannot be empty.")
        return

    target_gene = gene_symbol.upper()
    print(f"\nSearching NCBI MedGen for records associated with gene: {target_gene}...")

    total_search_results, combined_uids, search_strategy_desc = search_medgen_by_gene(
        target_gene, max_limit=DEFAULT_ANALYSIS_LIMIT
    )

    if not combined_uids:
        print(f"\n[ERROR] No matching MedGen records were found for gene symbol '{target_gene}'.\n")
        return

    print("✓ Search completed\n")
    print(f"Total MedGen candidate records: {total_search_results}")

    print("\nRetrieving and parsing structured MedGen records...")
    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=BATCH_SIZE)
    records, _ = parse_medgen_xml(doc_elements)

    print("Verifying direct AssociatedGenes relationship...")
    df_diseases, analysis_payload = analyze_gene_to_disease(target_gene, records, total_search_results)
    print("✓ Verification completed\n")

    matching_count = analysis_payload["matching_disease_count"]
    ncbi_gene_id = analysis_payload["ncbi_gene_id"]

    print("==================================================")
    print("GENE → DISEASE ANALYSIS RESULTS")
    print("==================================================")
    print(f"Gene Symbol:                  {target_gene}")
    print(f"NCBI Gene ID:                 {ncbi_gene_id}")
    print(f"MedGen records examined:      {len(records)}")
    print(f"Matching disease records:     {matching_count}")
    print("==================================================")

    if df_diseases.empty:
        print(f"\n[WARNING] No MedGen disease records contained direct '{target_gene}' associations.")
        return

    print(f"\n{'Rank':<6}{'Disease Title':<45}{'MedGen ID':<12}{'Concept ID':<12}")
    print("-" * 75)

    for _, row in df_diseases.iterrows():
        rank = int(row["Rank"])
        title = str(row["title"])[:43]
        uid = str(row["medgen_uid"])
        cid = str(row["concept_id"]) if str(row["concept_id"]) else "N/A"
        print(f"{rank:<6}{title:<45}{uid:<12}{cid:<12}")

    print("==================================================")

    gene_slug = sanitize_filename(target_gene)
    csv_path = f"results/{gene_slug}_associated_diseases.csv"
    json_path = f"results/{gene_slug}_gene_metadata.json"

    export_gene_disease_csv(df_diseases, target_gene, csv_path)
    export_gene_disease_json(analysis_payload, json_path)

    print("\n✓ Associated diseases CSV generated")
    print("✓ Gene metadata JSON generated\n")
    print(f"CSV:\n{csv_path}\n")
    print(f"JSON:\n{json_path}\n")


def run_disease_comparison_mode():
    """Mode 3: Compare Two Diseases"""
    print("\n==================================================")
    print("             DISEASE COMPARISON")
    print("==================================================")

    try:
        disease_a = input("Enter first disease name (Disease A): ").strip()
        disease_b = input("Enter second disease name (Disease B): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Operation cancelled.")
        return

    if not disease_a or not disease_b:
        print("\n[ERROR] Both disease names must be provided.")
        return

    print(f"\nFetching and analyzing records for Disease A: '{disease_a}'...")
    total_results_a, _, uids_a, _ = search_medgen(disease_a, max_limit=DEFAULT_ANALYSIS_LIMIT)
    docs_a = fetch_medgen_records_xml(uids_a, batch_size=BATCH_SIZE)
    records_a, _ = parse_medgen_xml(docs_a)

    print(f"Fetching and analyzing records for Disease B: '{disease_b}'...")
    total_results_b, _, uids_b, _ = search_medgen(disease_b, max_limit=DEFAULT_ANALYSIS_LIMIT)
    docs_b = fetch_medgen_records_xml(uids_b, batch_size=BATCH_SIZE)
    records_b, _ = parse_medgen_xml(docs_b)

    print("Comparing gene sets and calculating Jaccard similarity...")
    comparison_payload = compare_diseases(
        disease_a, records_a, total_results_a,
        disease_b, records_b, total_results_b
    )
    print("✓ Comparison completed\n")

    print("==================================================")
    print("DISEASE COMPARISON SUMMARY")
    print("==================================================")
    print(f"Disease A:                    {disease_a}")
    print(f"Disease B:                    {disease_b}")
    print("-" * 50)
    print(f"Disease A records analyzed:   {comparison_payload['records_analyzed_a']}")
    print(f"Disease B records analyzed:   {comparison_payload['records_analyzed_b']}")
    print(f"Disease A unique genes:       {comparison_payload['unique_to_a_count']}")
    print(f"Disease B unique genes:       {comparison_payload['unique_to_b_count']}")
    print(f"Shared genes:                 {comparison_payload['shared_genes_count']}")
    print(f"Combined unique genes:        {comparison_payload['combined_unique_genes_count']}")
    print(f"\nGene-set similarity:          {comparison_payload['jaccard_percentage']}%")
    print("==================================================")

    shared_genes = comparison_payload["shared_genes"]
    if shared_genes:
        print("\n==================================================")
        print("SHARED GENES")
        print("==================================================")
        print(f"{'Gene':<10}{'Gene ID':<12}{disease_a[:14] + ' Count':<16}{disease_b[:14] + ' Count':<16}")
        print("-" * 54)
        for sg in shared_genes:
            g = sg["Gene"]
            gid = sg["NCBI_Gene_ID"] if sg["NCBI_Gene_ID"] else "N/A"
            ca = sg["Count_A"]
            cb = sg["Count_B"]
            print(f"{g:<10}{gid:<12}{ca:<16}{cb:<16}")
        print("==================================================")

    # Export comparison outputs
    slug_a = sanitize_filename(disease_a)
    slug_b = sanitize_filename(disease_b)
    comp_prefix = f"{slug_a}_vs_{slug_b}"

    json_path = f"results/{comp_prefix}_comparison.json"
    csv_path = f"results/{comp_prefix}_shared_genes.csv"
    chart_path = f"results/{comp_prefix}_comparison.png"

    export_comparison_json(comparison_payload, json_path)
    if shared_genes:
        export_comparison_csv(comparison_payload, csv_path)
    generate_comparison_chart(comparison_payload, chart_path)

    print("\n✓ Comparison JSON generated")
    if shared_genes:
        print("✓ Shared genes CSV generated")
    print("✓ Comparison chart generated\n")

    print("Outputs:\n")
    print(f"{json_path}")
    if shared_genes:
        print(f"{csv_path}")
    print(f"{chart_path}\n")

    print("==================================================")
    print("Interpretation:")
    print("The similarity value represents overlap between")
    print("the analyzed gene sets. It does not represent")
    print("clinical similarity or biological causality.")
    print("==================================================\n")


def main():
    print("==================================================")
    print("                 GENEDXPLORER")
    print("       Disease–Gene Relationship Explorer")
    print("==================================================")
    print("\nSource: NCBI MedGen")
    print("Access: Biopython Bio.Entrez")

    configure_ncbi()

    while True:
        print("\n==================================================")
        print("MAIN MENU")
        print("==================================================")
        print("1. Disease → Gene Analysis")
        print("2. Gene → Disease Analysis")
        print("3. Compare Two Diseases")
        print("4. Exit")
        print("==================================================")

        try:
            choice = input("Select option (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n[INFO] Exiting GeneDxplorer.")
            sys.exit(0)

        if choice == "1":
            run_disease_gene_mode()
        elif choice == "2":
            run_gene_disease_mode()
        elif choice == "3":
            run_disease_comparison_mode()
        elif choice in ["4", "exit", "quit", "q"]:
            print("\nExiting GeneDxplorer. Goodbye!")
            sys.exit(0)
        else:
            print("\n[ERROR] Invalid choice. Please select 1, 2, 3, or 4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Exiting GeneDxplorer.")
        sys.exit(0)
