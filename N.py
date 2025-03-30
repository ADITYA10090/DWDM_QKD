import pandas as pd
import math
import numpy as np

# Read the input CSV file (assumed to be named 'input.csv')
# The CSV file should have two columns: the first for x values and the second for y values.
df_input = pd.read_csv("input.csv", header=None, names=["x", "y"])

# Create a dictionary to easily lookup y given x.
# Assuming x values are unique:
y_lookup = dict(zip(df_input["x"], df_input["y"]))

def compute_B(i, x, y):
    """
    Compute B(i, x) using the formula:
    B(i,x) = ((1/(1/1500 - 1/i + 1/x))/x)^4 * y
    with a special case: if i equals x, return infinity.
    """
    # Special case: when i equals x
    if math.isclose(i, x, rel_tol=1e-9):
        return math.inf

    # Calculate the inner denominator: (1/1500 - 1/i + 1/x)
    denominator = 1/1550 - 1/i + 1/x

    # To avoid division by zero, check if denominator is 0.
    if math.isclose(denominator, 0, rel_tol=1e-9):
        raise ValueError(f"Denominator is zero for i={i} and x={x}")

    # Compute the factor = (1/(denominator))/x
    factor = (1 / denominator) / x

    # Apply the power 4 and multiply by y
    result = (factor ** 4) * y
    return result

# Loop through i values from 1530 to 1565
for i in range(1530, 1531):
    computed_results = []
    # Iterate over the rows in the input data
    for _, row in df_input.iterrows():
        x = row["x"]
        y = row["y"]
        # print(x,y)
        try:
            B_val = compute_B(i, x, y)
        except ValueError as e:
            print(f"Skipping i={i}, x={x} due to error: {e}")
            B_val = np.nan  # or handle as needed
        
        computed_results.append({"x": x, "B(i,x)": B_val})
    
    # Convert the results to a DataFrame
    df_result = pd.DataFrame(computed_results)
    
    # Save the computed data to a CSV file named as "i nm.csv"
    output_filename = f"{i} nm.csv"
    df_result.to_csv(output_filename, index=False)
    print(f"Saved computed data for i={i} in file: {output_filename}")

def get_B(a, b):
    """
    Function to retrieve B(a, b):
    - a: i value.
    - b: x value.
    It looks up the y corresponding to x=b from the input data and computes B(a, b).
    """
    # Check if b exists in our lookup
    if b not in y_lookup:
        raise ValueError(f"x value {b} not found in input data.")
    
    y_val = y_lookup[b]
    return compute_B(a, b, y_val)

# Example usage of get_B function:
if __name__ == "__main__":
    # For example, retrieve B(1550, 1600)
    a = 1545
    b = 1561
    try:
        result = get_B(a, b)
        print(f"B({a},{b}) = {result}")
    except Exception as e:
        print(e)
