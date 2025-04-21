from itertools import combinations
from collections import deque

def generate_single_shifts(flights, role_filter=None, airport_filter=None):
    """
    Generates a list of individual shifts (one role per flight) based on the
    presence windows defined in each flight's 'workers' dictionary.    
    """
    single_shifts = []
    
    # Filters flights by airport
    for f in flights:
        if airport_filter and f["airport"] != airport_filter:
            continue
        
        # Iterate through required roles
        for role, times in f["workers"].items():
            # Skip role if doesn't match
            if role_filter and role != role_filter:
                continue
            
            # Shift entry for this role and flight
            shift = {
                'flight_id': f['id'],
                'role': role,
                'airport': f['airport'],
                'start': times['start'],
                'end': times['end'],
                'departure': f['departure']
            }
            single_shifts.append(shift)

    return single_shifts

#################################################

def generate_all_shifts_9h_for_role(shifts_same_role, max_duration_hours, min_separation):
    """
    Generates all valid shift combinations (max 9h) using both individual flights and indivisible blocks.
    Conditions:
      - No repeated flights in a shift
      - Max shift duration
      - Minimum time gap between consecutive flights
    """
    all_valid_shifts = []
    items = []

    # Normalize inputs
    for item in shifts_same_role:
        if isinstance(item, dict) and item.get("indivisible"):
            items.append(item["flights"]) # Block case
        else:
            items.append([item]) # One flight case

    seen_combos = set()

    # Try all combinations 1 to N items. items are all flights, both unique and cluster, r indicate how many items are being combined
    for r in range(1, len(items) + 1):
        # Combine all possible flights, combination tool
        for combo in combinations(items, r):
            flat = [f for block in combo for f in block] # Flatten combination
            flight_ids = tuple(sorted(f["flight_id"] for f in flat)) # Get IDs
            # Skip if flight repeated 
            if len(flight_ids) != len(set(flight_ids)): # Set do not enable duplicates, check if length is reduced
                continue
            # Skip if combination already checked
            if flight_ids in seen_combos:
                continue
            seen_combos.add(flight_ids)
            # Sort flights departure time
            sorted_flights = sorted(flat, key=lambda s: s["departure"])
            # Check separation constraint
            if not consecutive_pairs_ok(sorted_flights, min_separation):
                continue
            # Shift object with shift information
            shift_obj = build_shift_object(sorted_flights)
            # Keep shifts allowed duration
            if shift_obj["duration_hours"] <= max_duration_hours:
                all_valid_shifts.append(shift_obj)

    # Eliminate duplicates
    unique = {}
    for sh in all_valid_shifts:
        key = serialize_shift(sh)
        unique[key] = sh

    return list(unique.values())


def consecutive_pairs_ok(shift_list, min_separation):
    """
    Checks that, for each consecutive pair of flights in the list,
    the time gap between them is greater than min_separation (in minutes),
    unless both flights belong to the same indivisible block (same 'block_id').
    """
    # Sort the flights by departure time
    sorted_list = sorted(shift_list, key=lambda s: s['departure'])

    # Loop through each pair of consecutive flights
    for i in range(len(sorted_list) - 1):
        flight1 = sorted_list[i]
        flight2 = sorted_list[i+1]

        # If both flights belong to the same block, skip the check
        if flight1.get("block_id") is not None and flight1.get("block_id") == flight2.get("block_id"):
            continue

        # Calculate the gap between the two flights (in minutes)
        gap = (flight2["departure"] - flight1["departure"]).total_seconds() / 60.0

        # If the gap is too small, this combination is invalid
        if gap <= min_separation:
            return False

    # If all consecutive pairs are valid, return True
    return True




def build_shift_object(shift_list):  # Receives a list of consecutive flights
    """
    Given a list of consecutive flights (same role and airport),
    creates a full shift dictionary containing:
      - flights: list of flight IDs (ordered by departure time)
      - role and airport
      - shift start and end times
      - total effective duration in hours (adjusted if split shift)
      - split: True if there's a valid break (1-5 hours), otherwise False
      - start_1, end_1: first part of the shift
      - start_2, end_2: second part of the shift (if split)
    """

    # Sort by departure time
    sorted_list = sorted(shift_list, key=lambda s: s['departure'])

    # Extract 
    flight_ids = [s['flight_id'] for s in sorted_list]           # List of flight IDs
    role = sorted_list[0]['role']                                # All flights share same role
    airport = sorted_list[0]['airport']                          # All flights share same airport
    start_time = sorted_list[0]['start']                         # Shift start = first flight's start time
    end_time = sorted_list[-1]['end']                            # Shift end = last flight's end time

    # Calculate total shift duration (without adjusting for breaks)
    total_duration = (end_time - start_time).total_seconds() / 3600.0

    # Check for a valid break (split shift: a gap of 1 to 5 hours between flights)
    pause_minutes = 0
    split = False # If split
    split_index = None # At which flight starts second shift
    for i in range(len(sorted_list) - 1):
        gap = (sorted_list[i+1]['start'] - sorted_list[i]['end']).total_seconds() / 60.0
        if 60 <= gap <= 300:  # 1 to 5 hours = valid split
            split = True
            pause_minutes += gap
            split_index = i + 1  # Index where the second block starts
            break

    # Subtract break time from total duration to get effective shift duration
    effective_duration = total_duration - (pause_minutes / 60.0)

    # Define shift blocks: if split, separate into 2 parts
    if split and split_index is not None:
        block1 = sorted_list[:split_index]
        block2 = sorted_list[split_index:]
        start_1 = block1[0]['start']
        end_1 = block1[-1]['end']
        start_2 = block2[0]['start']
        end_2 = block2[-1]['end']
    else:
        # No split: single block
        start_1 = start_time
        end_1 = end_time
        start_2 = end_2 = None

    # Return the full shift object
    return {
        'flights': flight_ids,
        'role': role,
        'airport': airport,
        'start': start_time,
        'end': end_time,
        'duration_hours': round(effective_duration, 2),
        'split': split,
        'start_1': start_1,
        'end_1': end_1,
        'start_2': start_2,
        'end_2': end_2
    }



def serialize_shift(shift_obj):
    """
    Converts a shift object into an immutable key (tuple),
    which can be used to identify duplicate shifts.    
    """
    # Sorted tuple
    flights_tuple = tuple(sorted(shift_obj['flights']))
    return (flights_tuple, shift_obj['role'], shift_obj['airport'], shift_obj['start'], shift_obj['end'])







