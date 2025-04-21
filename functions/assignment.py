from collections import defaultdict
from datetime import timedelta, date



# Assignment
def assign_greedy_workers(
    shifts,
    flights,
    max_weekly_hours=40,
    existing_workers=None,
    hour_counter=None,
    min_rest_hours_between_shifts=12,
    last_shift_end_time=None,
    max_consecutive_days=6,
    streak_tracker=None,
):
    """
    Greedy shift assignment algorithm:
    - Assigns workers to cover all flights using shifts
    - Respects constraints:
        • ≤ max_weekly_hours per natural week
        • ≥ min_rest_hours_between_shifts between two shifts
        • ≤ max_consecutive_days worked in a row (not natural week)
    - Reuses existing workers when possible; creates new ones otherwise
    """

    # Prefixes used to build worker IDs by role
    role_prefix = {
        "SPV PAX": "SP",  "CHECKIN": "CH", "AG PAX": "AP", "COORDI": "CO",
        "SPV RAMP": "SR", "DRIV": "DR",   "OPE_A": "OA",  "OPE_B": "OB",
    }

    # Initialize persistent structures if not provided
    if existing_workers is None:
        existing_workers = set()
    if hour_counter is None: # Hours worked per worker
        hour_counter = defaultdict(float)  
    if last_shift_end_time is None: # End time last shift
        last_shift_end_time = {} 
    if streak_tracker is None: # How many days in a row has worked
        streak_tracker = {} 

    # No worker assigned to 2 shifts in the same day
    assigned_day = defaultdict(set) 

    # Set of all flights that must be covered
    all_flights = {f["id"] for f in flights}
    covered = set()  # Set of already covered flights
    assignments = []  # Final assignment result

    # Greedy assignment
    while covered != all_flights: # While flights not being assigned
        pending = all_flights - covered # Remaining flights

        # Select shifts that cover at least one pending flight
        valid_shifts = [sh for sh in shifts if any(fid in pending for fid in sh["flights"])]
        if not valid_shifts:
            break  # All flights covered

        # Try to find shifts that match with existing workers
        compatible = []
        for sh in valid_shifts: # For each shift
            role, apt = sh["role"], sh["airport"]
            start = sh["start"]
            iso_year, iso_week, _ = start.date().isocalendar() # Weekly hours control
            day_key = (apt, role, start.date())

            for wid in existing_workers: # get worker
                if not wid.startswith(f"{apt}-{role_prefix.get(role, role[:2].upper())}"):
                    continue
                if wid in assigned_day[day_key]:
                    continue
                # Weekly hours constraint
                if hour_counter[(wid, iso_year, iso_week)] + sh["duration_hours"] > max_weekly_hours:
                    continue
                # Rest between shifts
                last_end = last_shift_end_time.get(wid)
                if last_end and start < last_end + timedelta(hours=min_rest_hours_between_shifts):
                    continue
                # Max consecutive work days
                last_day, streak = streak_tracker.get(wid, (None, 0))
                new_streak = (
                    streak + 1
                    if last_day and start.date() == last_day + timedelta(days=1)
                    else (streak if last_day and start.date() == last_day else 1)
                )
                if new_streak > max_consecutive_days:
                    continue
                compatible.append(sh)
                break  # Found at least one compatible worker

        # If compatible shifts exist, use them; otherwise use any valid
        pool = compatible if compatible else valid_shifts

        # Select the best shift:
        # Priority 1: covers more pending flights
        # Priority 2: shorter duration
        best = min(pool, key=lambda sh: (-len(set(sh["flights"]) & pending), sh["duration_hours"]))

        # Extract shift info
        role, apt = best["role"], best["airport"]
        start, end = best["start"], best["end"]
        iso_year, iso_week, _ = start.date().isocalendar()
        day_key = (apt, role, start.date())
        prefix = role_prefix.get(role, role[:2].upper())

        # Try to assign to an existing worker
        worker_id = None
        for wid in sorted(existing_workers):
            if not wid.startswith(f"{apt}-{prefix}"): # Same airport and role
                continue
            if wid in assigned_day[day_key]: # Not shift that day
                continue
            if hour_counter[(wid, iso_year, iso_week)] + best["duration_hours"] > max_weekly_hours: # Weekly hours restriction
                continue
            last_end = last_shift_end_time.get(wid)
            if last_end and start < last_end + timedelta(hours=min_rest_hours_between_shifts): # Rest between shifts
                continue
            last_day, streak = streak_tracker.get(wid, (None, 0)) # Consecutive days
            new_streak = (
                streak + 1
                if last_day and start.date() == last_day + timedelta(days=1)
                else (streak if last_day and start.date() == last_day else 1)
            )
            if new_streak > max_consecutive_days:
                continue
            # Assign this shift to this worker
            worker_id = wid
            streak_tracker[wid] = (start.date(), new_streak)
            break

        # If no existing worker fits, create a new one
        if worker_id is None:
            worker_id = next_worker_id(apt, prefix, existing_workers)
            existing_workers.add(worker_id)
            streak_tracker[worker_id] = (start.date(), 1)

        # Register assignment and update tracking structures
        assignments.append({"worker_id": worker_id, "shift": best})
        covered.update(best["flights"])
        hour_counter[(worker_id, iso_year, iso_week)] += best["duration_hours"]
        assigned_day[day_key].add(worker_id)
        last_shift_end_time[worker_id] = end

    # Return the final assignments and any flights left uncovered
    return assignments, all_flights - covered


# Generate unique worker IDs
def next_worker_id(apt, prefix, existing): # Existing are currently IDs
    """
    Returns the next available worker ID like 'BCN-SP1', 'BCN-SP2', ...
    """
    nums = [
        int(w[len(f"{apt}-{prefix}") :]) # Extract number
        for w in existing
        if w.startswith(f"{apt}-{prefix}") and w[len(f"{apt}-{prefix}") :].isdigit()
    ]
    return f"{apt}-{prefix}{max(nums, default=0) + 1}"



