from sympy import symbols, plot
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)

x = symbols("x")
transforms = standard_transformations + (implicit_multiplication_application, convert_xor)

print("Type equations like:  y = 4*x + 10   or just   x - 5")
print("Press Enter on a blank line when you're done.\n")

exprs = []
while True:
    text = input("f(x) = ").strip()
    if not text:
        break
    # allow "y = ..." or "f(x) = ..." by keeping only the right side
    if "=" in text:
        text = text.split("=", 1)[1]
    try:
        exprs.append(parse_expr(text, transformations=transforms))
    except Exception as e:
        print(f"  Couldn't read that ({e}). Try again.")

if exprs:
    p = plot(*exprs, (x, -20, 20), legend=True, title="Graph",
             xlabel="x", ylabel="f(x)", show=False)
    p.show()
else:
    print("Nothing to plot.")