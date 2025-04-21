from tabulate import tabulate
import numpy as np
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import textwrap




def print_shifts_table(shifts):
    """
    Prints a  table that summarizes shifts.
    """

    # Group shifts by (flights, role, airport, start, end)
    grouped = defaultdict(list)
    for sh in shifts:
        key = (
            tuple(sorted(sh['flights'])),  # Ensure order doesn't affect grouping
            sh['role'],
            sh['airport'],
            sh['start'],
            sh['end']
        )
        grouped[key].append(sh)  # Append the shift to its corresponding group

    rows = []
    for group, turnos in grouped.items():
        sh = turnos[0]  # Use the first shift in the group as reference
        repetitions = len(turnos)  # Number of times this identical shift appears
        flights_str = ", ".join(sh['flights'])  # Concatenate flight IDs into one string
        day = sh['start'].strftime("%d-%m")  # Format date (day and month)

        # Format start and end times of each block (if available)
        start1 = sh['start_1'].strftime("%H:%M") if sh.get('start_1') else np.nan
        end1   = sh['end_1'].strftime("%H:%M")   if sh.get('end_1') else np.nan
        start2 = sh['start_2'].strftime("%H:%M") if sh.get('start_2') else np.nan
        end2   = sh['end_2'].strftime("%H:%M")   if sh.get('end_2') else np.nan

        # Add row to the output list
        rows.append({
            "Flights": flights_str,                      # Flight IDs
            "#": len(sh['flights']),                     # Number of flights in the shift
            "Role": sh['role'],                          # Role (e.g. CHECKIN, SPV PAX...)
            "APT": sh['airport'],                        # Airport
            "D": day,                                    # Date
            "S1": start1,                                # Start of block 1
            "E1": end1,                                  # End of block 1
            "S2": start2,                                # Start of block 2 (if split)
            "E2": end2,                                  # End of block 2 (if split)
            "Dur(h)": round(sh['duration_hours'], 2),    # Total effective duration
            "Split": "true" if sh.get("split", False) else "false",  # Indicates if it's a split shift
            "#Workers": repetitions                      # How many times this shift repeats
        })

    print("Generated Shifts:")
    # Tabulate renders full content nicely
    print(tabulate(rows, headers="keys", tablefmt="fancy_grid", stralign="center"))
    
    
def print_worker_assignments(assignments):
    """
    Imprime tablas separadas por día y dentro de cada una agrupadas por aeropuerto.
    Una fila por trabajador asignado, mostrando su turno y si proviene de un clúster o no.
    """
    # Agrupar por día
    grouped_by_day = {}
    for a in assignments:
        sh = a["shift"]
        day = sh['start'].strftime("%Y-%m-%d")
        if day not in grouped_by_day:
            grouped_by_day[day] = []
        grouped_by_day[day].append(a)

    # Imprimir tabla para cada día
    for day in sorted(grouped_by_day.keys()):
        print(f"=== Día {day} ===")
        day_assignments = grouped_by_day[day]
        grouped_by_apt = {}
        for a in day_assignments:
            apt = a["shift"]["airport"]
            if apt not in grouped_by_apt:
                grouped_by_apt[apt] = []
            grouped_by_apt[apt].append(a)
            
        # Imprimir por aeropuerto
        for apt in sorted(grouped_by_apt.keys()):
            print(f" Aeropuerto: {apt}")
            rows = []
            for a in grouped_by_apt[apt]:
                sh = a['shift']
                flights_str = ", ".join(sh['flights'])
                rows.append({
                    "Worker": a['worker_id'],
                    "Role": sh['role'],
                    "Flights": flights_str,
                    "S1": sh['start_1'].strftime("%H:%M") if sh.get("start_1") else "",
                    "E1": sh['end_1'].strftime("%H:%M") if sh.get("start_1") else "",
                    "S2": sh['start_2'].strftime("%H:%M") if sh.get("start_2") else "",
                    "E2": sh['end_2'].strftime("%H:%M") if sh.get("start_2") else "",
                    "Dur(h)": round(sh['duration_hours'], 2),
                    "Split": "true" if sh.get("split", False) else "false",
                })
            print(tabulate(rows, headers="keys", tablefmt="fancy_grid", stralign="center"))


def export_assignments_to_pdf(assignments, output_path="Worker_Assignments.pdf"):
    def wrap_flight_text(flights, max_line_length=40):
        return textwrap.fill(", ".join(flights), width=max_line_length)

    pax_roles = {"SPV PAX", "CHECKIN", "AG PAX", "COORDI"}
    ramp_roles = {"SPV RAMP", "DRIV", "OPE_A", "OPE_B"}

    role_colors = {
        "SPV PAX": "#e63946",
        "CHECKIN": "#f4a261",
        "AG PAX": "#80cfa9",
        "COORDI": "#8fbcd4",
        "SPV RAMP": "#e63946",
        "DRIV": "#f4a261",
        "OPE_A": "#80cfa9",
        "OPE_B": "#80cfa9",
    }

    grouped = defaultdict(lambda: defaultdict(list))
    for a in assignments:
        sh = a["shift"]
        day = sh["start"].strftime("%Y-%m-%d")
        apt = sh["airport"]
        grouped[day][apt].append(a)

    with PdfPages(output_path) as pdf:
        for day in sorted(grouped):
            day_obj = datetime.strptime(day, "%Y-%m-%d")
            weekday_name = day_obj.strftime("%A")
            for apt in sorted(grouped[day]):

                # Separar asignaciones por grupo de rol
                pax_rows = []
                ramp_rows = []

                for a in grouped[day][apt]:
                    sh = a['shift']
                    row = {
                        "Worker": a['worker_id'],
                        "Role": sh['role'],
                        "Flights": wrap_flight_text(sh['flights']),
                        "S1": sh['start_1'].strftime("%H:%M") if sh.get("start_1") else "",
                        "E1": sh['end_1'].strftime("%H:%M") if sh.get("start_1") else "",
                        "S2": sh['start_2'].strftime("%H:%M") if sh.get("start_2") else "",
                        "E2": sh['end_2'].strftime("%H:%M") if sh.get("start_2") else "",
                        "Dur(h)": round(sh['duration_hours'], 2),
                        "Split": "true" if sh.get("split", False) else "false",
                    }
                    if sh["role"] in pax_roles:
                        pax_rows.append(row)
                    elif sh["role"] in ramp_roles:
                        ramp_rows.append(row)

                df_pax = pd.DataFrame(pax_rows)
                df_ramp = pd.DataFrame(ramp_rows)
                total_rows = len(df_pax) + len(df_ramp)
                fig_height = 0.5 * total_rows + 3

                fig, ax = plt.subplots(figsize=(14, fig_height))
                fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.1)
                ax.axis("off")
                ax.set_title(f"{apt} // {day} ({weekday_name})", fontsize=16, fontweight='bold', y=1.02)

                y_offset = 1.0
                cell_height = 1.0 / (total_rows + 6)

                def draw_table(df, label):
                    nonlocal y_offset
                    if df.empty:
                        return

                    # Título de bloque como tabla
                    title_table = ax.table(
                        cellText=[[label]],
                        colLabels=None,
                        loc='upper left',
                        bbox=[0, y_offset - cell_height * 1.2, 1, cell_height * 1.2]
                    )
                    title_table.auto_set_font_size(False)
                    title_table.set_fontsize(11)
                    title_cell = title_table[0, 0]
                    title_cell.set_text_props(fontweight='bold', ha='center', va='center')
                    title_cell.visible_edges = "open"
                    title_cell.set_facecolor("#e0e0e0")

                    y_offset -= cell_height * 1.5

                    table = ax.table(
                        cellText=df.values,
                        colLabels=df.columns,
                        cellLoc='center',
                        loc='upper left',
                        bbox=[0, y_offset - cell_height * (len(df) + 1), 1, cell_height * (len(df) + 1)]
                    )

                    flights_col_idx = df.columns.get_loc("Flights")
                    role_col_idx = df.columns.get_loc("Role")

                    for key, cell in table.get_celld().items():
                        row_idx, col_idx = key

                        # Ajuste de anchos
                        if col_idx == flights_col_idx:
                            cell.set_width(0.45)
                            cell.set_text_props(ha='left', va='center')
                        else:
                            cell.set_width(0.06)

                        # Pintar fondo en columna "Role"
                        if row_idx > 0 and col_idx == role_col_idx:
                            role_value = df.iloc[row_idx - 1]["Role"]
                            color = role_colors.get(role_value, "#ffffff")
                            cell.set_facecolor(color)

                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    y_offset -= cell_height * (len(df) + 2)

                draw_table(df_pax, "TURNO PASAJEROS")
                draw_table(df_ramp, "TURNO RAMPA")

                pdf.savefig(fig)
                plt.close(fig)

    print(f"📄 PDF exportado correctamente como: {output_path}")
