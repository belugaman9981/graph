"""
Function Grapher — plot one or more functions of x on a single graph.

Type functions using x as the variable, e.g.:
    4*x + 10
    x**2 - 5
    sin(x)
Separate multiple functions with commas, or enter them one at a time.
"""

from sympy import symbols, sympify, plot
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)

x = symbols("x")
TRANSFORMS = standard_transformations + (implicit_multiplication_application,) 


def parse_function(text):
    """Turn a user-typed string into a SymPy expression."""
    # allow ^ as exponent, since that's what most people type
    text = text.replace("^", "**")
    return parse_expr(text, local_dict={"x": x}, transformations=TRANSFORMS)


def main():
    print("=== Function Grapher ===")
    print("Enter functions of x, separated by commas.")
    print("Examples:  4*x + 10, x - 5")
    print("           x^2, sin(x), 1/x")
    print()

    raw = input("Function(s): ").strip()
    if not raw:
        print("Nothing entered — exiting.")
        return

    expressions = []
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            expressions.append(parse_function(piece))
        except Exception:
            print(f"  Could not understand: {piece!r} — skipping.")

    if not expressions:
        print("No valid functions to plot.")
        return

    # ask for a custom x-range (optional)
    xr = input("x-range [press Enter for -10 to 10]: ").strip()
    if xr:
        try:
            lo, hi = (float(v) for v in xr.replace("to", ",").split(","))
            domain = (x, lo, hi)
        except Exception:
            print("  Range not understood, using -10 to 10.")
            domain = (x, -10, 10)
    else:
        domain = (x, -10, 10)

    p = plot(*expressions, domain, show=False, legend=True, title="Graph",
             ylabel="f(x)", xlabel="x")
    p.show()


if __name__ == "__main__":
    main()