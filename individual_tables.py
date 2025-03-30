import pandas as pd
import math
import numpy as np

# Read the input CSV file (assumed to be named 'input.csv')
# The CSV file should have two columns:
#   - First column: wavelength (in nm), expected to be in the range 1530 to 1565.
#   - Second column: corresponding value B(1550, wavelength)
df_input = pd.read_csv("input_big.csv", header=None, names=["x", "y"])

# Create a lookup dictionary for B(1550, x)
# It is assumed that x values are unique.
y_lookup = dict(zip(df_input["x"], df_input["y"]))

def compute_B(a, b):
    """
    Compute B(a, b) using the formula:
    
      B(a,b) = (λ_del / λ_q)^4 * B(1550, λ_del)
      
    where:
      λ_del = floor( 1 / (1/1550 - 1/a + 1/b) )
      λ_q   = b   (in nm)
      B(1550, λ_del) is obtained by directly looking up λ_del in the input data.
    
    Special case: if a equals b, return infinity.
    """
    # Special case: when a equals b
    if math.isclose(a, b, rel_tol=1e-9):
        return math.inf

    # Compute the denominator for λ_del
    denominator = 1/1550 - 1/a + 1/b
    if math.isclose(denominator, 0, rel_tol=1e-9):
        raise ValueError(f"Denominator is zero for a={a} and b={b}")
    
    # Compute λ_del as a float and then take the floor (greatest integer less than it)
    lambda_del_float = 1 / denominator
    lambda_del = math.floor(lambda_del_float)
    
    # Define λ_q; here we assume λ_q = b (in nm)
    lambda_q = b

    # Lookup B(1550, λ_del) from the input data dictionary
    if lambda_del not in y_lookup:
        raise ValueError(f"λ_del value {lambda_del} not found in input data.")
    B1550_lambda_del = y_lookup[lambda_del]
    
    # Compute the final value using the formula
    result = ((lambda_del / lambda_q) ** 4) * B1550_lambda_del
    return result

# Loop over a and b in the range 1530 to 1565.
# For each a, compute B(a, b) for every b, and save the results in a CSV file named "a nm.csv".
for a in range(1530, 1531):
    computed_results = []
    for b in range(1530, 1566):
        try:
            B_val = compute_B(a, b)
        except ValueError as e:
            print(f"Skipping a={a}, b={b} due to error: {e}")
            B_val = np.nan
        computed_results.append({"b": b, "B(a,b)": B_val})
    
    df_result = pd.DataFrame(computed_results)
    output_filename = f"{a} nm.csv"
    df_result.to_csv(output_filename, index=False)
    print(f"Saved computed data for a={a} in file: {output_filename}")

def get_B(a, b):
    """
    Retrieve B(a, b) using the formula.
    """
    return compute_B(a, b)

# Example usage:
if __name__ == "__main__":
    # For example, retrieve B(1545, 1561)
    a = 1545
    b = 1536
    try:
        result = get_B(a, b)
        print(f"B({a},{b}) = {result}")
    except Exception as e:
        print(e)
