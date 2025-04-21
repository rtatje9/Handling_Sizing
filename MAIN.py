# MIRAR TÍTULO GANTT, ESPACIO HASTA TURNOS
'''
─────────────────────────────────────────────────────────────────────────────
MAIN.py
Sizing methodology for airport ground handling personnel and equipment

This script executes the full sizing and scheduling process for airport
handling staff using real operational data and role-specific constraints.

Inputs:
  - Excel files with flight schedules and role-based operation rules.


Output:
  - Gantt charts of worker assignments
  - Tabular assignment report
  - Weekly summary of worked hours per employee

Dependencies:
  - pandas
  - matplotlib
  - numpy
  - tabulate
  - datetime
  - collections


Author: Roger Tatjé
─────────────────────────────────────────────────────────────────────────────
'''

from functions.flight_data import load_excel_data
from functions.worker_data import load_worker_shift_rules
from functions.builder import build_flight_objects
from functions.shift_generation import generate_single_shifts, generate_all_shifts_9h_for_role
from functions.assignment import assign_greedy_workers
from functions.cluster_group import generate_fixed_cluster_shifts, find_all_valid_clusters, select_best_non_overlapping_clusters
from functions.print_shifts import print_shifts_table, print_worker_assignments, export_assignments_to_pdf
from functions.print_results import plot_shifts_to_pdf, plot_shifts_to_screen
from functions.hours_summary import print_worker_hours_summary, export_worker_hours_summary_to_pdf

from collections import defaultdict

# Input Files
flight_excel_data = "Basic_Data.xlsx"
worker_excel_data = "Workers_shift.xlsx"

# Parámetros configurables  
MAX_SHIFT_DURATION = 9  # hours
CLUSTER_GAP_MINUTES = 20  # minutes
MAX_WEEKLY_HOURS = 40 # hours
MIN_REST_HOURS_BETWEEN_SHIFTS = 12  # hours
MAX_CONSECUTIVE_DAYS = 6 # days

# Output Parameters
output_path_gantt_pdf = "Worker_Assignments_Gantt.pdf"
output_path_table_pdf = "Worker_Assignments_Table.pdf"
summary_output_pdf = "Worker_Hours_Summary.pdf"  # O cambia por input si quieres pedirlo al usuario



# 1. Load flights data from excel
df = load_excel_data(flight_excel_data)

# 2. Load rules for each role and operation type
worker_rules = load_worker_shift_rules(worker_excel_data)

# 3. Build flight objects with time windows for each applicable role
flights = build_flight_objects(df, worker_rules)

# Get unique airports
unique_airports = sorted({f["airport"] for f in flights})
# print("Unique airports detected:", unique_airports)

# Get roles
roles_in_data = list(worker_rules.keys())
# print("Detected roles:", roles_in_data)

# Initialize global lists and tracking structures
all_shifts = []
all_assignments = []
existing_workers = set()                 # Set of already created worker IDs
hour_counter = defaultdict(float)        # Tracks worked hours per worker per natural week
last_shift_end_time = {}                 # Last shift end time per worker
streak_tracker = {}                      # Tracks streaks of consecutive working days per worker


# 4) For each role
for role in roles_in_data:
    # 5) For each airport
    for airport in unique_airports:
        # Get all single shifts for this role at this airport
        shifts_this_role_airport = generate_single_shifts(flights, role_filter=role, airport_filter=airport)

        # Get days
        days_in_airport = sorted({s["departure"].date() for s in shifts_this_role_airport})
        # 6) For each day for role and airport
        for day in days_in_airport:
            # Filters current day
            shifts_this_day = [s for s in shifts_this_role_airport if s["departure"].date() == day] # 
            cluster_blocks = [] 
            cluster_flight_ids = set() 

            # 7) Identify clusters
            if role in {"SPV PAX", "CHECKIN", "SPV RAMP", "DRIV"}:
                # Find candidate clusters
                all_candidate_clusters = find_all_valid_clusters(shifts_this_day, role, CLUSTER_GAP_MINUTES)
                # Select the best non-overlapping clusters
                clusters = select_best_non_overlapping_clusters(all_candidate_clusters)
                # For each cluster
                for cluster in clusters:
                    # Generate shifts
                    bloques = generate_fixed_cluster_shifts(cluster)
                    cluster_blocks.extend(bloques)
                    # Flights already covered
                    for bloque in bloques:
                        cluster_flight_ids.update(f["flight_id"] for f in bloque["flights"])

            # 8) Remaining shifts
            remaining_shifts = [s for s in shifts_this_day if s["flight_id"] not in cluster_flight_ids]

            # Combine
            inputs_for_generation = cluster_blocks + remaining_shifts

            # 9) Generate all valid pairings
            all_shifts_that_day = generate_all_shifts_9h_for_role(inputs_for_generation, max_duration_hours=MAX_SHIFT_DURATION, min_separation=CLUSTER_GAP_MINUTES)

            # 10) Assign workers greedy
            print(f"Task {role}, Airport {airport}, Day {day}")
            print_shifts_table(all_shifts_that_day)

            all_shifts.extend(all_shifts_that_day) # All shifts (across all roles, days, and airports)

            assignments, not_covered = assign_greedy_workers(
                    all_shifts_that_day,
                    flights,
                    MAX_WEEKLY_HOURS,
                    existing_workers,
                    hour_counter,
                    MIN_REST_HOURS_BETWEEN_SHIFTS,
                    last_shift_end_time,
                    MAX_CONSECUTIVE_DAYS,          
                    streak_tracker                 
            )
            all_assignments.extend(assignments)

            if not_covered:
                print(f"WARNING: {len(not_covered)} flight(s) not covered: {sorted(not_covered)}")

# 11) Summary shift generation and assignments
print(f"Total shifts generated across all roles: {len(all_shifts)}")
print(f"Total workers assigned: {len(all_assignments)}")

# 12) Print final assignments (screen)
print("=== Final assignment table ===")
print_worker_assignments(all_assignments)
# plot_shifts_to_screen(all_assignments, flights) # Gantt
# print_worker_hours_summary(hour_counter) # Screen


# Export to PDF
plot_shifts_to_pdf(all_assignments, flights, output_path_gantt_pdf) # Gantt
export_assignments_to_pdf(all_assignments, output_path_table_pdf) # Table
export_worker_hours_summary_to_pdf(hour_counter, output_path=summary_output_pdf) # Hours summary





