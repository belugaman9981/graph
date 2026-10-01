"""XY Grapher. Install: py -m pip install numpy matplotlib
Run: py xy_grapher.py
Enter one equation per line, then click Graph or press Ctrl+Enter.
"""

import ast
import re
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


FUNCTIONS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "sqrt": np.sqrt, "abs": np.abs, "exp": np.exp,
    "log": np.log, "ln": np.log, "log10": np.log10,
}
CONSTANTS = {"pi": np.pi, "e": np.e}
COLORS = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c", "#0891b2"]
TOKEN = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|[a-z]+|\*\*|[+\-*/()]")


def parse_expression(text):
    """Parse a limited math language without executing user input as Python."""
    text = text.lower().replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-")
    text = re.sub(r"\s+", "", text)
    tokens = TOKEN.findall(text)
    if not tokens or "".join(tokens) != text:
        raise ValueError("Use numbers, x, y, +, -, *, /, ^, parentheses and supported functions.")
    expanded = []
    for token in tokens:
        # Permit 2x, 2(x+1), x(y+1), (x+1)(x-1), and 2sin(x).
        if expanded:
            previous = expanded[-1]
            ends_value = previous == ")" or previous in {"x", "y", *CONSTANTS} or previous[0].isdigit() or previous[0] == "."
            starts_value = token == "(" or token[0].isalpha() or token[0].isdigit() or token[0] == "."
            if ends_value and starts_value:
                expanded.append("*")
        expanded.append(token)
    try:
        tree = ast.parse("".join(expanded), mode="eval").body
    except SyntaxError as error:
        raise ValueError("Check your operators and parentheses.") from error

    def validate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if not np.isfinite(float(node.value)) or abs(node.value) > 1e100:
                raise ValueError("That number is too large.")
        elif isinstance(node, ast.Name) and node.id in {"x", "y", *CONSTANTS}:
            pass
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            validate(node.left)
            validate(node.right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            validate(node.operand)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords:
            validate(node.args[0])
        else:
            raise ValueError("Unknown name or operation. Functions: " + ", ".join(FUNCTIONS))

    validate(tree)
    return tree


def evaluate(node, x, y):
    if isinstance(node, ast.Constant):
        return np.float64(node.value)
    if isinstance(node, ast.Name):
        return {"x": x, "y": y, **CONSTANTS}[node.id]
    if isinstance(node, ast.UnaryOp):
        value = evaluate(node.operand, x, y)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Call):
        return FUNCTIONS[node.func.id](evaluate(node.args[0], x, y))
    left, right = evaluate(node.left, x, y), evaluate(node.right, x, y)
    operations = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply,
                  ast.Div: np.divide, ast.Pow: np.power}
    return operations[type(node.op)](left, right)


def variables(node):
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name) and item.id in {"x", "y"}}


def parse_equation(text):
    if len(text) > 300:
        raise ValueError("Keep each equation under 300 characters.")
    if "=" not in text:
        text = "y=" + text
    if text.count("=") != 1:
        raise ValueError("Use one equals sign per equation.")
    left, right = (parse_expression(part) for part in text.split("="))
    if not (variables(left) | variables(right)):
        raise ValueError("An equation needs x or y.")
    for isolated, other in ((left, right), (right, left)):
        if isinstance(isolated, ast.Name) and isolated.id in {"x", "y"} and isolated.id not in variables(other):
            return isolated.id, other, None
    return "implicit", left, right


def draw_equation(ax, equation, bounds, color):
    kind, left, right = parse_equation(equation)
    xmin, xmax, ymin, ymax = bounds
    with np.errstate(all="ignore"):
        if kind in {"x", "y"}:
            t = np.linspace(xmin if kind == "y" else ymin, xmax if kind == "y" else ymax, 4001)
            values = evaluate(left, t if kind == "y" else 0.0, t if kind == "x" else 0.0)
            values = np.array(np.broadcast_to(values, t.shape), dtype=float, copy=True)
            values[~np.isfinite(values)] = np.nan
            span = ymax - ymin if kind == "y" else xmax - xmin
            # Break large jumps so poles don't create lines across the graph.
            jumps = np.flatnonzero(np.abs(np.diff(values)) > span / 2)
            values[jumps] = np.nan
            values[jumps + 1] = np.nan
            ax.plot(t if kind == "y" else values, values if kind == "y" else t, color=color, linewidth=2)
            low, high = (ymin, ymax) if kind == "y" else (xmin, xmax)
            return bool(np.any(np.isfinite(values) & (values >= low) & (values <= high)))
        xx, yy = np.meshgrid(np.linspace(xmin, xmax, 601), np.linspace(ymin, ymax, 601))
        values = np.array(np.broadcast_to(evaluate(left, xx, yy) - evaluate(right, xx, yy), xx.shape), dtype=float)
        finite = values[np.isfinite(values)]
        if not finite.size:
            return False
        if np.all(finite == 0):
            raise ValueError("This equation holds everywhere in its domain; it doesn't define a single curve.")
        if finite.min() > 0 or finite.max() < 0:
            return False
        contour = ax.contour(xx, yy, np.ma.masked_invalid(values), levels=[0], colors=[color], linewidths=2)
        return any(len(segment) > 1 for segment in contour.allsegs[0])


class Grapher:
    def __init__(self, root):
        self.root = root
        root.title("XY Equation Grapher")
        root.geometry("1050x730")
        root.minsize(800, 580)
        panel = ttk.Frame(root, padding=12)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(panel, text="Your equations", font=("Arial", 15, "bold")).pack(anchor="w")
        ttk.Label(panel, text="One equation per line", padding=(0, 6)).pack(anchor="w")
        self.equations = tk.Text(panel, width=28, height=13, font=("Consolas", 12), undo=True)
        self.equations.pack(fill=tk.X)
        self.equations.insert("1.0", "y = 4x + 10\ny = x - 5")
        ttk.Label(panel, text="Examples:\ny = 2x + 3\nx + 2y = 8\nx = 4\ny = x^2\nx^2 + y^2 = 25\ny = sin(x)", padding=(0, 10)).pack(anchor="w")
        limits = ttk.LabelFrame(panel, text="Graph range", padding=8)
        limits.pack(fill=tk.X, pady=8)
        self.limits = []
        for row, (label, default) in enumerate((("x minimum", "-20"), ("x maximum", "20"), ("y minimum", "-20"), ("y maximum", "100"))):
            ttk.Label(limits, text=label).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(limits, width=10)
            entry.insert(0, default)
            entry.grid(row=row, column=1, padx=10)
            self.limits.append(entry)
        self.equal = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Equal x/y scale (for circles)", variable=self.equal).pack(anchor="w")
        ttk.Button(panel, text="Graph", command=self.graph).pack(fill=tk.X, pady=10)
        self.status = tk.StringVar()
        ttk.Label(panel, textvariable=self.status, wraplength=240).pack(anchor="w")
        ttk.Label(panel, text="Use the toolbar to zoom, pan or save.\nTrig functions use radians.\nGeneral equations use an approximate\ncontour; very small features or poles\nmay not be shown accurately.", padding=(0, 12)).pack(anchor="w")
        plot = ttk.Frame(root)
        plot.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.figure = Figure(figsize=(7, 6), layout="constrained")
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot, pack_toolbar=False)
        self.toolbar.pack(fill=tk.X)
        root.bind("<Control-Return>", lambda event: self.graph())
        self.graph()

    def graph(self):
        try:
            bounds = tuple(float(entry.get()) for entry in self.limits)
            if not all(np.isfinite(bounds)) or bounds[0] >= bounds[1] or bounds[2] >= bounds[3]:
                raise ValueError("Use finite range values with each minimum below its maximum.")
            lines = [line.strip() for line in self.equations.get("1.0", "end").splitlines() if line.strip()]
            if not lines or len(lines) > 20:
                raise ValueError("Enter between 1 and 20 equations.")
            for number, line in enumerate(lines, 1):
                try:
                    parse_equation(line)
                except (ValueError, OverflowError, RecursionError) as error:
                    raise ValueError(f"Equation {number}: {error}") from error
        except ValueError as error:
            messagebox.showerror("Check your input", str(error))
            return
        self.ax.clear()
        handles, messages = [], []
        for number, line in enumerate(lines, 1):
            color = COLORS[(number - 1) % len(COLORS)]
            try:
                visible = draw_equation(self.ax, line, bounds, color)
                handles.append(Line2D([0], [0], color=color, lw=2, label=line))
                if not visible:
                    messages.append(f"Equation {number}: no curve found in this range.")
            except (ValueError, TypeError, OverflowError, RecursionError) as error:
                messages.append(f"Equation {number}: {error}")
        self.ax.axhline(0, color="#333333", linewidth=1)
        self.ax.axvline(0, color="#333333", linewidth=1)
        self.ax.set_xlim(bounds[:2])
        self.ax.set_ylim(bounds[2:])
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_title("XY Graph")
        self.ax.grid(True, alpha=0.25)
        self.ax.set_aspect("equal" if self.equal.get() else "auto", adjustable="box")
        if handles:
            self.ax.legend(handles=handles, loc="upper right", fontsize=9)
        self.toolbar.update()
        self.canvas.draw()
        self.status.set("\n".join(messages) if messages else f"Graphed {len(lines)} equation(s).")


if __name__ == "__main__":
    app = tk.Tk()
    Grapher(app)
    app.mainloop()
