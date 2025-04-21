from tabulate import tabulate
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
from collections import defaultdict

def build_worker_hours_summary_by_airport(hour_counter):
    """
    Agrupa las horas trabajadas por semana y aeropuerto.
    Entrada: hour_counter con claves (worker_id, iso_year, iso_week)
    Devuelve: dict de (semana_string) → { aeropuerto → [filas] }
    """
    summary = defaultdict(lambda: defaultdict(list))  # semana → aeropuerto → lista de filas

    for (worker_id, year, week), hours in sorted(hour_counter.items()):
        airport, role = parse_worker_id(worker_id)
        week_range = get_week_range_from_year_week(year, week)

        row = {
            "Worker ID": worker_id,
            "Role": role,
            "Hours Worked": round(hours, 2)
        }

        summary[week_range][airport].append(row)

    # Ordenar las listas por Worker ID para mantener consistencia visual
    for week in summary:
        for airport in summary[week]:
            role_order = ["SPV PAX", "CHECKIN", "AG PAX", "COORDI", "SPV RAMP", "DRIV", "OPE_A", "OPE_B"]
            summary[week_range][airport].sort(key=lambda row: (role_order.index(row["Role"]), row["Worker ID"]))

    return summary

def print_worker_hours_summary(hour_counter):
    """
    Prints a summary of total hours worked per worker, grouped by week and airport.
    """
    summary = build_worker_hours_summary_by_airport(hour_counter)

    for week_range in sorted(summary.keys()):
        print(f"\n=== Weekly Summary ({week_range}) ===")
        for airport in sorted(summary[week_range].keys()):
            print(f"Airport: {airport}")
            print(tabulate(summary[week_range][airport], headers="keys", tablefmt="fancy_grid", stralign="center"))

def export_worker_hours_summary_to_pdf(hour_counter, output_path):
    """
    Exports a summary of hours worked to a PDF file, grouped by week and airport.
    """
    summary = build_worker_hours_summary_by_airport(hour_counter)

    with PdfPages(output_path) as pdf:
        for week_range in sorted(summary.keys()):
            for airport in sorted(summary[week_range].keys()):
                df = pd.DataFrame(summary[week_range][airport])
                fig, ax = plt.subplots(figsize=(10, 0.4 * len(df) + 2))
                ax.axis("off")
                ax.set_title(f"Airport: {airport}  //  Week: {week_range}",
                             fontsize=14, fontweight="bold", y=1.02)

                table = ax.table(
                    cellText=df.values,
                    colLabels=df.columns,
                    cellLoc='center',
                    loc='center'
                )
                table.auto_set_font_size(False)
                table.set_fontsize(9)

                pdf.savefig(fig)
                plt.close(fig)

    print(f"PDF summary exported to: {output_path}")

def parse_worker_id(worker_id):
    """
    Extracts airport and full role from a worker ID like 'BCN-SP1'.
    """
    parts = worker_id.split('-')
    if len(parts) >= 2:
        airport = parts[0]
        role_prefix = parts[1][:2]
        role_map = {
            "SP": "SPV PAX", "CH": "CHECKIN", "AP": "AG PAX", "CO": "COORDI",
            "SR": "SPV RAMP", "DR": "DRIV", "OA": "OPE_A", "OB": "OPE_B"
        }
        role = role_map.get(role_prefix, "UNKNOWN")
    else:
        airport = "UNKNOWN"
        role = "UNKNOWN"
    return airport, role

def get_week_range_from_year_week(year, week):
    """
    Returns a string like '8–14 April 2025' for a given ISO year and week number.
    """
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return f"{monday.day}–{sunday.day} {sunday.strftime('%B %Y')}"
