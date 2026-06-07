import re

class ExpressionHelper:
    _KNOWN_FUNCS = ("sin", "cos", "tan", "asin", "acos", "atan",
                    "sqrt", "log10", "log2", "log", "ln", "exp", "abs")

    @staticmethod
    def to_pretty(text):
        return text.replace("sqrt", "√")

    # ----- preprocess -----
    @staticmethod
    def preprocess(text):
        text = text.strip().replace(" ", "")
        text = (text.replace("√", "sqrt")
                    .replace("·", "*")
                    .replace("×", "*"))
        return text

    # ----- logaritmi in base qualsiasi -----
    @staticmethod
    def _expand_log_bases(expr):
        pat = re.compile(r"log(\d+(?:\.\d+)?)\(")
        while True:
            m = pat.search(expr)
            if not m:
                return expr
            base = m.group(1)
            open_idx = m.end() - 1
            depth, j = 0, open_idx
            while j < len(expr):
                if expr[j] == "(":
                    depth += 1
                elif expr[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= len(expr):
                return expr
            arg = expr[open_idx + 1:j]
            expr = expr[:m.start()] + f"(log({arg})/log({base}))" + expr[j + 1:]

    # ----- normalize -----
    @staticmethod
    def normalize(expr):
        expr = ExpressionHelper.preprocess(expr)
        expr = expr.replace("^", "**")
        expr = ExpressionHelper._expand_log_bases(expr)
        expr = re.sub(r"sqrt(?!\()(\d+(?:\.\d+)?|[A-Za-z])", r"sqrt(\1)", expr)
        expr = re.sub(r"(\d)([A-Za-z(])", r"\1*\2", expr)
        expr = re.sub(r"(\))([A-Za-z0-9(])", r"\1*\2", expr)
        expr = re.sub(r"([xy])([xy])", r"\1*\2", expr)
        for fn in ExpressionHelper._KNOWN_FUNCS:
            expr = expr.replace(fn + "*(", fn + "(")
        return expr

    @staticmethod
    def to_display(text):
        return ExpressionHelper.to_pretty(ExpressionHelper.preprocess(text))

    # ----- punti -----
    @staticmethod
    def parse_point(text):
        raw = ExpressionHelper.preprocess(text)
        num = r"-?\d+(?:\.\d+)?"
        m = re.match(rf"^([A-Za-z]\w*)=?\(({num}),({num})\)$", raw)
        if m:
            return m.group(1), float(m.group(2)), float(m.group(3))
        return None

    @staticmethod
    def split_equation(text):
        if "=" not in text:
            return None
        a, b = text.split("=", 1)
        if a == "" or b == "":
            return None
        return f"({ExpressionHelper.normalize(a)})-({ExpressionHelper.normalize(b)})"