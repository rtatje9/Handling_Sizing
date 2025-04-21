from matplotlib.backends.backend_pdf import PdfPages

def plot_shifts_to_pdf(assignments, flights, output_path="Gantt_Assignments.pdf"):
    _generate_shift_plots(assignments, flights, mode="pdf", output_path=output_path)

def plot_shifts_to_screen(assignments, flights):
    _generate_shift_plots(assignments, flights, mode="screen")


def _generate_shift_plots(assignments, flights, mode, output_path=None):
    from datetime import timedelta
    from collections import defaultdict
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Patch 
    from datetime import datetime

    assert mode in {"pdf", "screen"}

    role_order = ["SPV PAX", "CHECKIN", "AG PAX", "COORDI", "SPV RAMP", "DRIV", "OPE_A", "OPE_B"]
    role_colors = {
        "SPV PAX": "#e63946", "CHECKIN": "#f4a261", "AG PAX": "#80cfa9", "COORDI": "#8fbcd4",
        "SPV RAMP": "#e63946", "DRIV": "#f4a261", "OPE_A": "#80cfa9", "OPE_B": "#80cfa9"
    }
    flight_colors = {"Dep": "#08306b", "Arr": "#2171b5", "Arr/Dep": "#deebf7"}

    assgn_grouped = defaultdict(list)
    for a in assignments:
        sh = a["shift"]
        if "airport" not in sh or not sh.get("start_1"):
            continue
        apt = sh["airport"]
        day_str = sh["start_1"].strftime("%Y-%m-%d")
        assgn_grouped[(day_str, apt)].append(a)

    flight_grouped = defaultdict(list)
    for f in flights:
        if "airport" not in f or not f.get("departure"):
            continue
        apt = f["airport"]
        day_str = f["departure"].strftime("%Y-%m-%d")
        flight_grouped[(day_str, apt)].append(f)

    pdf = PdfPages(output_path) if mode == "pdf" else None

    for (day, apt), group_assignments in assgn_grouped.items():
        group_flights = flight_grouped.get((day, apt), [])

        group_assignments.sort(
            key=lambda x: (role_order.index(x["shift"]["role"]) if x["shift"]["role"] in role_order else 99, x["worker_id"])
        )
        group_flights.sort(key=lambda f: f["departure"])

        all_times = []
        for a in group_assignments:
            sh = a["shift"]
            all_times.extend([sh["start_1"], sh["end_1"]])
            if sh.get("split"):
                all_times.extend([sh["start_2"], sh["end_2"]])
        for f in group_flights:
            all_times.extend([f["departure"] - timedelta(minutes=45), f["departure"]])
        if not all_times:
            continue

        min_time = min(all_times) - timedelta(minutes=30)
        max_time = max(all_times) + timedelta(minutes=30)
        min_val = mdates.date2num(min_time)
        max_val = mdates.date2num(max_time)

        num_flights = len(group_flights)
        num_assignments = len(group_assignments)
        row_step = 0.6
        flight_positions = [(num_flights - i - 1) * row_step for i in range(num_flights)]
        assgn_positions = [-(i + 1) * row_step for i in range(num_assignments)]
        total_height = 1 + max(flight_positions) - min(assgn_positions)

        fig, ax = plt.subplots(figsize=(16, total_height + 2))
        fig.subplots_adjust(left=0.15, top=0.90, bottom=0.2)
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        fig.suptitle(f"{apt} // {day} ({day_obj.strftime('%A')})", fontsize=16, y=0.98)
        ax.set_xlim(min_val, max_val)

        for i, f in enumerate(group_flights):
            y_f = flight_positions[i]
            flight_start = f["departure"] - timedelta(minutes=45)
            flight_end = f["departure"]
            start_num = mdates.date2num(flight_start)
            end_num = mdates.date2num(flight_end)
            width = end_num - start_num
            x_departure = end_num
            flight_type = f.get("operation_type", "Dep").title()
            color = flight_colors.get(flight_type, "lightblue")
            ax.barh(y_f, width, left=start_num, height=0.4, color=color, edgecolor="black")
            text_color = "white" if flight_type in ["Arr", "Dep"] else "black"
            ax.text(start_num + width/2, y_f, f["id"], va="center", ha="center", fontsize=8, color=text_color)
            ax.text(end_num + 0.01*(max_val - min_val), y_f, f["departure"].strftime("%H:%M"), va="center", ha="left", fontsize=8)
            flight_id = f["id"]
            for j, a in enumerate(group_assignments):
                y_a = assgn_positions[j]
                if flight_id in a["shift"]["flights"]:
                    ax.plot([x_departure, x_departure], [y_f + 0.2, y_a - 0.2],
                            linestyle='dotted', color='#4a4a4a', linewidth=1.5)
                    ax.plot(x_departure, y_a, 'o', color='#4a4a4a', markeredgecolor='black', markeredgewidth=1, markersize=5)

        if num_flights > 0 and num_assignments > 0:
            sep_y = 0 - (row_step / 2)
            ax.axhline(y=sep_y, color="black", linewidth=1.5)

        for j, a in enumerate(group_assignments):
            y_a = assgn_positions[j]
            sh = a["shift"]
            role = sh["role"]
            color = role_colors.get(role, "gray")
            offset = 0.005 * (max_val - min_val)
            if j > 0 and group_assignments[j-1]["shift"]["role"] == "COORDI" and role == "SPV RAMP":
                div_y = (assgn_positions[j-1] + assgn_positions[j]) / 2
                ax.axhline(y=div_y, color="black", linewidth=1.5)

            if sh.get("start_1") and sh.get("end_1"):
                s1 = mdates.date2num(sh["start_1"])
                e1 = mdates.date2num(sh["end_1"])
                ax.barh(y_a, e1 - s1, left=s1, height=0.4, color=color, edgecolor="black")
                ax.text(s1 - offset, y_a, sh["start_1"].strftime("%H:%M"), ha="right", va="center", fontsize=8)
                ax.text(e1 + offset, y_a, sh["end_1"].strftime("%H:%M"), ha="left", va="center", fontsize=8)

            if sh.get("split") and sh.get("start_2") and sh.get("end_2"):
                s2 = mdates.date2num(sh["start_2"])
                e2 = mdates.date2num(sh["end_2"])
                ax.barh(y_a, e2 - s2, left=s2, height=0.4, color=color, edgecolor="black")
                ax.text(s2 - offset, y_a, sh["start_2"].strftime("%H:%M"), ha="right", va="center", fontsize=8)
                ax.text(e2 + offset, y_a, sh["end_2"].strftime("%H:%M"), ha="left", va="center", fontsize=8)

        y_ticks = flight_positions + assgn_positions
        y_labels = [""] * len(flight_positions) + [a["worker_id"] for a in group_assignments]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_ylim(min(y_ticks) - row_step / 2, max(y_ticks) + row_step / 2)

        ax.xaxis_date()
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        ax.set_ylabel("")
        ax.set_xlabel("Time")
        ax.grid(True, axis="x", linestyle="--", alpha=0.5)

       # Centrado vertical de bloques FLIGHTS, PAX y RAMP
        flight_y_center = (max(flight_positions) + min(flight_positions)) / 2 if flight_positions else 0
        pax_assignments = [a for a in group_assignments if a["shift"]["role"] in {"SPV PAX", "CHECKIN", "AG PAX", "COORDI"}]
        ramp_assignments = [a for a in group_assignments if a["shift"]["role"] in {"SPV RAMP", "DRIV", "OPE_A", "OPE_B"}]

        def center_y(assignments):
            if not assignments:
                return 0
            indices = [group_assignments.index(a) for a in assignments]
            ys = [assgn_positions[i] for i in indices]
            return (max(ys) + min(ys)) / 2

        pax_y_center = center_y(pax_assignments)
        ramp_y_center = center_y(ramp_assignments)

        # Añadir textos en sus posiciones centradas reales
        ax.text(min_val - 0.02 * (max_val - min_val), flight_y_center, "FLIGHTS",
                rotation=90, va="center", ha="center", fontweight='bold', fontsize=10, clip_on=False)
        ax.text(min_val - 0.08 * (max_val - min_val), pax_y_center, "PAX",
                rotation=90, va="center", ha="center", fontweight='bold', fontsize=10, clip_on=False)
        ax.text(min_val - 0.08 * (max_val - min_val), ramp_y_center, "RAMP",
                rotation=90, va="center", ha="center", fontweight='bold', fontsize=10, clip_on=False)
        flight_legend_elements = [
            Patch(facecolor=flight_colors[key], edgecolor='black', label=key) for key in flight_colors
        ]
        ax.legend(
            handles=flight_legend_elements,
            title="Operation Type",
            loc="upper left",
            bbox_to_anchor=(1.01, 1),  # Fuera del gráfico a la derecha
            borderaxespad=0,
            fontsize=8,
            title_fontsize=9
        )

        # Leyenda de abreviaturas de roles
        role_prefix = {
            "SPV PAX": ("SP", "Passenger Supervisor"),
            "CHECKIN": ("CH", "Check-in Staff"),
            "AG PAX": ("AP", "Passenger Agent"),
            "COORDI": ("CO", "Coordinator"),
            "SPV RAMP": ("SR", "Ramp Supervisor"),
            "DRIV": ("DR", "Driver"),
            "OPE_A": ("OA", "Operator A"),
            "OPE_B": ("OB", "Operator B")
        }

        # Convertir a formato legible
        role_legend_text = "\n".join([f"{v[0]} = {v[1]}" for k, v in role_prefix.items()])
        operation_legend_text = "Operation legend:\nDep = Departure\nArr = Arrival\nArr/Dep = Arrival + Departure"


        # Mostrar leyendas
        fig.text(0.01, 0.02, f"Role legend:\n{role_legend_text}", ha="left", va="bottom", fontsize=8)
        fig.text(0.20, 0.02, operation_legend_text, ha="left", va="bottom", fontsize=8)

        if mode == "pdf":
            pdf.savefig(fig)
            plt.close(fig)
        else:
            plt.show()

    if mode == "pdf":
        pdf.close()
        print(f"📄 Gantt exportado correctamente como: {output_path}")
