from datetime import timedelta
import math
from functions.shift_generation import consecutive_pairs_ok, build_shift_object
from itertools import combinations




def find_all_valid_clusters(shifts, role, max_gap_minutes):
    """
    Finds all valid clusters (consecutive flights) where all flight pairs are within the allowed gap.
    """
    if role not in {"SPV PAX", "CHECKIN", "SPV RAMP", "DRIV"}:
        return []

    # Sort by departure
    sorted_shifts = sorted(shifts, key=lambda s: s["departure"])

    valid_clusters = []

    # Try all combinations of 2 or more flights
    for r in range(2, len(sorted_shifts) + 1):
        for combo in combinations(sorted_shifts, r):
            # Check that all consecutive pairs in the combo meet the gap condition
            is_valid = True
            for i in range(len(combo) - 1):
                t1 = combo[i]["departure"]
                t2 = combo[i+1]["departure"]
                gap = (t2 - t1).total_seconds() / 60
                if gap > max_gap_minutes:
                    is_valid = False
                    break
            if is_valid:
                valid_clusters.append(list(combo))

    return valid_clusters

######################

def select_best_non_overlapping_clusters(clusters):
    """
    Selects a subset of non-overlapping clusters that maximizes flight coverage.
    """
    selected = []
    used_flight_ids = set()

    # Sort descending
    clusters = sorted(clusters, key=lambda c: -len(c))

    for cluster in clusters:
        # Current cluster
        cluster_ids = {f['flight_id'] for f in cluster}
        if cluster_ids & used_flight_ids:
            continue  # Skip if it overlaps with already selected
        selected.append(cluster)
        used_flight_ids.update(cluster_ids)

    return selected


######################################




def generate_fixed_cluster_shifts(cluster):
    """
    Given a cluster (list of close flights),
    applies the 0.6 rule to determine how many workers are needed,
    and splits the flights optimally among them.
    Returns a list of indivisible blocks, each with a block_id.
    """
    if not cluster:
        return []

    # Sort the cluster by departure time
    sorted_cluster = sorted(cluster, key=lambda f: f["departure"])
    num_flights = len(sorted_cluster)

    # Determine number of workers using the 0.6 rule
    if num_flights < 3:
        num_workers = 1
    else:
        num_workers = math.ceil(num_flights * 0.6)

    # Distribute flights among workers
    flight_groups = distribute_cluster_flights(sorted_cluster, num_workers)

    blocks = []
    block_counter = 1

    for group in flight_groups:
        # Unique block ID for this group
        block_id = f"block_{block_counter}"
        # Assign ID to each flight
        for flight in group:
            flight["block_id"] = block_id
        # Group as indivisible
        blocks.append({
            "flights": group,
            "indivisible": True,
            "block_id": block_id
        })
        block_counter += 1

    return blocks





def distribute_cluster_flights(cluster_flights, num_workers):
    """
    Distributes the flights of a cluster among the required number of workers.
    Returns a list of lists, where each sublist contains the flights assigned to one worker.
    The distribution uses round-robin.
    """
    # Sort the flights by departure time
    sorted_flights = sorted(cluster_flights, key=lambda f: f["departure"])

    # Initialize an empty list for each worker
    distributed = [[] for _ in range(num_workers)]

    # Distribute flights in round-robin
    for i, flight in enumerate(sorted_flights):
        worker_index = i % num_workers
        distributed[worker_index].append(flight)

    return distributed
