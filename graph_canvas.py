import math
import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GraphCanvas:
    SELECTION_PIXEL_TOL = 10

    MODE_NAMES = {
        "move": "Muovi",
        "new_point": "Nuovo punto",
        "new_segment": "Nuovo segmento",
        "new_line": "Nuova retta",
        "new_circle": "Nuovo cerchio",
        "midpoint": "Punto medio",
        "intersection": "Intersezione",
        "distance": "Distanza",
    }

    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg="#cfcfcf", bd=1, relief="sunken")
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.xlim = [-10.0, 10.0]
        self.ylim = [-10.0, 10.0]
        self.mode = "move"

        self._panning = False
        self._last_pixel = None
        self.temp_name = None

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.redraw()

    # ----- Coordinate -----
    def world_to_pixel(self, x, y):
        return self.ax.transData.transform((x, y))

    def pixel_to_world(self, px, py):
        return self.ax.transData.inverted().transform((px, py))

    def pixel_distance(self, x1, y1, x2, y2):
        px1, py1 = self.world_to_pixel(x1, y1)
        px2, py2 = self.world_to_pixel(x2, y2)
        return math.hypot(px1 - px2, py1 - py2)

    def get_view_size_pixels(self):
        bbox = self.ax.get_window_extent()
        return max(1, int(bbox.width)), max(1, int(bbox.height))

    def function_sample_count(self):
        width, _ = self.get_view_size_pixels()
        return int(min(12000, max(1800, width * 4)))

    def implicit_grid_size(self):
        width, height = self.get_view_size_pixels()
        nx = int(min(900, max(220, width * 0.75)))
        ny = int(min(900, max(220, height * 0.75)))
        return nx, ny

    # ----- Modalità -----
    def set_mode(self, mode):
        self.mode = mode
        self.temp_name = None
        self.app.selected_for_action = []
        self.app.update_mode_buttons()
        self.app.set_status("Modalità attiva: " + self.MODE_NAMES.get(mode, mode))

    def auto_back_to_move(self, msg="Operazione completata. Modalità tornata a Muovi"):
        self.set_mode("move")
        self.app.set_status(msg)

    def reset_view(self):
        self.xlim = [-10.0, 10.0]
        self.ylim = [-10.0, 10.0]
        self.redraw()

    # ----- Disegno -----
    def draw_label(self, x, y, text, color):
        self.ax.text(
            x, y, text, fontsize=8, color=color,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.6, pad=1),
        )

    def redraw(self):
        self.ax.clear()
        self.ax.set_facecolor("white")
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True, color="#d0d0d0", linewidth=0.6)
        self.ax.axhline(0, color="black", linewidth=1)
        self.ax.axvline(0, color="black", linewidth=1)
        self.ax.set_title("Grafix", fontsize=11)

        pd = self.app.get_points_dict()
        for f in self.app.functions:
            self.draw_function(f)
        for imp in self.app.implicits:
            self.draw_implicit(imp)
        for line in self.app.lines:
            self.draw_line(line, pd)
        for circle in self.app.circles:
            self.draw_circle(circle, pd)
        for p in self.app.points:
            self.ax.plot(p.x, p.y, "o", color=p.color, markersize=7)
            self.draw_label(p.x + 0.15, p.y + 0.15, p.name, "black")
        self.canvas.draw_idle()

    def draw_function(self, f):
        xs = np.linspace(self.xlim[0], self.xlim[1], self.function_sample_count())
        try:
            with np.errstate(all="ignore"):
                ys = np.asarray(f.evaluate(xs), dtype=float)
            if ys.shape == ():
                ys = np.full_like(xs, float(ys))
            ys[~np.isfinite(ys)] = np.nan
            span = max(abs(self.ylim[0]), abs(self.ylim[1]), 1.0)
            ys[np.abs(ys) > span * 8] = np.nan
            self.ax.plot(xs, ys, color=f.color, linewidth=1.8)
            finite = np.where(np.isfinite(ys))[0]
            if len(finite):
                mid = finite[len(finite) // 2]
                self.draw_label(xs[mid], ys[mid], f.name, f.color)
        except Exception:
            pass

    def draw_implicit(self, imp):
        try:
            nx, ny = self.implicit_grid_size()
            xs = np.linspace(self.xlim[0], self.xlim[1], nx)
            ys = np.linspace(self.ylim[0], self.ylim[1], ny)
            X, Y = np.meshgrid(xs, ys)
            with np.errstate(all="ignore"):
                Z = np.asarray(imp.evaluate(X, Y), dtype=float)
            Z[~np.isfinite(Z)] = np.nan
            self.ax.contour(X, Y, Z, levels=[0], colors=[imp.color], linewidths=1.7)
            self.draw_label(self.xlim[0] + 0.5, self.ylim[1] - 0.8, imp.name, imp.color)
        except Exception:
            pass

    def draw_line(self, line, pd):
        p1 = pd.get(line.p1_name)
        p2 = pd.get(line.p2_name)
        if not p1 or not p2:
            return
        if line.segment:
            self.ax.plot([p1.x, p2.x], [p1.y, p2.y], color=line.color, linewidth=1.8)
            self.draw_label((p1.x + p2.x) / 2, (p1.y + p2.y) / 2, line.name, line.color)
        else:
            if abs(p1.x - p2.x) < 1e-9:
                xs = [p1.x, p1.x]
                ys = [self.ylim[0], self.ylim[1]]
                lx, ly = p1.x + 0.15, self.ylim[1] - 0.7
            else:
                m = (p2.y - p1.y) / (p2.x - p1.x)
                q = p1.y - m * p1.x
                xs = np.array([self.xlim[0], self.xlim[1]])
                ys = m * xs + q
                lx, ly = 0, q
            self.ax.plot(xs, ys, color=line.color, linewidth=1.8)
            self.draw_label(lx, ly, line.name, line.color)

    def draw_circle(self, circle, pd):
        cx, cy = circle.get_center(pd)
        r = circle.get_radius(pd)
        if cx is None or cy is None or r is None or r <= 0:
            return
        t = np.linspace(0, 2 * np.pi, 500)
        self.ax.plot(cx + r * np.cos(t), cy + r * np.sin(t),
                     color=circle.color, linewidth=1.8)
        self.draw_label(cx + r / math.sqrt(2), cy + r / math.sqrt(2),
                        circle.name, circle.color)

    # ----- Eventi mouse -----
    def on_scroll(self, event):
        factor = 0.85 if event.button == "up" else 1.18
        if event.xdata is not None and event.ydata is not None:
            ax_, ay_ = event.xdata, event.ydata
        else:
            ax_ = (self.xlim[0] + self.xlim[1]) / 2
            ay_ = (self.ylim[0] + self.ylim[1]) / 2
        self.xlim = [ax_ + (self.xlim[0] - ax_) * factor,
                     ax_ + (self.xlim[1] - ax_) * factor]
        self.ylim = [ay_ + (self.ylim[0] - ay_) * factor,
                     ay_ + (self.ylim[1] - ay_) * factor]
        self.redraw()

    def on_press(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x_w, y_w = event.xdata, event.ydata
        near_point = self.find_near_point(x_w, y_w)

        if self.mode == "move":
            self._panning = True
            self._last_pixel = (event.x, event.y)
            return

        if self.mode == "new_point":
            self.app.create_point(round(x_w, 2), round(y_w, 2))
            self.auto_back_to_move()
            return

        if self.mode in ("new_segment", "new_line", "new_circle"):
            if near_point is None:
                p = self.app.create_point(round(x_w, 2), round(y_w, 2), return_point=True)
                near_point = ("point", p)
            if self.temp_name is None:
                self.temp_name = near_point[1].name
                self.app.set_status(
                    f"Primo punto scelto: {near_point[1].name}. Ora clicca il secondo punto")
                return
            p1, p2 = self.temp_name, near_point[1].name
            self.temp_name = None
            if p1 == p2:
                self.app.set_status("Scegli un secondo punto diverso")
                return
            if self.mode == "new_segment":
                self.app.create_segment_from_names(p1, p2)
            elif self.mode == "new_line":
                self.app.create_line_from_names(p1, p2)
            else:
                self.app.create_circle_from_names(p1, p2)
            self.auto_back_to_move()
            return

        if self.mode == "midpoint":
            obj = self.find_near_line_only(x_w, y_w)
            if obj is None or not obj[1].segment:
                self.app.set_status("Clicca proprio sopra un segmento")
                return
            self.app.create_midpoint_from_segment(obj[1])
            self.auto_back_to_move()
            return

        if self.mode == "intersection":
            self._handle_intersection_click(event, x_w, y_w)
            return

        if self.mode == "distance":
            self._handle_distance_click(event, x_w, y_w)
            return

    def _handle_intersection_click(self, event, x_w, y_w):
        all_near = self.find_all_near_objects(x_w, y_w)
        if not all_near:
            self.app.set_status("Nessun oggetto trovato sotto il clic")
            return

        if self.app.selected_for_action:
            ft, fo = self.app.selected_for_action[0]
            all_near = [o for o in all_near if not (o[1] is fo and o[0] == ft)]
            if not all_near:
                self.app.set_status("Scegli un oggetto diverso dal primo")
                return

        if len(all_near) == 1:
            self.app.handle_intersection_pick(all_near[0])
            return

        menu = tk.Menu(self.canvas.get_tk_widget(), tearoff=0)
        for typ, obj in all_near:
            name = getattr(obj, "name", str(obj))
            menu.add_command(
                label=f"{typ}: {name}",
                command=lambda t=typ, o=obj: self.app.handle_intersection_pick((t, o)),
            )
        menu.post(*self._event_screen_xy(event))

    def _event_screen_xy(self, event):
        gui = getattr(event, "guiEvent", None)
        if gui is not None and hasattr(gui, "x_root") and hasattr(gui, "y_root"):
            return gui.x_root, gui.y_root
        widget = self.canvas.get_tk_widget()
        ex = event.x if event.x is not None else 0
        ey = event.y if event.y is not None else 0
        height = widget.winfo_height()
        return (widget.winfo_rootx() + int(ex),
                widget.winfo_rooty() + int(height - ey))

    def _handle_distance_click(self, event, x_w, y_w):
        all_near = self.find_all_near_objects(x_w, y_w)
        if not all_near:
            self.app.set_status("Nessun oggetto trovato sotto il clic")
            return
        if self.app.selected_for_action:
            ft, fo = self.app.selected_for_action[0]
            all_near = [o for o in all_near if not (o[1] is fo and o[0] == ft)]
            if not all_near:
                self.app.set_status("Scegli un oggetto diverso dal primo")
                return
        if len(all_near) == 1:
            self.app.handle_distance_pick(all_near[0])
            return
        menu = tk.Menu(self.canvas.get_tk_widget(), tearoff=0)
        for typ, obj in all_near:
            name = getattr(obj, "name", str(obj))
            menu.add_command(
                label=f"{typ}: {name}",
                command=lambda t=typ, o=obj: self.app.handle_distance_pick((t, o)),
            )
        menu.post(*self._event_screen_xy(event))

    def on_motion(self, event):
        if not self._panning or self.mode != "move":
            return
        if event.x is None or event.y is None or self._last_pixel is None:
            return
        x0, y0 = self.pixel_to_world(*self._last_pixel)
        x1, y1 = self.pixel_to_world(event.x, event.y)
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            return
        self.xlim = [self.xlim[0] - dx, self.xlim[1] - dx]
        self.ylim = [self.ylim[0] - dy, self.ylim[1] - dy]
        self._last_pixel = (event.x, event.y)
        self.redraw()

    def on_release(self, event):
        self._panning = False
        self._last_pixel = None

    # ----- Selezione oggetti -----
    def find_near_point(self, x_w, y_w):
        best, best_d = None, self.SELECTION_PIXEL_TOL + 1
        for p in self.app.points:
            d = self.pixel_distance(x_w, y_w, p.x, p.y)
            if d < best_d:
                best_d, best = d, p
        return ("point", best) if best and best_d <= self.SELECTION_PIXEL_TOL else None

    def _point_segment_pixel_dist(self, x_w, y_w, p1, p2, clamp=True):
        p1x, p1y = self.world_to_pixel(p1.x, p1.y)
        p2x, p2y = self.world_to_pixel(p2.x, p2.y)
        px, py = self.world_to_pixel(x_w, y_w)
        dx, dy = p2x - p1x, p2y - p1y
        if dx == 0 and dy == 0:
            return math.hypot(px - p1x, py - p1y)
        t = ((px - p1x) * dx + (py - p1y) * dy) / (dx * dx + dy * dy)
        if clamp:
            t = max(0.0, min(1.0, t))
        return math.hypot(px - (p1x + t * dx), py - (p1y + t * dy))

    def find_near_line_only(self, x_w, y_w):
        best, best_d = None, self.SELECTION_PIXEL_TOL + 1
        pd = self.app.get_points_dict()
        for line in self.app.lines:
            p1, p2 = pd.get(line.p1_name), pd.get(line.p2_name)
            if not p1 or not p2:
                continue
            d = self._point_segment_pixel_dist(x_w, y_w, p1, p2, clamp=line.segment)
            if d < best_d:
                best_d, best = d, line
        return ("line", best) if best and best_d <= self.SELECTION_PIXEL_TOL else None

    def _circle_edge_pixel_dist(self, x_w, y_w, cx, cy, r):
        center_px = np.array(self.world_to_pixel(cx, cy))
        click_px = np.array(self.world_to_pixel(x_w, y_w))
        edge_px = np.array(self.world_to_pixel(cx + r, cy))
        radius_px = np.hypot(*(edge_px - center_px))
        dist_px = np.hypot(*(click_px - center_px))
        return abs(dist_px - radius_px)

    def find_near_circle_only(self, x_w, y_w):
        best, best_d = None, self.SELECTION_PIXEL_TOL + 1
        pd = self.app.get_points_dict()
        for circle in self.app.circles:
            cx, cy = circle.get_center(pd)
            r = circle.get_radius(pd)
            if cx is None or cy is None or r is None:
                continue
            d = self._circle_edge_pixel_dist(x_w, y_w, cx, cy, r)
            if d < best_d:
                best_d, best = d, circle
        return ("circle", best) if best and best_d <= self.SELECTION_PIXEL_TOL else None

    def find_near_function_only(self, x_w, y_w):
        best, best_d = None, self.SELECTION_PIXEL_TOL + 1
        click_px = np.array(self.world_to_pixel(x_w, y_w))
        xs = np.linspace(self.xlim[0], self.xlim[1], 500)
        for f in self.app.functions:
            try:
                with np.errstate(all="ignore"):
                    ys = np.asarray(f.evaluate(xs), dtype=float)
                if ys.shape == ():
                    ys = np.full_like(xs, float(ys))
            except Exception:
                continue
            for xi, yi in zip(xs, ys):
                if not np.isfinite(yi) or yi < self.ylim[0] or yi > self.ylim[1]:
                    continue
                px = np.array(self.world_to_pixel(xi, yi))
                d = np.hypot(*(click_px - px))
                if d < best_d:
                    best_d, best = d, f
        return ("function", best) if best and best_d <= self.SELECTION_PIXEL_TOL else None

    def find_near_implicit_only(self, x_w, y_w):
        best, best_d = None, self.SELECTION_PIXEL_TOL + 1
        nx, ny = 80, 80
        xs = np.linspace(self.xlim[0], self.xlim[1], nx)
        ys = np.linspace(self.ylim[0], self.ylim[1], ny)
        X, Y = np.meshgrid(xs, ys)
        for imp in self.app.implicits:
            try:
                with np.errstate(all="ignore"):
                    Z = np.asarray(imp.evaluate(X, Y), dtype=float)
            except Exception:
                continue
            cells = self._straddle_cells(Z)
            jj, ii = np.where(cells)
            for j, i in zip(jj, ii):
                xc = (xs[i] + xs[i + 1]) / 2
                yc = (ys[j] + ys[j + 1]) / 2
                d = self.pixel_distance(x_w, y_w, xc, yc)
                if d < best_d:
                    best_d, best = d, imp
        return ("implicit", best) if best and best_d <= self.SELECTION_PIXEL_TOL else None

    @staticmethod
    def _straddle_cells(Z):
        a, b = Z[:-1, :-1], Z[:-1, 1:]
        c, d = Z[1:, :-1], Z[1:, 1:]
        stack = np.stack([a, b, c, d])
        valid = np.all(np.isfinite(stack), axis=0)
        with np.errstate(invalid="ignore"):
            mn = np.min(stack, axis=0)
            mx = np.max(stack, axis=0)
        return valid & (mn <= 0) & (mx >= 0)

    def find_all_near_objects(self, x_w, y_w):
        candidates = []
        for finder in (self.find_near_point, self.find_near_line_only,
                       self.find_near_circle_only, self.find_near_function_only,
                       self.find_near_implicit_only):
            res = finder(x_w, y_w)
            if res:
                candidates.append(res)
        seen, unique = set(), []
        for typ, obj in candidates:
            if id(obj) not in seen:
                seen.add(id(obj))
                unique.append((typ, obj))
        return unique