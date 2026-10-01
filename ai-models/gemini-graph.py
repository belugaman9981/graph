import sympy as sp
from sympy.plotting import plot

def plot_user_functions():
    # Define the symbol 'x'
    x = sp.symbols('x')
    
    print("--- Mathematical Function Plotter ---")
    print("Enter expressions in terms of x (e.g., '4*x + 10', 'x - 5', 'x**2').")
    print("Type 'done' when you are finished entering functions.\n")
    
    expressions = []
    
    while True:
        user_input = input("Enter a function f(x) [or 'done']: ").strip()
        
        if user_input.lower() == 'done':
            break
            
        if not user_input:
            continue
            
        try:
            # Parse the user input string into a SymPy expression
            expr = sp.sympify(user_input)
            expressions.append(expr)
            print(f"Added: f(x) = {expr}")
        except Exception as e:
            print(f"Invalid input. Please use valid mathematical expressions (e.g., use '*' for multiplication). Error: {e}")
    
    if not expressions:
        print("No functions were entered.")
        return

    # Ask for range limits
    try:
        x_min = float(input("Enter min x value (default -20): ") or -20)
        x_max = float(input("Enter max x value (default 20): ") or 20)
    except ValueError:
        x_min, x_max = -20, 20

    # Create the plot combining all expressions
    print("Plotting graph...")
    
    # SymPy's plot function supports passing multiple expressions directly
    p = plot(
        *expressions,
        (x, x_min, x_max),
        title="Graph",
        xlabel="x",
        ylabel="f(x)",
        legend=True,
        show=True
    )

if __name__ == "__main__":
    plot_user_functions()