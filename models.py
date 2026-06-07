import math
import numpy as np

# ----- Ambiente sicuro per le espressioni -----
_SAFE_FUNCS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "sqrt": np.sqrt,
    "log": np.log,
    "ln": np.log,
    "log10": np.log10,
    "exp": np.exp,
    "abs": np.abs,
    "pi": np.pi,
    "e": np.e,
}

# ----- Point -----
class Point:
    def __init__(self, name, x, y, color="red"):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.color = color

# ----- Line -----
class Line:
    def __init__(self, name, p1_name, p2_name, color="blue", segment=False):
        self.name = name
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.color = color
        self.segment = segment

# ----- Circle -----
class Circle:
    def __init__(self, name, center_name=None, radius_point_name=None, color="green",
                 cx=None, cy=None, radius=None, display_name=None):
        self.name = name
        self.center_name = center_name
        self.radius_point_name = radius_point_name
        self.color = color
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.display_name = display_name

    @property
    def from_equation(self):
        return self.cx is not None and self.cy is not None and self.radius is not None

    def get_center(self, points_dict):
        if self.cx is not None and self.cy is not None:
            return self.cx, self.cy
        if self.center_name:
            p = points_dict.get(self.center_name)
            if p:
                return p.x, p.y
        return None, None

    def get_radius(self, points_dict):
        if self.radius is not None:
            return self.radius
        c = points_dict.get(self.center_name)
        r = points_dict.get(self.radius_point_name)
        if c and r:
            return math.dist((c.x, c.y), (r.x, r.y))
        return None

# ----- FunctionPlot -----
class FunctionPlot:
    def __init__(self, name, expression, color="purple", display=None):
        self.name = name
        self.expression = expression
        self.display = display or expression
        self.color = color
        self._code = compile(expression, "<function>", "eval")
        self._env = dict(_SAFE_FUNCS)

    def evaluate(self, x):
        self._env["x"] = x
        return eval(self._code, {"__builtins__": {}}, self._env)

# ----- ImplicitPlot -----
class ImplicitPlot:
    def __init__(self, name, equation, color="darkgreen", label="equazione", display=None):
        self.name = name
        self.equation = equation
        self.display = display or equation
        self.color = color
        self.label = label
        self._code = compile(equation, "<implicit>", "eval")
        self._env = dict(_SAFE_FUNCS)

    def evaluate(self, x, y):
        self._env["x"] = x
        self._env["y"] = y
        return eval(self._code, {"__builtins__": {}}, self._env)