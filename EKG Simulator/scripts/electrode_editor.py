from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import tkinter as tk
except ModuleNotFoundError:  # pragma: no cover - depends on local Python build
    tk = None

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except Exception:  # pragma: no cover - depends on local Python build
    FigureCanvasTkAgg = None
    Figure = None


ROOT_DIR = Path(__file__).resolve().parents[1]
LEADS_FILE = ROOT_DIR / "backend" / "app" / "domain" / "leads.py"
CANVAS_SIZE = 420
CANVAS_PADDING = 32
AXIS_LIMIT = 1.2
POINT_RADIUS = 8


@dataclass
class PlaneDefinition:
    title: str
    axis_x: str
    axis_y: str


PLANES = [
    PlaneDefinition("Plano XY", "x", "y"),
    PlaneDefinition("Plano XZ", "x", "z"),
    PlaneDefinition("Plano YZ", "y", "z"),
]


LEAD_COLORS = {
    "V1": "#c84c36",
    "V2": "#dd6e42",
    "V3": "#e58f64",
    "V4": "#0d6b73",
    "V5": "#147d64",
    "V6": "#40916c",
    "V3R": "#7b2cbf",
    "V4R": "#9d4edd",
    "V7": "#1d3557",
    "V8": "#457b9d",
    "V9": "#5fa8d3",
}


PRECORDIAL_BLOCK_PATTERN = re.compile(
    r"PRECORDIAL_LEADS: dict\[str, np\.ndarray\] = \{\n(?P<body>.*?)\n\}",
    re.DOTALL,
)
ENTRY_PATTERN = re.compile(
    r'^\s*"(?P<lead>[^"]+)":\s*chest_lead\((?P<x>[-\d.]+),\s*(?P<y>[-\d.]+),\s*(?P<z>[-\d.]+)\),?$'
)


class PlaneCanvas:
    def __init__(self, app: "ElectrodeEditorApp", parent: tk.Widget, plane: PlaneDefinition) -> None:
        self.app = app
        self.plane = plane
        self.frame = tk.Frame(parent, bg="#f6f1eb", bd=1, relief="solid")
        self.title = tk.Label(
            self.frame,
            text=f"{plane.title} ({plane.axis_x.upper()} x {plane.axis_y.upper()})",
            font=("Helvetica", 14, "bold"),
            bg="#f6f1eb",
            fg="#11262d",
        )
        self.title.pack(pady=(10, 4))
        self.canvas = tk.Canvas(
            self.frame,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg="#fffdf9",
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=(0, 12))
        self.drag_lead: str | None = None
        self.canvas.bind("<Button-1>", self.on_pointer_down)
        self.canvas.bind("<B1-Motion>", self.on_pointer_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_pointer_up)

    @property
    def drawable_size(self) -> float:
        return CANVAS_SIZE - 2 * CANVAS_PADDING

    def axis_to_canvas(self, x_value: float, y_value: float) -> tuple[float, float]:
        px = CANVAS_PADDING + ((x_value + AXIS_LIMIT) / (2 * AXIS_LIMIT)) * self.drawable_size
        py = CANVAS_PADDING + ((AXIS_LIMIT - y_value) / (2 * AXIS_LIMIT)) * self.drawable_size
        return px, py

    def canvas_to_axis(self, px: float, py: float) -> tuple[float, float]:
        x_value = ((px - CANVAS_PADDING) / self.drawable_size) * (2 * AXIS_LIMIT) - AXIS_LIMIT
        y_value = AXIS_LIMIT - ((py - CANVAS_PADDING) / self.drawable_size) * (2 * AXIS_LIMIT)
        return self.clamp(x_value), self.clamp(y_value)

    @staticmethod
    def clamp(value: float) -> float:
        return max(-AXIS_LIMIT, min(AXIS_LIMIT, value))

    def draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")

        left, top = CANVAS_PADDING, CANVAS_PADDING
        right, bottom = CANVAS_SIZE - CANVAS_PADDING, CANVAS_SIZE - CANVAS_PADDING
        mid_x = (left + right) / 2
        mid_y = (top + bottom) / 2

        canvas.create_rectangle(left, top, right, bottom, outline="#d9d2c7", width=1)
        canvas.create_line(left, mid_y, right, mid_y, fill="#d9d2c7", dash=(4, 4))
        canvas.create_line(mid_x, top, mid_x, bottom, fill="#d9d2c7", dash=(4, 4))
        canvas.create_text(mid_x, top - 14, text=self.plane.axis_y.upper(), fill="#5c6b73", font=("Helvetica", 11, "bold"))
        canvas.create_text(right + 16, mid_y, text=self.plane.axis_x.upper(), fill="#5c6b73", font=("Helvetica", 11, "bold"))

        for lead, coords in self.app.leads.items():
            px, py = self.axis_to_canvas(coords[self.plane.axis_x], coords[self.plane.axis_y])
            color = LEAD_COLORS.get(lead, "#0d6b73")
            width = 3 if lead == self.app.selected_lead else 1
            canvas.create_oval(
                px - POINT_RADIUS,
                py - POINT_RADIUS,
                px + POINT_RADIUS,
                py + POINT_RADIUS,
                fill=color,
                outline="#11262d",
                width=width,
                tags=(f"lead:{lead}",),
            )
            canvas.create_text(
                px,
                py - 16,
                text=lead,
                fill="#11262d",
                font=("Helvetica", 10, "bold"),
                tags=(f"lead:{lead}",),
            )

    def pick_lead(self, event: tk.Event[tk.Canvas]) -> str | None:
        current = self.canvas.find_withtag("current")
        if not current:
            return None
        for tag in self.canvas.gettags(current[0]):
            if tag.startswith("lead:"):
                return tag.split(":", 1)[1]
        return None

    def on_pointer_down(self, event: tk.Event[tk.Canvas]) -> None:
        lead = self.pick_lead(event)
        if lead is None:
            return
        self.drag_lead = lead
        self.app.select_lead(lead)
        self.on_pointer_move(event)

    def on_pointer_move(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_lead is None:
            return
        px = max(CANVAS_PADDING, min(CANVAS_SIZE - CANVAS_PADDING, event.x))
        py = max(CANVAS_PADDING, min(CANVAS_SIZE - CANVAS_PADDING, event.y))
        value_x, value_y = self.canvas_to_axis(px, py)
        self.app.update_lead_axes(
            self.drag_lead,
            self.plane.axis_x,
            value_x,
            self.plane.axis_y,
            value_y,
        )

    def on_pointer_up(self, _event: tk.Event[tk.Canvas]) -> None:
        self.drag_lead = None


class ElectrodeEditorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Editor de Derivacoes Precordiais")
        self.root.configure(bg="#efe7dc")
        self.lead_order, self.leads = self.load_leads()
        self.selected_lead = self.lead_order[0]
        self.status_var = tk.StringVar(value=f"Arquivo: {LEADS_FILE}")
        self.detail_var = tk.StringVar()
        self.is_dirty = False

        self.build_layout()
        self.refresh()

    def build_layout(self) -> None:
        header = tk.Frame(self.root, bg="#efe7dc")
        header.pack(fill="x", padx=18, pady=(16, 10))

        tk.Label(
            header,
            text="Editor de Derivacoes",
            font=("Helvetica", 20, "bold"),
            bg="#efe7dc",
            fg="#11262d",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Arraste os pontos em XY, XZ e YZ. O preview 3D atualiza automaticamente; o arquivo so muda ao clicar em Salvar.",
            font=("Helvetica", 11),
            bg="#efe7dc",
            fg="#42535a",
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.root, bg="#efe7dc")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        sidebar = tk.Frame(body, bg="#f6f1eb", bd=1, relief="solid", width=250)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Derivacoes",
            font=("Helvetica", 14, "bold"),
            bg="#f6f1eb",
            fg="#11262d",
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.listbox = tk.Listbox(
            sidebar,
            height=14,
            exportselection=False,
            font=("Menlo", 12),
            selectbackground="#d7ebe5",
            selectforeground="#11262d",
        )
        self.listbox.pack(fill="x", padx=14)
        for lead in self.lead_order:
            self.listbox.insert("end", lead)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_from_list)

        tk.Label(
            sidebar,
            textvariable=self.detail_var,
            justify="left",
            anchor="nw",
            font=("Menlo", 11),
            bg="#f6f1eb",
            fg="#11262d",
        ).pack(fill="both", expand=True, padx=14, pady=(12, 8))

        actions = tk.Frame(sidebar, bg="#f6f1eb")
        actions.pack(fill="x", padx=14, pady=(0, 14))

        tk.Button(
            actions,
            text="Salvar",
            command=self.save_leads,
            bg="#0d6b73",
            fg="white",
            relief="flat",
            padx=12,
            pady=8,
        ).pack(fill="x")

        tk.Button(
            actions,
            text="Recarregar do arquivo",
            command=self.reload_from_disk,
            bg="#d9d2c7",
            fg="#11262d",
            relief="flat",
            padx=12,
            pady=8,
        ).pack(fill="x", pady=(8, 0))

        self.status_label = tk.Label(
            sidebar,
            textvariable=self.status_var,
            wraplength=210,
            justify="left",
            bg="#f6f1eb",
            fg="#42535a",
            font=("Helvetica", 10),
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 14))

        planes_frame = tk.Frame(body, bg="#efe7dc")
        planes_frame.pack(side="left", fill="both", expand=True)

        self.plane_canvases: list[PlaneCanvas] = []
        for index, plane in enumerate(PLANES):
            plane_canvas = PlaneCanvas(self, planes_frame, plane)
            row = index // 2
            column = index % 2
            plane_canvas.frame.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")
            self.plane_canvases.append(plane_canvas)

        planes_frame.grid_columnconfigure(0, weight=1)
        planes_frame.grid_columnconfigure(1, weight=1)
        planes_frame.grid_rowconfigure(0, weight=1)
        planes_frame.grid_rowconfigure(1, weight=1)

        preview_frame = tk.Frame(body, bg="#f6f1eb", bd=1, relief="solid")
        preview_frame.pack(side="left", fill="both", expand=True, padx=(14, 0))

        tk.Label(
            preview_frame,
            text="Preview 3D",
            font=("Helvetica", 14, "bold"),
            bg="#f6f1eb",
            fg="#11262d",
        ).pack(anchor="w", padx=14, pady=(14, 8))

        if FigureCanvasTkAgg is None or Figure is None:
            tk.Label(
                preview_frame,
                text="Matplotlib/TkAgg nao esta disponivel neste Python.\nO editor 2D funciona, mas o preview 3D nao pode ser exibido.",
                justify="left",
                bg="#f6f1eb",
                fg="#8f1d14",
                font=("Helvetica", 11),
            ).pack(anchor="w", padx=14, pady=(0, 14))
            self.figure = None
            self.preview_canvas = None
            self.preview_axes = None
        else:
            self.figure = Figure(figsize=(6.3, 6.8), dpi=100, facecolor="#fffdf9")
            self.preview_axes = self.figure.add_subplot(111, projection="3d")
            self.preview_canvas = FigureCanvasTkAgg(self.figure, master=preview_frame)
            self.preview_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def load_leads(self) -> tuple[list[str], dict[str, dict[str, float]]]:
        content = LEADS_FILE.read_text(encoding="utf-8")
        block_match = PRECORDIAL_BLOCK_PATTERN.search(content)
        if block_match is None:
            raise RuntimeError("Nao foi possivel localizar PRECORDIAL_LEADS em leads.py")

        lead_order: list[str] = []
        leads: dict[str, dict[str, float]] = {}
        for raw_line in block_match.group("body").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            entry_match = ENTRY_PATTERN.match(line)
            if entry_match is None:
                continue
            lead = entry_match.group("lead")
            lead_order.append(lead)
            leads[lead] = {
                "x": float(entry_match.group("x")),
                "y": float(entry_match.group("y")),
                "z": float(entry_match.group("z")),
            }
        if not leads:
            raise RuntimeError("Nenhuma derivacao precordial foi lida de leads.py")
        return lead_order, leads

    def save_leads(self) -> None:
        content = LEADS_FILE.read_text(encoding="utf-8")
        lines = ["PRECORDIAL_LEADS: dict[str, np.ndarray] = {"]
        for lead in self.lead_order:
            coords = self.leads[lead]
            lines.append(
                f'    "{lead}": chest_lead({coords["x"]:.2f}, {coords["y"]:.2f}, {coords["z"]:.2f}),'
            )
        lines.append("}")
        replacement = "\n".join(lines)
        updated = PRECORDIAL_BLOCK_PATTERN.sub(replacement, content, count=1)
        LEADS_FILE.write_text(updated, encoding="utf-8")
        self.is_dirty = False
        self.status_var.set(f"Salvo em {LEADS_FILE.name}")

    def reload_from_disk(self) -> None:
        self.lead_order, self.leads = self.load_leads()
        if self.selected_lead not in self.leads:
            self.selected_lead = self.lead_order[0]
        self.is_dirty = False
        self.status_var.set(f"Recarregado de {LEADS_FILE.name}")
        self.refresh()

    def select_lead(self, lead: str) -> None:
        self.selected_lead = lead
        index = self.lead_order.index(lead)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.update_detail_text()
        self.redraw_planes()

    def on_select_from_list(self, _event: tk.Event[tk.Listbox]) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.select_lead(self.lead_order[selection[0]])

    def update_lead_axes(self, lead: str, axis_a: str, value_a: float, axis_b: str, value_b: float) -> None:
        self.leads[lead][axis_a] = round(value_a, 2)
        self.leads[lead][axis_b] = round(value_b, 2)
        self.selected_lead = lead
        self.is_dirty = True
        self.status_var.set(f"Alteracoes pendentes em {LEADS_FILE.name}")
        self.update_detail_text()
        self.redraw_planes()
        self.redraw_preview()

    def update_detail_text(self) -> None:
        coords = self.leads[self.selected_lead]
        self.detail_var.set(
            f"{self.selected_lead}\n\n"
            f"x = {coords['x']:.2f}\n"
            f"y = {coords['y']:.2f}\n"
            f"z = {coords['z']:.2f}\n\n"
            f"status = {'nao salvo' if self.is_dirty else 'salvo'}\n\n"
            "Planos:\n"
            "XY define largura e anterioridade\n"
            "XZ define largura e altura\n"
            "YZ define anterioridade e altura"
        )

    def redraw_planes(self) -> None:
        for plane_canvas in self.plane_canvases:
            plane_canvas.draw()

    def redraw_preview(self) -> None:
        if self.preview_axes is None or self.preview_canvas is None:
            return

        ax = self.preview_axes
        ax.clear()

        scale = 0.9
        z_basal, z_mid, z_apical = 0.25, -0.25, -0.9
        slope1 = (z_mid - z_apical) / 0.4
        slope2 = (z_basal - z_mid) / 0.3
        ring_colors = [
            "#8FAADC", "#F6BD60", "#F28482", "#84A59D", "#90BE6D", "#F7EDE2",
            "#CDB4DB", "#FFC8DD", "#B5838D", "#A0C4FF", "#BDB2FF", "#FFD6A5",
            "#CAFFBF", "#FFADAD", "#D0F4DE", "#FDFFB6", "#9BF6FF",
        ]
        angles_basal = [0, 60, 120, 180, 240, 300]
        angles_mid = [0, 60, 120, 180, 240, 300]
        angles_apical = [45, 135, 225, 315]

        def z_func(radius: float) -> float:
            if radius < 0.4:
                return z_apical + slope1 * radius
            if radius < 0.7:
                return z_mid + slope2 * (radius - 0.4)
            return z_basal + slope2 * (radius - 0.7)

        def draw_segment(inner_radius: float, outer_radius: float, start_deg: float, end_deg: float, color: str) -> None:
            import numpy as np

            if end_deg <= start_deg:
                end_deg += 360
            radii = np.linspace(inner_radius, outer_radius, 12)
            angles = np.deg2rad(np.linspace(start_deg, end_deg, 26))
            rr, tt = np.meshgrid(radii, angles)
            x = scale * rr * np.cos(tt)
            y = scale * rr * np.sin(tt)
            z = np.vectorize(z_func)(rr)
            ax.plot_surface(x, y, z, color=color, linewidth=0, antialiased=False, shade=False, alpha=0.7)

        color_index = 0
        for index, start_deg in enumerate(angles_basal):
            end_deg = angles_basal[(index + 1) % len(angles_basal)]
            draw_segment(0.7, 1.0, start_deg, end_deg, ring_colors[color_index])
            color_index += 1
        for index, start_deg in enumerate(angles_mid):
            end_deg = angles_mid[(index + 1) % len(angles_mid)]
            draw_segment(0.4, 0.7, start_deg, end_deg, ring_colors[color_index])
            color_index += 1
        for index, start_deg in enumerate(angles_apical):
            end_deg = angles_apical[(index + 1) % len(angles_apical)]
            draw_segment(0.18, 0.4, start_deg, end_deg, ring_colors[color_index])
            color_index += 1
        draw_segment(0.0, 0.18, 0, 360, ring_colors[16])

        import numpy as np

        theta_line = np.linspace(0, 2 * np.pi, 280)
        for radius, width in [(0.18, 2.6), (0.4, 2.6), (0.7, 2.6), (1.0, 3.2)]:
            ax.plot(
                scale * radius * np.cos(theta_line),
                scale * radius * np.sin(theta_line),
                [z_func(radius)] * len(theta_line),
                color="black",
                linewidth=width,
            )
        for angle_deg in angles_basal:
            angle = np.deg2rad(angle_deg)
            ax.plot(
                [scale * 0.7 * np.cos(angle), scale * 1.0 * np.cos(angle)],
                [scale * 0.7 * np.sin(angle), scale * 1.0 * np.sin(angle)],
                [z_func(0.7), z_func(1.0)],
                color="black",
                linewidth=1.8,
            )
        for angle_deg in angles_mid:
            angle = np.deg2rad(angle_deg)
            ax.plot(
                [scale * 0.4 * np.cos(angle), scale * 0.7 * np.cos(angle)],
                [scale * 0.4 * np.sin(angle), scale * 0.7 * np.sin(angle)],
                [z_func(0.4), z_func(0.7)],
                color="black",
                linewidth=1.8,
            )
        for angle_deg in angles_apical:
            angle = np.deg2rad(angle_deg)
            ax.plot(
                [scale * 0.18 * np.cos(angle), scale * 0.4 * np.cos(angle)],
                [scale * 0.18 * np.sin(angle), scale * 0.4 * np.sin(angle)],
                [z_func(0.18), z_func(0.4)],
                color="black",
                linewidth=1.8,
            )

        for lead, coords in self.leads.items():
            color = LEAD_COLORS.get(lead, "#0d6b73")
            marker_size = 58 if lead == self.selected_lead else 34
            ax.scatter(coords["x"], coords["y"], coords["z"], color=color, s=marker_size, edgecolors="#11262d", linewidths=0.8)
            ax.text(coords["x"], coords["y"], coords["z"] + 0.04, lead, fontsize=9, color="#11262d")

        ax.set_title("Bullseye 3D + eletrodos", pad=16, color="#11262d")
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_zlim(-1.1, 1.1)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.view_init(elev=24, azim=38)
        ax.set_box_aspect((1, 1, 1))
        ax.xaxis.pane.set_facecolor((1.0, 0.99, 0.97, 0.0))
        ax.yaxis.pane.set_facecolor((1.0, 0.99, 0.97, 0.0))
        ax.zaxis.pane.set_facecolor((1.0, 0.99, 0.97, 0.0))
        self.figure.tight_layout()
        self.preview_canvas.draw_idle()

    def refresh(self) -> None:
        self.select_lead(self.selected_lead)
        self.redraw_planes()
        self.redraw_preview()


def main() -> None:
    if tk is None:
        raise RuntimeError(
            "tkinter nao esta disponivel neste Python. No macOS, use um Python com Tk "
            "ou instale python-tk e execute novamente."
        )
    if FigureCanvasTkAgg is None or Figure is None:
        raise RuntimeError(
            "Matplotlib com backend TkAgg nao esta disponivel neste Python. "
            "Use um Python do macOS com Tk para abrir o editor com preview 3D."
        )
    root = tk.Tk()
    app = ElectrodeEditorApp(root)
    root.minsize(1280, 820)
    root.mainloop()


if __name__ == "__main__":
    main()
