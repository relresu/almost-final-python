import csv
import os
import statistics
import analytics  # your existing weighted.py module
import array_operations # select, project, sort, insert, delete
from ingest import clean_ingest # read csv file and validate rows
import reports



# ----------------------

# ----------------------
# File name for the CSV database
FILENAME = "studentRecord.csv"  # CSV file name

# Column names for the student data
HEADER = [
    "student_id",
    "last_name",
    "first_name",
    "section",
    "quiz1",
    "quiz2",
    "quiz3",
    "quiz4",
    "quiz5",
    "midterm",
    "final",
    "attendance_percent"
]



valid_rows, _ = array_operations.clean_ingest("studentRecord.csv", HEADER) # calls the clean_ingest function


# ----------------------
# Main Menu
# ----------------------
def menu():
    while True:
        print("\n=== STUDENT CSV MENU ===")
        print("1. Add and Save Student(s)")
        print("2. Read CSV File")
        print("3. Delete Student by ID")
        print("4. Select Header Column")
        print("5. Project Student Record by Student ID")
        print("6. Sort Student Data")
        print("7. Analytics and Reports")
        print("8. Display Section Records")   
        print("9. Exit")                      

        choice = input("Enter choice: ").strip()

        if choice == "1":
            array_operations.add_data()

        elif choice == "2":
            valid_rows, _ = array_operations.clean_ingest()
            if valid_rows:
                print("\n📘 Valid rows:")
                for row in valid_rows:
                    print(row)

        elif choice == "3":
            array_operations.delete_data()

        elif choice == "4":
            array_operations.select_column()

        elif choice == "5":
            array_operations.select_row()

        elif choice == "6":
            array_operations.sort_data()

        elif choice == "7":
            while True:
                print("\n=== ANALYTICS AND REPORTS MENU ===")
                print("a. Compute Weighted Grades")
                print("b. Grade Distribution (A–F)")
                print("c. Percentiles (Top/Bottom 10%)")
                print("d. Outliers (±1.5 SD)")
                print("e. Improvement (Final vs Midterm)")
                print("f. Summary Report")
                print("g. At-Risk Students (Export CSV)")
                print("h. Back to Main Menu")

                sub = input("Select an option (a–h): ").lower().strip()

                if sub == "a":
                    analytics.compute_grades()
                elif sub == "b":
                    analytics.grade_distribution()
                elif sub == "c":
                    analytics.percentiles()
                elif sub == "d":
                    analytics.outliers()
                elif sub == "e":
                    analytics.improvement()
                elif sub == "f":
                    reports.summary_report()
                elif sub == "g":
                    reports.export_at_risk()
                elif sub == "h":
                    break
                else:
                    print("Invalid choice. Try again.")

        elif choice == "8":  
            section = input("Enter section name (pi,A,AE): ")
            reports.display_section_simple(section)

        elif choice == "9":  
            print("Exiting program...")
            break

        else:
            print("Invalid choice. Try again.")
if __name__ == "__main__":
    menu()
