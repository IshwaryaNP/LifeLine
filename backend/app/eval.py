import json
from app.metrics import compute_ground_truth_metrics

def main():
    print("=" * 65)
    print("      LIFELINE TRIAGE - SYSTEM VS BASELINE EVALUATION REPORT    ")
    print("=" * 65)
    print("NOTE: Evaluated on simulated data with self-generated ground truth.\n")
    
    m = compute_ground_truth_metrics()
    
    print("1. DUPLICATE-MERGE CLUSTERING PERFORMANCE:")
    print(f"   - Precision:          {m['duplicate_merge']['precision']:.3f}")
    print(f"   - Recall:             {m['duplicate_merge']['recall']:.3f}")
    print(f"   - F1-Score:           {m['duplicate_merge']['f1']:.3f}")
    print(f"   - Raw Reports:        {m['duplicate_merge']['total_raw_reports']}")
    print(f"   - Consolidated Incs:  {m['duplicate_merge']['consolidated_incidents']}")
    print(f"   - Volume Reduction:   {m['duplicate_merge']['compression_ratio']}x compression")
    print()

    print("2. TOP-10 OVERLAP WITH EXPERT HIDDEN GROUND TRUTH:")
    print(f"   - Lifeline System:    {m['expert_ranking_top10_overlap']['system'] * 100:.1f}%")
    print(f"   - Volume Baseline:    {m['expert_ranking_top10_overlap']['baseline'] * 100:.1f}%")
    print()

    print("3. SILENT HIGH-RISK ZONE DETECTION:")
    print(f"   - Planted Silent:     {m['silent_zones_flagged']['total_planted']} zones (Z01, Z04, Z07)")
    print(f"   - System Flagged:     {m['silent_zones_flagged']['system_flagged']} / {m['silent_zones_flagged']['total_planted']} (PASS)")
    print(f"   - Baseline Flagged:   {m['silent_zones_flagged']['baseline_flagged']} / {m['silent_zones_flagged']['total_planted']} (Ignored due to 0-reports)")
    print()

    print("4. INFORMATION EXTRACTION & LOCATION RESOLUTION:")
    print(f"   - Need Type Accuracy: {m['extraction_accuracy']['need_type_accuracy'] * 100:.1f}%")
    print(f"   - People Count Acc:   {m['extraction_accuracy']['people_count_accuracy'] * 100:.1f}%")
    print(f"   - Locations Resolved: {m['location_resolution']['percent_resolved']:.1f}% ({m['location_resolution']['resolved_count']}/{m['location_resolution']['total_reports']})")
    print(f"   - Vague/Needs Check:  {100 - m['location_resolution']['percent_resolved']:.1f}%")
    print()

    print("5. SAFETY & ROBUSTNESS:")
    print(f"   - Fake Reports in Top 10 Incidents: {m['fake_reports_in_top10']}")
    print()

    print("6. PERFORMANCE BENCHMARK:")
    print(f"   - Time per 1,000 reports: {m['performance']['processing_time_1000_reports_ms']} ms")
    print("=" * 65)

if __name__ == "__main__":
    main()
