import pandas as pd
import math
import numpy as np

# Read the input CSV file (assumed to be named 'input_big.csv')
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

# Define the range for a and b (both from 1530 to 1565 inclusive)
a_values = range(1530, 1566)
b_values = range(1530, 1566)

# Create an empty DataFrame to hold the B(a,b) values.
# Rows are a values and columns are b values.
B_table = pd.DataFrame(index=a_values, columns=b_values)

# Populate the lookup table
for a in a_values:
    for b in b_values:
        try:
            B_table.at[a, b] = compute_B(a, b)
        except ValueError as e:
            print(f"Skipping a={a}, b={b} due to error: {e}")
            B_table.at[a, b] = np.nan

# Optionally, set the index and column names for clarity.
B_table.index.name = "a"
B_table.columns.name = "b"

# Save the complete lookup table to a single CSV file.
B_table.to_csv("B_table.csv")
print("Saved the B_table to 'B_table.csv'")

def get_B(a, b, table=B_table):
    """
    Retrieve B(a, b) from the precomputed B_table.
    
    Parameters:
      a (int or float): the value for a (should be between 1530 and 1565)
      b (int or float): the value for b (should be between 1530 and 1565)
      table (DataFrame): the lookup table containing B(a,b) values.
    
    Returns:
      The B(a, b) value from the table.
    """
    # Ensure a and b are numeric (cast if needed)
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        raise ValueError("Both a and b must be numeric.")
    
    # Retrieve from the table (note: the index and columns of the table are the a and b values)
    try:
        return table.at[int(a), int(b)]
    except KeyError:
        raise ValueError(f"Value a={a} or b={b} is not in the lookup table.")

# Example usage:
if __name__ == "__main__":
    # For example, retrieve B(1545, 1536)
    a_example = 1545
    b_example = 1536
    try:
        result = get_B(a_example, b_example)
        print(f"B({a_example}, {b_example}) = {result}")
    except Exception as e:
        print(e)
