"""Plot multiple functions on a single graph.

Type equations like:
    y = 4*x + 10
    x - 5
    sin(x)
    x**2 - 3*x + 1

Press Enter on a blank line when you're done.
"""

from sympy import symbols, plot
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

x = symbols("x")
transforms = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def read_expression(text):
    """Turn user text into a sympy expression, or None if it can't be read."""
    text = text.strip()
    if not text:
        return None
    # Allow "y = ..." or "f(x) = ..." by keeping only the right-hand side.
    if "=" in text:
        text = text.split("=", 1)[1]
    try:
        return parse_expr(text, transformations=transforms)
    except Exception as e:
        print(f"  Couldn't read that ({e}). Try again.")
        return None


def main():
    print("Type equations like:  y = 4*x + 10   or just   x - 5")
    print("Press Enter on a blank line when you're done.\n")

    exprs = []
    while True:
        text = input("f(x) = ")
        if not text.strip():
            break
        expr = read_expression(text)
        if expr is not None:
            exprs.append(expr)

    if not exprs:
        print("Nothing to plot.")
        return

    p = plot(
        *exprs,
        (x, -20, 20),
        legend=True,
        title="Graph",
        xlabel="x",
        ylabel="f(x)",
        show=False,
    )
    p.show()


if __name__ == "__main__":
    main()
