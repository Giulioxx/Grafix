import math
import re
import random
import tkinter as tk
from tkinter import messagebox, colorchooser

import numpy as np

try:
    from scipy.optimize import brentq as _brentq
    _HAVE_BRENTQ = True
except Exception:
    _brentq = None
    _HAVE_BRENTQ = False

from models import Point, Line, Circle, FunctionPlot, ImplicitPlot
from utils import ExpressionHelper
from graph_canvas import GraphCanvas

PALETTE = ["#2c3e50", "#8e44ad", "#16a085", "#c0392b", "#d35400",
           "#2980b9", "#7f8c8d", "#f39c12", "#27ae60", "#e74c3c"]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Grafix")
        self.root.geometry("1420x790")
        self.root.configure(bg="#dddddd")

        self.points = []
        self.lines = []
        self.circles = []
        self.functions = []
        self.implicits = []

        self.point_counter = 0
        self.line_counter = 0
        self.circle_counter = 0
        self.function_counter = 0
        self.implicit_counter = 0

        self.mode_buttons = {}
        self.selected_for_action = []
        self._point_rows = []
        self._object_rows = []

        self.build_ui()
        self.update_lists()
        self.graph.set_mode("move")

    # ----- Colore -----
    def _random_color(self):
        return random.choice(PALETTE)

    # ----- UI -----
    def build_ui(self):
        top = tk.Frame(self.root, bg="#cfcfcf", bd=1, relief="raised")
        top.pack(fill="x")

        tk.Label(top, text="Disegno:", bg="#cfcfcf").pack(side="left", padx=(6, 4))
        self.add_mode_button(top, "move", "Muovi", 10)
        self.add_mode_button(top, "new_point", "Nuovo punto", 12)
        self.add_mode_button(top, "new_segment", "Nuovo segmento", 14)
        self.add_mode_button(top, "new_line", "Nuova retta", 12)
        self.add_mode_button(top, "new_circle", "Nuovo cerchio", 12)

        tk.Label(top, text=" Costruzioni:", bg="#cfcfcf").pack(side="left", padx=(10, 4))
        self.add_mode_button(top, "midpoint", "Punto medio", 12)
        self.add_mode_button(top, "intersection", "Intersezione", 12)
        self.add_mode_button(top, "distance", "Distanza", 12)

        tk.Button(top, text="Cambia colore", width=12,
                  command=self.change_selected_color).pack(side="left", padx=2, pady=4)
        tk.Button(top, text="Vista iniziale", width=12,
                  command=self.reset_view).pack(side="left", padx=2, pady=4)
        tk.Button(top, text="Elimina scelto", width=12,
                  command=self.delete_selected).pack(side="left", padx=2, pady=4)

        body = tk.Frame(self.root, bg="#dddddd")
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#ececec", width=420, bd=1, relief="groove")
        left.pack(side="left", fill="y", padx=4, pady=4)
        left.pack_propagate(False)

        graph_area = tk.Frame(body, bg="#c8c8c8", bd=1, relief="sunken")
        graph_area.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=4)

        self.graph = GraphCanvas(graph_area, self)
        self.graph.frame.pack(fill="both", expand=True)

        self.root.bind("<Key>", self._on_key)

        tk.Label(left, text="Input formule", bg="#ececec",
                 font=("Arial", 11, "bold")).pack(pady=(8, 4))
        row = tk.Frame(left, bg="#ececec")
        row.pack(fill="x", padx=8)
        self.input_entry = tk.Entry(row)
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<Return>", lambda e: self.process_input())
        self.input_entry.bind("<KeyRelease>",
                              lambda e: self._prettify_entry(self.input_entry, e))
        tk.Button(row, text="Inserisci", width=10,
                  command=self.process_input).pack(side="left", padx=(6, 0))

        box1 = tk.LabelFrame(left, text="Punti", bg="#ececec")
        box1.pack(fill="x", padx=8, pady=(0, 6))
        self.points_list = tk.Listbox(box1, height=8, exportselection=False,
                                      selectmode=tk.SINGLE)
        self.points_list.pack(fill="x", padx=4, pady=4)
        self.points_list.bind("<<ListboxSelect>>", self.on_points_select)

        box2 = tk.LabelFrame(left, text="Oggetti", bg="#ececec")
        box2.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.objects_list = tk.Listbox(box2, height=15, exportselection=False,
                                       selectmode=tk.SINGLE)
        self.objects_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.objects_list.bind("<<ListboxSelect>>", self.on_objects_select)

        calc = tk.LabelFrame(left, text="Calcolatrice", bg="#ececec")
        calc.pack(fill="x", padx=8, pady=(0, 8))
        crow = tk.Frame(calc, bg="#ececec")
        crow.pack(fill="x", padx=4, pady=4)
        self.calc_entry = tk.Entry(crow)
        self.calc_entry.pack(side="left", fill="x", expand=True)
        self.calc_entry.bind("<Return>", lambda e: self.run_calculator())
        self.calc_entry.bind("<KeyRelease>",
                             lambda e: self._prettify_entry(self.calc_entry, e))
        tk.Button(crow, text="Calcola", width=10,
                  command=self.run_calculator).pack(side="left", padx=(6, 0))
        self.calc_result = tk.Label(calc, text="Risultato:", bg="#ececec", anchor="w")
        self.calc_result.pack(fill="x", padx=4, pady=(0, 4))

        bottom = tk.Frame(self.root, bg="#d3d3d3", bd=1, relief="sunken")
        bottom.pack(fill="x")
        self.status = tk.Label(bottom, text="Pronto. Scegli uno strumento sopra.",
                               bg="#d3d3d3", anchor="w")
        self.status.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(bottom, text="Made by @ItsMeGiulioxx", bg="#d3d3d3",
                 anchor="e", fg="#444444").pack(side="right", padx=6)

    def add_mode_button(self, parent, key, text, width):
        b = tk.Button(parent, text=text, width=width,
                      command=lambda k=key: self.start_action_mode(k))
        b.pack(side="left", padx=2, pady=4)
        self.mode_buttons[key] = b

    def start_action_mode(self, key):
        self.selected_for_action = []
        self.graph.set_mode(key)

    def update_mode_buttons(self):
        for key, btn in self.mode_buttons.items():
            if self.graph.mode == key:
                btn.config(relief="sunken", bg="#bdbdbd")
            else:
                btn.config(relief="raised", bg="#f0f0f0")

    def set_status(self, text):
        self.status.config(text=text)

    def reset_view(self):
        self.graph.reset_view()
        self.set_status("Vista iniziale ripristinata")

    # ----- Gestione dati -----
    def get_points_dict(self):
        return {p.name: p for p in self.points}

    def get_point_by_name(self, name):
        return next((p for p in self.points if p.name == name), None)

    def point_exists(self, name):
        return any(p.name == name for p in self.points)

    def is_point_used_elsewhere(self, point_name):
        for line in self.lines:
            if point_name in (line.p1_name, line.p2_name):
                return True
        for circle in self.circles:
            if point_name in (circle.center_name, circle.radius_point_name):
                return True
        return False

    def remove_point_by_name(self, point_name):
        self.points = [p for p in self.points if p.name != point_name]

    def _fmt_num(self, v):
        v = round(float(v), 4)
        return int(v) if v == int(v) else v

    def update_lists(self):
        self.points_list.delete(0, tk.END)
        self._point_rows = []
        for p in self.points:
            self.points_list.insert(
                tk.END, f"{p.name} = ({self._fmt_num(p.x)}, {self._fmt_num(p.y)})")
            self._point_rows.append(p)

        self.objects_list.delete(0, tk.END)
        self._object_rows = []

        for l in self.lines:
            tipo = "segmento" if l.segment else "retta"
            self._add_object_row(f"{tipo}: {l.name} ({l.p1_name},{l.p2_name})", ("line", l))
        for c in self.circles:
            if c.display_name:
                txt = f"cerchio: {c.name} ({c.display_name})"
            elif c.from_equation:
                txt = (f"cerchio: {c.name} (centro ({self._fmt_num(c.cx)},"
                       f"{self._fmt_num(c.cy)}), raggio {self._fmt_num(c.radius)})")
            else:
                txt = f"cerchio: {c.name} ({c.center_name},{c.radius_point_name})"
            self._add_object_row(txt, ("circle", c))
        for f in self.functions:
            self._add_object_row(f"funzione: {f.name} (y = {f.display})", ("function", f))
        for q in self.implicits:
            self._add_object_row(f"{q.label}: {q.name} ({q.display})", ("implicit", q))

    def _add_object_row(self, text, kind_obj):
        self.objects_list.insert(tk.END, text)
        self._object_rows.append(kind_obj)

    def on_points_select(self, event=None):
        if self.points_list.curselection():
            self.objects_list.selection_clear(0, tk.END)

    def on_objects_select(self, event=None):
        if self.objects_list.curselection():
            self.points_list.selection_clear(0, tk.END)

    def _selected_point(self):
        sel = self.points_list.curselection()
        if sel and 0 <= sel[0] < len(self._point_rows):
            return self._point_rows[sel[0]]
        return None

    def _selected_object(self):
        sel = self.objects_list.curselection()
        if sel and 0 <= sel[0] < len(self._object_rows):
            return self._object_rows[sel[0]]
        return None

    # ----- Creazione oggetti -----
    def create_point(self, x, y, name=None, color="red", return_point=False):
        if not name:
            self.point_counter += 1
            name = "P" + str(self.point_counter)
            while self.point_exists(name):
                self.point_counter += 1
                name = "P" + str(self.point_counter)
        elif self.point_exists(name):
            self.remove_point_by_name(name)
        p = Point(name, x, y, color=color)
        self.points.append(p)
        self.update_lists()
        self.graph.redraw()
        return p if return_point else None

    def create_segment_from_names(self, p1, p2, color="black"):
        self.line_counter += 1
        self.lines.append(Line(f"s{self.line_counter}", p1, p2, color=color, segment=True))
        self.update_lists()
        self.graph.redraw()
        self.set_status("Segmento creato")

    def create_line_from_names(self, p1, p2, color="blue"):
        self.line_counter += 1
        self.lines.append(Line(f"r{self.line_counter}", p1, p2, color=color, segment=False))
        self.update_lists()
        self.graph.redraw()
        self.set_status("Retta creata")

    def create_circle_from_names(self, center, border, color="green"):
        pd = self.get_points_dict()
        c, b = pd.get(center), pd.get(border)
        if not c or not b:
            self.set_status("Cerchio non creato: punti mancanti")
            return
        radius = math.dist((c.x, c.y), (b.x, b.y))
        if radius < 0.1:
            self.set_status("Cerchio non creato: raggio troppo piccolo")
            messagebox.showerror("Errore", "Il raggio del cerchio è troppo piccolo.")
            return
        self.circle_counter += 1
        self.circles.append(Circle(f"c{self.circle_counter}", center, border, color=color))
        self.update_lists()
        self.graph.redraw()
        self.set_status("Cerchio creato")

    def create_midpoint_from_segment(self, seg):
        pd = self.get_points_dict()
        p1, p2 = pd.get(seg.p1_name), pd.get(seg.p2_name)
        if not p1 or not p2:
            return
        mx = round((p1.x + p2.x) / 2, 2)
        my = round((p1.y + p2.y) / 2, 2)
        self.create_point(mx, my, color="orange")
        self.set_status("Punto medio creato")

    # ----- Colore -----
    def get_selected_color(self):
        color = colorchooser.askcolor(title="Scegli colore")
        return color[1] if color and color[1] else None

    def change_selected_color(self):
        target_point = self._selected_point()
        target_object = self._selected_object()
        if target_point is None and target_object is None:
            self.set_status("Seleziona un punto o un oggetto a sinistra")
            return
        color = self.get_selected_color()
        if not color:
            return
        if target_point is not None:
            target_point.color = color
            self.set_status("Colore punto cambiato")
        else:
            _, obj = target_object
            obj.color = color
            self.set_status("Colore oggetto cambiato")
        self.graph.redraw()

    # ----- Parser cerchio da equazione -----
    def parse_circle_explicit(self, eq_str):
        original = eq_str.strip()
        eq = original.replace("^", "**").replace(" ", "")
        if eq.endswith("=0"):
            eq = eq[:-2]

        num = r"\d+(?:\.\d+)?"
        gx = rf"(?:x|\(x([+-]{num})\))"
        gy = rf"(?:y|\(y([+-]{num})\))"
        pattern = rf"^{gx}\*\*2\+{gy}\*\*2=({num})$"
        m = re.match(pattern, eq)
        if not m:
            return None
        try:
            h = -float(m.group(1)) if m.group(1) else 0.0
            k = -float(m.group(2)) if m.group(2) else 0.0
            r2 = float(m.group(3))
            if r2 <= 0:
                return None
            return (h, k, math.sqrt(r2)), original
        except ValueError:
            return None

    # ----- Limiti globali (per le intersezioni) -----
    def _get_global_bounds(self, margin=0.2):
        xs, ys = [], []
        pd = self.get_points_dict()
        for p in self.points:
            xs.append(p.x); ys.append(p.y)
        for c in self.circles:
            cx, cy = c.get_center(pd)
            r = c.get_radius(pd)
            if cx is not None and cy is not None:
                xs.append(cx); ys.append(cy)
                if r is not None:
                    xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        for line in self.lines:
            for nm in (line.p1_name, line.p2_name):
                p = pd.get(nm)
                if p:
                    xs.append(p.x); ys.append(p.y)
        if not xs:
            return -10, 10, -10, 10
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        dx = (xmax - xmin) * margin if xmax != xmin else 1.0
        dy = (ymax - ymin) * margin if ymax != ymin else 1.0
        return xmin - dx, xmax + dx, ymin - dy, ymax + dy

    # ----- Intersezioni (core) -----
    def get_line_points(self, line):
        pd = self.get_points_dict()
        return pd.get(line.p1_name), pd.get(line.p2_name)

    def is_point_on_segment(self, x, y, p1, p2):
        return (min(p1.x, p2.x) - 1e-6 <= x <= max(p1.x, p2.x) + 1e-6 and
                min(p1.y, p2.y) - 1e-6 <= y <= max(p1.y, p2.y) + 1e-6)

    def line_line_intersections(self, l1, l2):
        p1, p2 = self.get_line_points(l1)
        p3, p4 = self.get_line_points(l2)
        if not all((p1, p2, p3, p4)):
            return []
        d1x, d1y = p1.x - p2.x, p1.y - p2.y
        d2x, d2y = p3.x - p4.x, p3.y - p4.y
        den = d1x * d2y - d1y * d2x
        scale = math.hypot(d1x, d1y) * math.hypot(d2x, d2y)
        if scale == 0 or abs(den) < 1e-12 * scale:
            return []
        x = ((p1.x * p2.y - p1.y * p2.x) * (p3.x - p4.x) -
             (p1.x - p2.x) * (p3.x * p4.y - p3.y * p4.x)) / den
        y = ((p1.x * p2.y - p1.y * p2.x) * (p3.y - p4.y) -
             (p1.y - p2.y) * (p3.x * p4.y - p3.y * p4.x)) / den
        if l1.segment and not self.is_point_on_segment(x, y, p1, p2):
            return []
        if l2.segment and not self.is_point_on_segment(x, y, p3, p4):
            return []
        return [(round(x, 6), round(y, 6))]

    def line_circle_intersections(self, line, circle):
        p1, p2 = self.get_line_points(line)
        pd = self.get_points_dict()
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if not all((p1, p2)) or cx is None or cy is None or r is None:
            return []
        dx, dy = p2.x - p1.x, p2.y - p1.y
        fx, fy = p1.x - cx, p1.y - cy
        a = dx * dx + dy * dy
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r * r
        disc = b * b - 4 * a * c
        if disc < 0 or a == 0:
            return []
        sq = math.sqrt(disc)
        q = -0.5 * (b + math.copysign(sq, b))
        t_candidates = []
        if a != 0:
            t_candidates.append(q / a)
        if q != 0:
            t_candidates.append(c / q)
        if not t_candidates:
            t_candidates = [-b / (2 * a)]
        pts = []
        for t in t_candidates:
            if line.segment and not (0 <= t <= 1):
                continue
            pt = (round(p1.x + t * dx, 6), round(p1.y + t * dy, 6))
            if pt not in pts:
                pts.append(pt)
        return pts

    def circle_circle_intersections(self, c1, c2):
        pd = self.get_points_dict()
        cx1, cy1 = c1.get_center(pd)
        cx2, cy2 = c2.get_center(pd)
        r1, r2 = c1.get_radius(pd), c2.get_radius(pd)
        if None in (cx1, cy1, cx2, cy2, r1, r2):
            return []
        d = math.dist((cx1, cy1), (cx2, cy2))
        if d == 0 or d > r1 + r2 or d < abs(r1 - r2):
            return []
        a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
        h2 = r1 * r1 - a * a
        if h2 < 0:
            return []
        h = math.sqrt(h2)
        xm = cx1 + a * (cx2 - cx1) / d
        ym = cy1 + a * (cy2 - cy1) / d
        rx = -(cy2 - cy1) * (h / d)
        ry = (cx2 - cx1) * (h / d)
        out = []
        for pt in [(round(xm + rx, 6), round(ym + ry, 6)),
                   (round(xm - rx, 6), round(ym - ry, 6))]:
            if pt not in out:
                out.append(pt)
        return out

    def function_function_intersections(self, f1, f2):
        xmin, xmax, _, _ = self._get_global_bounds(margin=0.5)
        xs = np.linspace(xmin, xmax, 3000)

        def diff(x):
            try:
                return f1.evaluate(x) - f2.evaluate(x)
            except Exception:
                return np.nan

        pts = []
        for x in self._find_roots(diff, xs):
            try:
                y = float(f1.evaluate(x))
            except Exception:
                continue
            if math.isfinite(y):
                x, y = self._snap_point(float(x), y)
                pts.append((round(x, 6), round(y, 6)))
        return self._unique_points(pts, tol=1e-3)

    def function_line_intersections(self, f, line):
        p1, p2 = self.get_line_points(line)
        if not p1 or not p2:
            return []
        if abs(p2.x - p1.x) < 1e-12:
            x = p1.x
            try:
                y = float(f.evaluate(x))
            except Exception:
                return []
            if math.isfinite(y) and self._point_on_line_or_segment(x, y, line):
                return [(round(x, 6), round(y, 6))]
            return []
        m = (p2.y - p1.y) / (p2.x - p1.x)
        q = p1.y - m * p1.x
        xmin, xmax, _, _ = self._get_global_bounds(margin=0.5)
        xs = np.linspace(xmin, xmax, 3000)

        def diff(x):
            try:
                return f.evaluate(x) - (m * x + q)
            except Exception:
                return np.nan

        pts = []
        for x in self._find_roots(diff, xs):
            try:
                y = float(f.evaluate(x))
            except Exception:
                continue
            if math.isfinite(y) and self._point_on_line_or_segment(x, y, line):
                pts.append((round(x, 6), round(y, 6)))
        return self._unique_points(pts)

    def function_circle_intersections(self, f, circle):
        pd = self.get_points_dict()
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or cy is None or r is None:
            return []
        xmin, xmax, _, _ = self._get_global_bounds(margin=0.5)
        xs = np.linspace(xmin, xmax, 5000)

        def diff(x):
            try:
                y = f.evaluate(x)
                return (x - cx) ** 2 + (y - cy) ** 2 - r * r
            except Exception:
                return np.nan

        pts = []
        for x in self._find_roots(diff, xs, y_tol=1e-6):
            try:
                y = float(f.evaluate(x))
            except Exception:
                continue
            if math.isfinite(y) and self._point_on_circle(x, y, circle):
                pts.append((round(x, 6), round(y, 6)))
        return self._unique_points(pts)

    # ----- Implicite -----
    def _implicit_value(self, imp, x, y):
        try:
            value = imp.evaluate(x, y)
            if isinstance(value, np.ndarray):
                return np.array(value, dtype=float)
            return float(value)
        except Exception:
            if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
                shape = np.broadcast(np.asarray(x), np.asarray(y)).shape
                return np.full(shape, np.nan)
            return np.nan

    def _point_on_implicit(self, point, imp, tol=1e-6):
        val = self._implicit_value(imp, point.x, point.y)
        return not np.isnan(val) and abs(val) <= tol

    def implicit_line_intersections(self, imp, line):
        p1, p2 = self.get_line_points(line)
        if not p1 or not p2:
            return []
        dx, dy = p2.x - p1.x, p2.y - p1.y
        xmin, xmax, ymin, ymax = self._get_global_bounds(margin=0.5)
        if line.segment:
            tmin, tmax = 0.0, 1.0
        else:
            tvals = []
            if abs(dx) > 1e-12:
                tvals += [(xmin - p1.x) / dx, (xmax - p1.x) / dx]
            if abs(dy) > 1e-12:
                tvals += [(ymin - p1.y) / dy, (ymax - p1.y) / dy]
            tmin, tmax = (min(tvals), max(tvals)) if tvals else (-100, 100)
        t_samples = np.linspace(tmin, tmax, 2000)

        def func(t):
            return self._implicit_value(imp, p1.x + t * dx, p1.y + t * dy)

        pts = []
        for t in self._find_roots(func, t_samples):
            x, y = p1.x + t * dx, p1.y + t * dy
            if self._point_on_line_or_segment(x, y, line):
                pts.append((round(x, 6), round(y, 6)))
        return self._unique_points(pts)

    def implicit_circle_intersections(self, imp, circle):
        pd = self.get_points_dict()
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or cy is None or r is None or r <= 0:
            return []
        theta = np.linspace(0, 2 * np.pi, 800)

        def func(th):
            return self._implicit_value(imp, cx + r * np.cos(th), cy + r * np.sin(th))

        pts = []
        for th in self._find_roots(func, theta):
            pts.append((round(cx + r * math.cos(th), 6), round(cy + r * math.sin(th), 6)))
        return self._unique_points(pts)

    def implicit_function_intersections(self, imp, func):
        xmin, xmax, _, _ = self._get_global_bounds(margin=0.5)
        xs = np.linspace(xmin, xmax, 3000)

        def h(x):
            try:
                y = func.evaluate(x)
                return self._implicit_value(imp, x, y)
            except Exception:
                return np.nan

        pts = []
        for x in self._find_roots(h, xs):
            try:
                y = float(func.evaluate(x))
            except Exception:
                continue
            if math.isfinite(y):
                pts.append((round(x, 6), round(y, 6)))
        return self._unique_points(pts)

    def _newton_2d(self, imp1, imp2, x0, y0, max_iter=25, tol=1e-10):
        x, y = float(x0), float(y0)
        for _ in range(max_iter):
            f1 = self._implicit_value(imp1, x, y)
            f2 = self._implicit_value(imp2, x, y)
            if any(np.isnan(v) or not math.isfinite(v) for v in (f1, f2)):
                return None
            if max(abs(f1), abs(f2)) < tol:
                return (x, y)
            h = max(1e-7, 1e-6 * max(1.0, abs(x), abs(y)))
            vals = [self._implicit_value(imp1, x + h, y), self._implicit_value(imp1, x - h, y),
                    self._implicit_value(imp1, x, y + h), self._implicit_value(imp1, x, y - h),
                    self._implicit_value(imp2, x + h, y), self._implicit_value(imp2, x - h, y),
                    self._implicit_value(imp2, x, y + h), self._implicit_value(imp2, x, y - h)]
            if any(np.isnan(v) or not math.isfinite(v) for v in vals):
                return None
            j11 = (vals[0] - vals[1]) / (2 * h)
            j12 = (vals[2] - vals[3]) / (2 * h)
            j21 = (vals[4] - vals[5]) / (2 * h)
            j22 = (vals[6] - vals[7]) / (2 * h)
            J = np.array([[j11, j12], [j21, j22]], dtype=float)
            F = np.array([f1, f2], dtype=float)
            try:
                delta = np.linalg.solve(J, -F)
            except np.linalg.LinAlgError:
                try:
                    delta = -np.linalg.pinv(J).dot(F)
                except Exception:
                    return None
            if not np.all(np.isfinite(delta)):
                return None
            norm0 = max(abs(f1), abs(f2))
            step, accepted = 1.0, False
            for _ in range(10):
                xn, yn = x + step * float(delta[0]), y + step * float(delta[1])
                g1 = self._implicit_value(imp1, xn, yn)
                g2 = self._implicit_value(imp2, xn, yn)
                if (math.isfinite(g1) and math.isfinite(g2)
                        and max(abs(g1), abs(g2)) < norm0):
                    accepted = True
                    break
                step *= 0.5
            if not accepted:
                xn, yn = x + float(delta[0]), y + float(delta[1])
            x, y = xn, yn
            if step * np.linalg.norm(delta, ord=np.inf) < tol:
                break
        f1 = self._implicit_value(imp1, x, y)
        f2 = self._implicit_value(imp2, x, y)
        if math.isfinite(f1) and math.isfinite(f2) and max(abs(f1), abs(f2)) < 1e-8:
            return (x, y)
        return None

    def implicit_implicit_intersections(self, imp1, imp2):
        xmin, xmax, ymin, ymax = self._get_global_bounds(margin=0.2)
        nx, ny = 220, 220
        xs = np.linspace(xmin, xmax, nx)
        ys = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(xs, ys)
        Z1 = np.array(self._implicit_value(imp1, X, Y), dtype=float)
        Z2 = np.array(self._implicit_value(imp2, X, Y), dtype=float)

        cells = self._straddle_cells(Z1) & self._straddle_cells(Z2)
        jj, ii = np.where(cells)

        pts = []
        for j, i in zip(jj, ii):
            xc = (xs[i] + xs[i + 1]) / 2
            yc = (ys[j] + ys[j + 1]) / 2
            refined = self._newton_2d(imp1, imp2, xc, yc)
            if refined is not None:
                x, y = refined
                if xmin - 1e-6 <= x <= xmax + 1e-6 and ymin - 1e-6 <= y <= ymax + 1e-6:
                    pts.append((round(x, 8), round(y, 8)))
        return self._unique_points(pts, tol=1e-5)

    @staticmethod
    def _straddle_cells(Z):
        a, b = Z[:-1, :-1], Z[:-1, 1:]
        c, d = Z[1:, :-1], Z[1:, 1:]
        stack = np.stack([a, b, c, d])
        valid = np.all(np.isfinite(stack), axis=0)
        with np.errstate(invalid="ignore"):
            mn, mx = np.min(stack, axis=0), np.max(stack, axis=0)
        return valid & (mn <= 0) & (mx >= 0)

    # ----- Supporto alle radici -----
    def _refine_scalar_root(self, func, a, b, x0=None, y_tol=1e-10, max_iter=80):
        left, right = (a, b) if a <= b else (b, a)

        # ----- Brent sul bracket -----
        if _HAVE_BRENTQ and left < right:
            try:
                fl, fr = float(func(left)), float(func(right))
                if math.isfinite(fl) and math.isfinite(fr) and fl * fr < 0:
                    return float(_brentq(lambda t: float(func(t)), left, right,
                                         xtol=1e-13, rtol=1e-14, maxiter=200))
            except Exception:
                pass

        # ----- Newton smorzato + bisezione -----
        x = (left + right) / 2 if x0 is None else min(max(x0, left), right)
        for _ in range(max_iter):
            try:
                fx = float(func(x))
            except Exception:
                break
            if not math.isfinite(fx):
                break
            if abs(fx) < y_tol:
                return x
            h = max(1e-8, 1e-6 * max(1.0, abs(x)))
            try:
                fp, fm = float(func(x + h)), float(func(x - h))
            except Exception:
                fp = fm = np.nan
            if math.isfinite(fp) and math.isfinite(fm):
                dfx = (fp - fm) / (2 * h)
                if abs(dfx) > 1e-14:
                    xn = x - fx / dfx
                    if left <= xn <= right and math.isfinite(xn):
                        x = xn
                        continue
            mid = (left + right) / 2
            try:
                fleft, fmid = float(func(left)), float(func(mid))
            except Exception:
                break
            if math.isfinite(fleft) and math.isfinite(fmid) and fleft * fmid <= 0:
                right = mid
            else:
                left = mid
            x = (left + right) / 2
            if right - left < 1e-12:
                return x
        return x

    def _find_roots(self, func, x_samples, y_tol=1e-7, dedup_tol=1e-6):
        x_samples = np.asarray(x_samples, dtype=float)
        n = x_samples.size
        if n < 2:
            return []

        # ----- Valutazione (vettoriale + fallback scalare) -----
        vals = None
        try:
            with np.errstate(all="ignore"):
                arr = np.asarray(func(x_samples), dtype=float)
            if arr.shape == x_samples.shape:
                vals = np.where(np.isfinite(arr), arr, np.nan)
        except Exception:
            vals = None
        if vals is None:
            vals = np.empty(n, dtype=float)
            for i, x in enumerate(x_samples):
                try:
                    v = float(func(x))
                    vals[i] = v if math.isfinite(v) else np.nan
                except Exception:
                    vals[i] = np.nan

        finite = vals[np.isfinite(vals)]
        fscale = float(np.median(np.abs(finite))) if finite.size else 1.0
        if not math.isfinite(fscale) or fscale <= 0:
            fscale = 1.0

        roots = []
        node_tol = max(y_tol, 1e-9 * fscale)
        accept_tol = max(y_tol, 1e-6 * fscale)
        tang_tol = max(y_tol * 1000, 1e-3 * fscale)

        def _accept(r, tol):
            if r is None or not math.isfinite(r):
                return
            try:
                fr = float(func(r))
            except Exception:
                return
            if math.isfinite(fr) and abs(fr) <= tol:
                roots.append(r)

        for i in range(n - 1):
            v0, v1 = vals[i], vals[i + 1]
            if np.isnan(v0) or np.isnan(v1):
                continue
            a, b = x_samples[i], x_samples[i + 1]
            if v0 * v1 < 0:
                if abs(v1 - v0) > 1e6 * max(fscale, 1e-12):
                    continue
                _accept(self._refine_scalar_root(func, a, b, y_tol=y_tol), accept_tol)
            elif abs(v0) <= node_tol:
                _accept(self._refine_scalar_root(func, a, b, x0=a, y_tol=y_tol), accept_tol)
            elif abs(v1) <= node_tol:
                _accept(self._refine_scalar_root(func, a, b, x0=b, y_tol=y_tol), accept_tol)

        abs_vals = np.abs(vals)
        for i in range(1, n - 1):
            trio = abs_vals[i - 1:i + 2]
            if np.any(np.isnan(trio)):
                continue
            if abs_vals[i] <= abs_vals[i - 1] and abs_vals[i] <= abs_vals[i + 1] \
                    and abs_vals[i] < tang_tol:
                _accept(self._refine_scalar_root(
                    func, x_samples[i - 1], x_samples[i + 1],
                    x0=x_samples[i], y_tol=y_tol), tang_tol)

        roots = sorted(r for r in roots if math.isfinite(r))
        uniq = []
        for r in roots:
            if not uniq or abs(r - uniq[-1]) > dedup_tol:
                uniq.append(r)
        return uniq

    def _point_on_line_or_segment(self, x, y, line, tol=1e-4):
        p1, p2 = self.get_line_points(line)
        if not p1 or not p2:
            return False
        area = abs((p2.x - p1.x) * (y - p1.y) - (p2.y - p1.y) * (x - p1.x))
        den = math.dist((p1.x, p1.y), (p2.x, p2.y))
        if den == 0 or area / den > tol:
            return False
        return self.is_point_on_segment(x, y, p1, p2) if line.segment else True

    def _point_on_circle(self, x, y, circle, tol=1e-4):
        pd = self.get_points_dict()
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or cy is None or r is None:
            return False
        return abs(math.dist((x, y), (cx, cy)) - r) <= tol

    def _unique_points(self, pts, tol=1e-3):
        out = []
        for x, y in pts:
            x = 0.0 if abs(x) < 1e-3 else x
            y = 0.0 if abs(y) < 1e-3 else y
            merged = False
            for i, (ux, uy) in enumerate(out):
                if abs(x - ux) < tol and abs(y - uy) < tol:
                    out[i] = ((x + ux) / 2, (y + uy) / 2)
                    merged = True
                    break
            if not merged:
                out.append((x, y))
        return out

    def _snap_value(self, v, tol=1e-3):
        if abs(v - round(v)) < tol:
            return float(round(v))
        half = round(v * 2) / 2
        if abs(v - half) < tol:
            return float(half)
        return v

    def _snap_point(self, x, y, tol=1e-3):
        x = 0.0 if abs(x) < tol else self._snap_value(x, tol)
        y = 0.0 if abs(y) < tol else self._snap_value(y, tol)
        return x, y

    # ----- Gestione intersezioni (UI) -----
    def handle_intersection_pick(self, obj):
        if obj[0] not in ("point", "line", "circle", "function", "implicit"):
            self.set_status("Oggetto non supportato per l'intersezione")
            return
        self.selected_for_action.append(obj)
        if len(self.selected_for_action) > 2:
            self.selected_for_action = self.selected_for_action[-2:]
        if len(self.selected_for_action) == 1:
            name = getattr(obj[1], "name", str(obj[1]))
            self.set_status(f"Primo oggetto scelto: {name}. Scegli il secondo")
            return
        a, b = self.selected_for_action
        self.selected_for_action = []
        pts = self._unique_points(self.intersections_between(a, b), tol=1e-5)
        if not pts:
            self.graph.auto_back_to_move("Nessuna intersezione trovata")
            return
        created = 0
        for px, py in pts:
            if not any(abs(p.x - px) < 1e-5 and abs(p.y - py) < 1e-5 for p in self.points):
                self.create_point(round(px, 6), round(py, 6), color="brown")
                created += 1
        self.graph.auto_back_to_move(
            f"Trovate {len(pts)} intersezione/i. Punti creati: {created}")

    def intersections_between(self, obj1, obj2):
        t1, o1 = obj1
        t2, o2 = obj2
        key = frozenset((t1, t2)) if t1 != t2 else t1

        if t1 == "point" and t2 == "point":
            return [(o1.x, o1.y)] if abs(o1.x - o2.x) < 1e-9 and abs(o1.y - o2.y) < 1e-9 else []
        if t1 == "point" and t2 == "implicit":
            return [(o1.x, o1.y)] if self._point_on_implicit(o1, o2) else []
        if t1 == "implicit" and t2 == "point":
            return [(o2.x, o2.y)] if self._point_on_implicit(o2, o1) else []

        order = {"line": 0, "circle": 1, "function": 2, "implicit": 3}
        if t1 in order and t2 in order:
            (ta, oa), (tb, ob) = sorted([obj1, obj2], key=lambda o: order[o[0]])
            pair = (ta, tb)
            handlers = {
                ("line", "line"): lambda: self.line_line_intersections(oa, ob),
                ("line", "circle"): lambda: self.line_circle_intersections(oa, ob),
                ("line", "function"): lambda: self.function_line_intersections(ob, oa),
                ("line", "implicit"): lambda: self.implicit_line_intersections(ob, oa),
                ("circle", "circle"): lambda: self.circle_circle_intersections(oa, ob),
                ("circle", "function"): lambda: self.function_circle_intersections(ob, oa),
                ("circle", "implicit"): lambda: self.implicit_circle_intersections(ob, oa),
                ("function", "function"): lambda: self.function_function_intersections(oa, ob),
                ("function", "implicit"): lambda: self.implicit_function_intersections(ob, oa),
                ("implicit", "implicit"): lambda: self.implicit_implicit_intersections(oa, ob),
            }
            handler = handlers.get(pair)
            if handler:
                return handler()
        return []

    # ----- Eliminazione -----
    def _delete_line(self, line):
        p1, p2 = line.p1_name, line.p2_name
        self.lines = [l for l in self.lines if l is not line]
        removed = self._cleanup_orphans((p1, p2))
        return "Oggetto eliminato" + (f" con punti: {', '.join(removed)}" if removed else "")

    def _delete_circle(self, circle):
        if circle.center_name and circle.radius_point_name:
            pts = (circle.center_name, circle.radius_point_name)
            self.circles = [c for c in self.circles if c is not circle]
            removed = self._cleanup_orphans(pts)
            return "Cerchio eliminato" + (f" con punti: {', '.join(removed)}" if removed else "")
        self.circles = [c for c in self.circles if c is not circle]
        return "Cerchio da equazione eliminato"

    def _cleanup_orphans(self, point_names):
        removed = []
        for nm in point_names:
            if nm and not self.is_point_used_elsewhere(nm) and self.point_exists(nm):
                self.remove_point_by_name(nm)
                removed.append(nm)
        return removed

    def delete_selected(self):
        p = self._selected_point()
        if p is not None:
            name = p.name
            self.points = [q for q in self.points if q is not p]
            self.lines = [l for l in self.lines if name not in (l.p1_name, l.p2_name)]
            self.circles = [c for c in self.circles
                            if name not in (c.center_name, c.radius_point_name)]
            self.update_lists()
            self.graph.redraw()
            self.set_status("Punto eliminato")
            return

        sel = self._selected_object()
        if sel is None:
            self.set_status("Per eliminare scegli un solo elemento")
            return

        kind, obj = sel
        if kind == "line":
            msg = self._delete_line(obj)
        elif kind == "circle":
            msg = self._delete_circle(obj)
        elif kind == "function":
            self.functions = [f for f in self.functions if f is not obj]
            msg = "Funzione eliminata"
        else:
            self.implicits = [q for q in self.implicits if q is not obj]
            msg = "Curva implicita eliminata"
        self.update_lists()
        self.graph.redraw()
        self.set_status(msg)

    # ----- Input utente -----
    def _validate_function(self, expr):
        f = FunctionPlot("tmp", expr)
        for sample in (0.37, 1.7, -2.3, 5.0):
            try:
                val = float(f.evaluate(sample))
                return
            except (NameError, TypeError, SyntaxError):
                raise ValueError("Espressione non valida per una funzione y = f(x)")
            except Exception:
                continue
        return

    def _validate_implicit(self, equation):
        imp = ImplicitPlot("tmp", equation)
        for sx, sy in ((0.5, 0.5), (1.3, -0.7), (-2.0, 2.0)):
            try:
                float(imp.evaluate(sx, sy))
                return
            except (NameError, TypeError, SyntaxError):
                raise ValueError("Equazione non valida")
            except Exception:
                continue
        return

    def process_input(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        try:
            raw = ExpressionHelper.preprocess(text)
            low = raw.lower()

            point = ExpressionHelper.parse_point(raw)
            if point:
                self.create_point(point[1], point[2], point[0])
                self._clear_input("Punto aggiunto")
                return

            if low.startswith("line(") or low.startswith("retta("):
                inside = raw[raw.find("(") + 1:raw.rfind(")")]
                parts = [p.strip() for p in inside.split(",")]
                if len(parts) != 2:
                    raise ValueError("Formato: line(P1,P2)")
                if not (self.get_point_by_name(parts[0]) and self.get_point_by_name(parts[1])):
                    raise ValueError("Uno o entrambi i punti non esistono")
                self.create_line_from_names(parts[0], parts[1])
                self._clear_input("Retta aggiunta")
                return

            if low.startswith("circle("):
                inside = raw[raw.find("(") + 1:raw.rfind(")")]
                parts = [p.strip() for p in inside.split(",")]
                if len(parts) != 3:
                    raise ValueError("Formato: circle(cx,cy,r)")
                cx, cy, r = float(parts[0]), float(parts[1]), float(parts[2])
                if r <= 0:
                    raise ValueError("Raggio positivo richiesto")
                self._add_equation_circle(cx, cy, r,
                                          f"(x-{self._fmt_num(cx)})^2+(y-{self._fmt_num(cy)})^2={self._fmt_num(r*r)}")
                self._clear_input(f"Cerchio aggiunto (centro ({cx},{cy}), raggio {r})")
                return

            if low.startswith("y="):
                body = raw[2:]
                expr = ExpressionHelper.normalize(body)
                self._validate_function(expr)
                self.function_counter += 1
                self.functions.append(FunctionPlot(
                    f"f{self.function_counter}", expr, color=self._random_color(),
                    display=ExpressionHelper.to_display(body)))
                self.update_lists(); self.graph.redraw()
                self._clear_input("Funzione aggiunta")
                return

            if "=" in raw:
                circle_data = self.parse_circle_explicit(raw)
                if circle_data:
                    (h, k, r), display = circle_data
                    display = ExpressionHelper.to_display(display)
                    self._add_equation_circle(h, k, r, display)
                    self._clear_input(f"Cerchio aggiunto: {display}")
                    return
                eq = ExpressionHelper.split_equation(raw)
                if eq:
                    self._validate_implicit(eq)
                    label = "ellisse" if ("x^2/" in low and "y^2/" in low) else "equazione"
                    self.implicit_counter += 1
                    self.implicits.append(ImplicitPlot(
                        f"eq{self.implicit_counter}", eq, label=label,
                        color=self._random_color(), display=ExpressionHelper.to_display(raw)))
                    self.update_lists(); self.graph.redraw()
                    self._clear_input(label.capitalize() + " aggiunta")
                    return

            expr = ExpressionHelper.normalize(raw)
            self._validate_function(expr)
            self.function_counter += 1
            self.functions.append(FunctionPlot(
                f"f{self.function_counter}", expr, color=self._random_color(),
                display=ExpressionHelper.to_display(raw)))
            self.update_lists(); self.graph.redraw()
            self._clear_input("Funzione aggiunta")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def _add_equation_circle(self, cx, cy, r, display):
        self.circle_counter += 1
        self.circles.append(Circle(f"c{self.circle_counter}", cx=cx, cy=cy, radius=r,
                                   color=self._random_color(), display_name=display))
        self.update_lists()
        self.graph.redraw()

    def _clear_input(self, status):
        self.input_entry.delete(0, tk.END)
        self.set_status(status)

    def _prettify_entry(self, entry, event=None):
        if event is not None and event.keysym in (
                "Left", "Right", "Up", "Down", "Home", "End",
                "Return", "Tab", "Escape", "Control_L", "Control_R",
                "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
            return
        text = entry.get()
        if not text:
            return
        pretty = ExpressionHelper.to_pretty(text)
        if pretty == text:
            return
        try:
            cursor = entry.index(tk.INSERT)
            prefix_len = len(ExpressionHelper.to_pretty(text[:cursor]))
        except Exception:
            prefix_len = len(pretty)
        entry.delete(0, tk.END)
        entry.insert(0, pretty)
        entry.icursor(min(prefix_len, len(pretty)))

    # ----- Tastiera -----
    def _on_key(self, event):
        focused = self.root.focus_get()
        if isinstance(focused, tk.Entry):
            return
        key_map = {
            "m": "move",
            "p": "new_point",
            "s": "new_segment",
            "r": "new_line",
            "c": "new_circle",
            "i": "intersection",
            "d": "distance",
        }
        mode = key_map.get(event.keysym.lower())
        if mode:
            self.start_action_mode(mode)

    # ----- Distanza -----
    def handle_distance_pick(self, obj):
        self.selected_for_action.append(obj)
        if len(self.selected_for_action) > 2:
            self.selected_for_action = self.selected_for_action[-2:]
        if len(self.selected_for_action) == 1:
            name = getattr(obj[1], "name", str(obj[1]))
            self.set_status(f"Primo oggetto: {name}. Scegli il secondo")
            return
        a, b = self.selected_for_action
        self.selected_for_action = []
        d = self.distance_between(a, b)
        na = getattr(a[1], "name", "?")
        nb = getattr(b[1], "name", "?")
        if d is None:
            self.graph.auto_back_to_move(
                f"Coppia {na}/{nb} non supportata per la distanza")
            return
        self.graph.auto_back_to_move(
            f"Distanza {na} ↔ {nb} = {self._fmt_num(round(d, 4))}")

    _LINE_KINDS = ("line", "function", "implicit")

    def distance_between(self, obj1, obj2):
        t1, o1 = obj1
        t2, o2 = obj2
        pd = self.get_points_dict()

        if t1 == "point" and t2 == "point":
            return math.dist((o1.x, o1.y), (o2.x, o2.y))

        if t2 == "point" and t1 != "point":
            t1, o1, t2, o2 = t2, o2, t1, o1

        if t1 == "point" and t2 == "circle":
            return self._point_circle_distance(o1, o2, pd)
        if t1 == "point" and t2 == "line":
            return self._point_line_distance(o1, o2, pd)
        if t1 == "point" and t2 in ("function", "implicit"):
            coeffs = self._line_like_coeffs(t2, o2, pd)
            if coeffs is None:
                return None
            a, b, c = coeffs
            return abs(a * o1.x + b * o1.y + c)

        if t1 == "circle" and t2 == "circle":
            return self._circle_circle_distance(o1, o2, pd)
        if t1 == "circle" and t2 in self._LINE_KINDS:
            return self._circle_line_distance(o1, o2, t2, pd)
        if t2 == "circle" and t1 in self._LINE_KINDS:
            return self._circle_line_distance(o2, o1, t1, pd)

        if t1 in self._LINE_KINDS and t2 in self._LINE_KINDS:
            return self._line_like_distance(t1, o1, t2, o2, pd)

        return None

    # ----- Helper: coefficienti retta -----
    def _affine_coeffs(self, F):
        try:
            f00 = float(F(0.0, 0.0))
            f10 = float(F(1.0, 0.0))
            f01 = float(F(0.0, 1.0))
            if not all(math.isfinite(v) for v in (f00, f10, f01)):
                return None
            A, B, C = f10 - f00, f01 - f00, f00
            if A == 0 and B == 0:
                return None
            for x, y in ((2.3, -1.7), (-0.9, 3.1), (5.0, 5.0), (-4.2, -2.6)):
                act = float(F(x, y))
                if not math.isfinite(act):
                    return None
                pred = A * x + B * y + C
                if abs(pred - act) > 1e-7 * (1.0 + abs(pred) + abs(act)):
                    return None
            return A, B, C
        except Exception:
            return None

    def _line_like_coeffs(self, kind, obj, pd):
        if kind == "line":
            p1, p2 = pd.get(obj.p1_name), pd.get(obj.p2_name)
            if not p1 or not p2:
                return None
            dx, dy = p2.x - p1.x, p2.y - p1.y
            if math.hypot(dx, dy) == 0:
                return None
            a, b, c = dy, -dx, -(dy * p1.x - dx * p1.y)
        elif kind == "function":
            co = self._affine_coeffs(lambda x, y: float(obj.evaluate(x)) - y)
            if co is None:
                return None
            a, b, c = co
        elif kind == "implicit":
            co = self._affine_coeffs(lambda x, y: float(obj.evaluate(x, y)))
            if co is None:
                return None
            a, b, c = co
        else:
            return None
        n = math.hypot(a, b)
        if n == 0:
            return None
        return a / n, b / n, c / n

    def _line_like_distance(self, t1, o1, t2, o2, pd):
        L1 = self._line_like_coeffs(t1, o1, pd)
        L2 = self._line_like_coeffs(t2, o2, pd)
        if L1 is None or L2 is None:
            return None
        a1, b1, c1 = L1
        a2, b2, c2 = L2
        if abs(a1 * b2 - a2 * b1) > 1e-9:
            return 0.0
        if a1 * a2 + b1 * b2 < 0:
            a2, b2, c2 = -a2, -b2, -c2
        return abs(c1 - c2)

    def _circle_line_distance(self, circle, line_obj, line_kind, pd):
        L = self._line_like_coeffs(line_kind, line_obj, pd)
        if L is None:
            return None
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or cy is None or r is None:
            return None
        a, b, c = L
        d = abs(a * cx + b * cy + c)
        return d - r if d > r else 0.0

    def _point_line_distance(self, point, line, pd):
        p1, p2 = pd.get(line.p1_name), pd.get(line.p2_name)
        if not p1 or not p2:
            return None
        dx, dy = p2.x - p1.x, p2.y - p1.y
        length = math.hypot(dx, dy)
        if length == 0:
            return math.dist((point.x, point.y), (p1.x, p1.y))
        if line.segment:
            t = ((point.x - p1.x) * dx + (point.y - p1.y) * dy) / (length * length)
            if t < 0:
                return math.dist((point.x, point.y), (p1.x, p1.y))
            if t > 1:
                return math.dist((point.x, point.y), (p2.x, p2.y))
        return abs((point.x - p1.x) * dy - (point.y - p1.y) * dx) / length

    def _point_circle_distance(self, point, circle, pd):
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or r is None:
            return None
        return abs(math.dist((point.x, point.y), (cx, cy)) - r)

    def _circle_circle_distance(self, c1, c2, pd):
        cx1, cy1 = c1.get_center(pd)
        cx2, cy2 = c2.get_center(pd)
        r1, r2 = c1.get_radius(pd), c2.get_radius(pd)
        if None in (cx1, cy1, cx2, cy2, r1, r2):
            return None
        d = math.dist((cx1, cy1), (cx2, cy2))
        if d >= r1 + r2:
            return d - r1 - r2
        if d <= abs(r1 - r2):
            return abs(r1 - r2) - d
        return 0.0

    # ----- Calcolatrice -----
    def run_calculator(self):
        expr = self.calc_entry.get().strip()
        if not expr:
            return
        safe = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "sqrt": math.sqrt, "log": math.log, "ln": math.log,
            "log10": math.log10, "exp": math.exp,
            "pi": math.pi, "e": math.e, "abs": abs,
        }
        try:
            norm = ExpressionHelper.normalize(expr)
            code = compile(norm, "<calc>", "eval")
            result = eval(code, {"__builtins__": {}}, safe)
            self.calc_result.config(text="Risultato: " + str(result))
            self.set_status("Calcolo eseguito")
        except ZeroDivisionError:
            self.calc_result.config(text="Errore: divisione per zero")
        except Exception as e:
            self.calc_result.config(text=f"Errore: {e}")