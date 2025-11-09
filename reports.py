
from typing import List, Dict, Tuple, Optional
import csv
import os
import statistics

# Default configuration (same names used previously)
FILENAME = "studentRecord.csv"
OUT_DIR = "reports"
PASSING_GRADE = 75.0

# Weights (kept same as your previous reports/at_risk code)
WEIGHTS = {
    "quiz": 0.3,
    "midterm": 0.3,
    "final": 0.3,
    "attendance": 0.1
}

HEADER = [
    "student_id","last_name","first_name","section",
    "quiz1","quiz2","quiz3","quiz4","quiz5",
    "midterm","final","attendance_percent"
]


# Helpers

def _to_float_safe(val: Optional[str]) -> Optional[float]:
    """Convert string-like to float, return None on empty or invalid."""
    if val is None:
        return None
    if isinstance(val, float) or isinstance(val, int):
        return float(val)
    s = str(val).strip()
    if s == "" or s.lower() == "none":
        return None
    try:
        return float(s)
    except Exception:
        return None

def _compute_final_from_row_map(row: Dict[str, str]) -> Optional[float]:
    """
    Compute weighted final grade from a dict-like CSV row.
    Missing components are treated as 0 for the calculation (consistent with prior code).
    Returns final as float rounded to 2 decimals, or None if no numeric data present.
    """
    # Collect quizzes
    quizzes = []
    for i in range(1, 6):
        q = _to_float_safe(row.get(f"quiz{i}", None))
        if q is not None:
            quizzes.append(q)
    quiz_avg = (sum(quizzes) / len(quizzes)) if quizzes else 0.0

    mid = _to_float_safe(row.get("midterm", None))
    final = _to_float_safe(row.get("final", None))
    att = _to_float_safe(row.get("attendance_percent", None))

    # If all components missing and length 0 quizzes, return None
    if quiz_avg == 0.0 and mid is None and final is None and att is None:
        # no numeric info at all
        return None

    mid_val = mid if mid is not None else 0.0
    final_val = final if final is not None else 0.0
    att_val = att if att is not None else 0.0

    weighted = (
        quiz_avg * WEIGHTS["quiz"]
        + mid_val * WEIGHTS["midterm"]
        + final_val * WEIGHTS["final"]
        + att_val * WEIGHTS["attendance"]
    )

    return round(float(weighted), 2)

def _letter_grade(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    s = float(score)
    if s >= 90:
        return "A"
    if s >= 80:
        return "B"
    if s >= 70:
        return "C"
    if s >= 60:
        return "D"
    return "F"

# -------------------------
# File-reading helper
# -------------------------
def _read_csv_as_dicts(filename: str) -> List[Dict[str, str]]:
    """Read CSV into list of dict rows. If file missing, returns []"""
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]

# -------------------------
# Core functions (public)
# -------------------------
def summary_report(filename: str = FILENAME, export_sections: bool = True, out_folder: str = OUT_DIR) -> None:
    """
    Read 'filename', compute final grades, print a formatted summary to terminal.
    Optionally export per-section CSVs into 'out_folder' if export_sections is True.
    """
    rows = _read_csv_as_dicts(filename)
    if not rows:
        print("File not found or no data:", filename)
        return

    enriched = []
    grades = []
    for r in rows:
        final = _compute_final_from_row_map(r)
        enriched_row = dict(r)  # copy
        enriched_row["final_grade"] = f"{final:.2f}" if final is not None else ""
        enriched_row["final_numeric"] = final
        enriched_row["letter"] = _letter_grade(final)
        enriched.append(enriched_row)
        if final is not None:
            grades.append(final)

    # Print header table
    print("\n=== SUMMARY REPORT ===")
    print("{:<12} {:<15} {:<15} {:<10} {:>10} {:>8}".format(
        "student_id", "last_name", "first_name", "section", "final_grade", "letter"
    ))
    print("-" * 76)
    for r in enriched:
        print("{:<12} {:<15} {:<15} {:<10} {:>10} {:>8}".format(
            r.get("student_id", ""),
            r.get("last_name", ""),
            r.get("first_name", ""),
            r.get("section", ""),
            r.get("final_grade", "") if r.get("final_grade") is not None else "",
            r.get("letter", "")
        ))

    # Summary stats
    if grades:
        try:
            mean_v = statistics.mean(grades)
            med_v = statistics.median(grades)
        except statistics.StatisticsError:
            mean_v = med_v = 0.0
        print("\n--- SUMMARY STATISTICS ---")
        print(f"Total Students (with valid grade): {len(grades)}")
        print(f"Average Grade: {mean_v:.2f}")
        print(f"Median Grade: {med_v:.2f}")
        print(f"Highest Grade: {max(grades):.2f}")
        print(f"Lowest Grade: {min(grades):.2f}")
    else:
        print("\nNo valid numeric grade data available for statistics.")

    # Export per-section CSVs if requested
    if export_sections:
        export_per_section(enriched, out_folder=out_folder)

    # Optionally save an overall summary CSV for instructor convenience
    os.makedirs(out_folder, exist_ok=True)
    summary_csv = os.path.join(out_folder, "summary.csv")
    try:
        with open(summary_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["student_id","last_name","first_name","section","final_grade","letter"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in enriched:
                writer.writerow({
                    "student_id": r.get("student_id",""),
                    "last_name": r.get("last_name",""),
                    "first_name": r.get("first_name",""),
                    "section": r.get("section",""),
                    "final_grade": r.get("final_grade",""),
                    "letter": r.get("letter","")
                })
        print(f"\nSaved overall summary to: {summary_csv}")
    except Exception as e:
        print("Could not save summary CSV:", e)


def export_per_section(rows_or_filename, out_folder: str = OUT_DIR) -> None:
    """
    Export one CSV per section.
    rows_or_filename can be:
      - a list of enriched dict rows (with 'section' and 'final_grade'), or
      - a filename string to read the CSV from.
    Output files are created under out_folder with names like 'section_A.csv' (spaces sanitized).
    """
    # Accept either precomputed rows or filename
    if isinstance(rows_or_filename, str):
        rows = _read_csv_as_dicts(rows_or_filename)
        enriched = []
        for r in rows:
            final = _compute_final_from_row_map(r)
            enriched.append({
                **r,
                "final_grade": f"{final:.2f}" if final is not None else "",
                "final_numeric": final,
                "letter": _letter_grade(final)
            })
    else:
        enriched = list(rows_or_filename)  # assume list of dicts

    if not enriched:
        print("No data available to export per-section.")
        return

    os.makedirs(out_folder, exist_ok=True)
    # Group by section
    sections: Dict[str, List[Dict]] = {}
    for r in enriched:
        sec = r.get("section") or "UNSPECIFIED"
        sec_clean = str(sec).strip().replace(" ", "_")
        sections.setdefault(sec_clean, []).append(r)

    # For each section write CSV
    for sec_name, items in sections.items():
        out_path = os.path.join(out_folder, f"section_{sec_name}.csv")
        fieldnames = list(items[0].keys())
        # Ensure canonical ordering: id, last, first, section, original scores..., final_grade, letter
        # We'll attempt to put final_grade and letter near the end
        if "final_grade" in fieldnames:
            # move to end
            fieldnames = [fn for fn in fieldnames if fn not in ("final_grade","letter")]
            fieldnames += ["final_grade","letter"]
        try:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in items:
                    # ensure all fields exist
                    out_row = {k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames}
                    writer.writerow(out_row)
            print(f"Exported section {sec_name} → {out_path} ({len(items)} students)")
        except Exception as e:
            print(f"Failed to write {out_path}: {e}")


def export_at_risk(filename: str = FILENAME, output_file: str = os.path.join(OUT_DIR, "at_risk_students.csv"), threshold: float = PASSING_GRADE) -> None:
    """
    Identify students whose final grade < threshold and export to a CSV.
    Also prints the list to terminal (formatted).
    """
    rows = _read_csv_as_dicts(filename)
    if not rows:
        print("File not found or no data:", filename)
        return

    at_risk: List[Dict[str, str]] = []
    for r in rows:
        final = _compute_final_from_row_map(r)
        if final is None:
            continue
        if final < threshold:
            at_risk.append({
                "student_id": r.get("student_id",""),
                "last_name": r.get("last_name",""),
                "first_name": r.get("first_name",""),
                "section": r.get("section",""),
                "final_grade": f"{final:.2f}"
            })

    if not at_risk:
        print(" No students are currently at risk.")
        return

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # Write CSV
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["student_id","last_name","first_name","section","final_grade"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(at_risk)
        print(f"\nSaved at-risk list to: {output_file}")
    except Exception as e:
        print("Failed to write at-risk CSV:", e)
        return

    # Print formatted table
    print("\n=== AT-RISK STUDENTS ===")
    print("{:<12} {:<15} {:<15} {:<10} {:>10}".format("student_id","last_name","first_name","section","final_grade"))
    print("-" * 70)
    for s in at_risk:
        print("{:<12} {:<15} {:<15} {:<10} {:>10}".format(
            s["student_id"], s["last_name"], s["first_name"], s["section"], s["final_grade"]
        ))
    print(f"\n{len(at_risk)} student(s) found below {threshold}.")

# If run standalone, do a demo summary
if __name__ == "__main__":
    summary_report()


# at_risk.py
# backward-compat shim so main.py's import at_risk still works.


def display_section_simple(section_name: str, folder: str = OUT_DIR):
    """
    Display the selected section CSV in a clean column-aligned table (no tabulate).
    """
    sec_clean = section_name.strip().replace(" ", "_")
    file_path = os.path.join(folder, f"section_{sec_clean}.csv")

    if not os.path.exists(file_path):
        print(f"No CSV found for section '{section_name}'. Run summary_report() first to generate per-section files.")
        return

    with open(file_path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        print("Section CSV exists but is empty.")
        return

    header = rows[0]
    data = rows[1:]

    # Compute column widths
    col_widths = [len(h) for h in header]
    for row in data:
        for i, col in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(col)))

    # Format row helper
    def fmt(row):
        return " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(row))

    print(f"\n=== SECTION: {section_name.upper()} ===")
    print(fmt(header))
    print("-" * (sum(col_widths) + (3 * (len(col_widths) - 1))))
    for row in data:
        print(fmt(row))
    print() 



# allow direct call: python -m at_risk
if __name__ == "__main__":
    export_at_risk()
