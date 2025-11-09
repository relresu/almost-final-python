# tests/test_reports.py
import sys
import os
# Add parent folder to sys.path so 'import reports' works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
from pathlib import Path

import reports
from reports import _to_float_safe, _compute_final_from_row_map, _letter_grade, export_per_section, export_at_risk

# ---------------------------
# Helper test data
# ---------------------------
SIMPLE_HEADER = [
    "student_id","last_name","first_name","section",
    "quiz1","quiz2","quiz3","quiz4","quiz5",
    "midterm","final","attendance_percent"
]

# ---------------------------
# Tests
# ---------------------------
def test_to_float_safe_behavior():
    # None input
    assert _to_float_safe(None) is None
    # blank string and "None" string
    assert _to_float_safe("") is None
    assert _to_float_safe("None") is None
    # numeric strings and numeric inputs
    assert _to_float_safe("50") == 50.0
    assert _to_float_safe(25) == 25.0
    assert _to_float_safe(25.5) == 25.5
    # invalid string -> None
    assert _to_float_safe("abc") is None


def test_compute_final_from_row_map_basic():
    # Prepare a dict row with known values
    row = {
        "student_id": "S1",
        "last_name": "Test",
        "first_name": "Student",
        "section": "A",
        "quiz1": "80",
        "quiz2": "90",
        "quiz3": "70",
        "quiz4": "60",
        "quiz5": "100",
        "midterm": "85",
        "final": "75",
        "attendance_percent": "90"
    }
    # compute expected manually using WEIGHTS from reports.py
    quizzes = [80.0, 90.0, 70.0, 60.0, 100.0]
    quiz_avg = sum(quizzes) / len(quizzes)
    expected = round(
        quiz_avg * reports.WEIGHTS["quiz"]
        + 85.0 * reports.WEIGHTS["midterm"]
        + 75.0 * reports.WEIGHTS["final"]
        + 90.0 * reports.WEIGHTS["attendance"],
        2
    )
    got = _compute_final_from_row_map(row)
    assert got == expected


def test_letter_grade_boundaries():
    assert _letter_grade(None) == "N/A"
    assert _letter_grade(95.0) == "A"
    assert _letter_grade(90.0) == "A"
    assert _letter_grade(89.9) == "B"
    assert _letter_grade(80.0) == "B"
    assert _letter_grade(79.9) == "C"
    assert _letter_grade(70.0) == "C"
    assert _letter_grade(69.9) == "D"
    assert _letter_grade(60.0) == "D"
    assert _letter_grade(59.9) == "F"


def test_export_per_section_creates_files(tmp_path, capsys):
    # Create a simple enriched rows list (as export_per_section accepts)
    rows = [
        {"student_id": "s1", "last_name": "A", "first_name": "One", "section": "A", "final_grade": "80.00", "letter": "B"},
        {"student_id": "s2", "last_name": "B", "first_name": "Two", "section": "A", "final_grade": "90.00", "letter": "A"},
        {"student_id": "s3", "last_name": "C", "first_name": "Three", "section": "B", "final_grade": "70.00", "letter": "C"},
    ]
    out_folder = tmp_path / "out"
    export_per_section(rows, out_folder=str(out_folder))

    # Check that files exist for sections A and B
    file_a = out_folder / "section_A.csv"
    file_b = out_folder / "section_B.csv"
    assert file_a.exists()
    assert file_b.exists()

    # Validate content of section_A contains two students
    with open(file_a, "r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 2
    ids = {r["student_id"] for r in reader}
    assert ids == {"s1", "s2"}

    # Validate content of section_B contains one student
    with open(file_b, "r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 1
    assert reader[0]["student_id"] == "s3"


def test_export_at_risk_writes_file_and_prints(tmp_path, capsys):
    # Build a CSV with two students: one below threshold and one above
    csv_file = tmp_path / "students.csv"
    out_file = tmp_path / "at_risk_out.csv"

    # Choose numeric values that will produce final < 75 for s_low and >=75 for s_high
    # Using reports.WEIGHTS: quiz 0.3, midterm 0.3, final 0.3, attendance 0.1
    # s_low: quiz_avg=50, mid=60, final=60, att=70 -> weighted = 50*0.3+60*0.3+60*0.3+70*0.1 = 15+18+18+7 = 58 -> at risk
    # s_high: quiz_avg=90, mid=90, final=90, att=90 -> weighted = 90 -> safe
    rows = [
        {
            "student_id": "s_low", "last_name": "Low", "first_name": "Below",
            "section": "A", "quiz1": "50", "quiz2": "50", "quiz3": "50", "quiz4": "50", "quiz5": "50",
            "midterm": "60", "final": "60", "attendance_percent": "70"
        },
        {
            "student_id": "s_high", "last_name": "High", "first_name": "Above",
            "section": "A", "quiz1": "90", "quiz2": "90", "quiz3": "90", "quiz4": "90", "quiz5": "90",
            "midterm": "90", "final": "90", "attendance_percent": "90"
        }
    ]

    # write the CSV to disk
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SIMPLE_HEADER)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Run export_at_risk with threshold default (75)
    export_at_risk(filename=str(csv_file), output_file=str(out_file), threshold=reports.PASSING_GRADE)

    # Check that output file exists and contains only the at-risk student
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
    ids = [r["student_id"] for r in reader]
    assert ids == ["s_low"]

    # Check that the function printed the at-risk table and saved message
    captured = capsys.readouterr()
    assert "AT-RISK STUDENTS" in captured.out or "Saved at-risk list" in captured.out or "Saved at-risk list to:" in captured.out
s