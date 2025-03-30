# main_module.py

import pandas as pd
import numpy as np
import itertools

def load_B_table(filename="B_table.csv"):
    """
    Load the precomputed B table from a CSV file.
    Convert the index and column names to numeric types.
    """
    table = pd.read_csv(filename, index_col=0)
    table.index = pd.to_numeric(table.index, errors='coerce')
    table.columns = pd.to_numeric(table.columns, errors='coerce')
    return table

# Load the lookup table as a DataFrame.
B_lookup_df = load_B_table()

# Precompute a NumPy array version and mapping dictionaries.
B_lookup_np = B_lookup_df.values
row_values = B_lookup_df.index.to_numpy()
col_values = B_lookup_df.columns.to_numpy()
row_index = {val: idx for idx, val in enumerate(row_values)}
col_index = {val: idx for idx, val in enumerate(col_values)}

def get_B_vectorized(gi, q_list):
    """
    For a given gi and a list/array of q values, 
    retrieve the corresponding B(gi, q) values in one go.
    """
    gi_pos = row_index.get(float(gi))
    if gi_pos is None:
        raise ValueError(f"gi={gi} not found in the lookup table.")
    
    q_positions = []
    for q in q_list:
        pos = col_index.get(float(q))
        if pos is None:
            raise ValueError(f"q={q} not found in the lookup table.")
        q_positions.append(pos)
    
    return B_lookup_np[gi_pos, q_positions]

def compute_sorted_sums_for_Q(G, Q):
    """
    For a given configuration Q (a tuple of 1 to 4 elements from G),
    compute for each remaining element gi in G (i.e. gi not in Q):
    
        S(gi, Q) = sum_{q in Q} (q * B(gi, q))
    
    Uses vectorized operations for speed.
    
    Returns a sorted list of tuples (gi, S) sorted in ascending order by S.
    """
    Q_arr = np.array(Q, dtype=float)
    
    Q_col_positions = []
    for q in Q:
        pos = col_index.get(float(q))
        if pos is None:
            raise ValueError(f"q={q} not found in the lookup table.")
        Q_col_positions.append(pos)
    Q_col_positions = np.array(Q_col_positions)
    
    # All gi not in Q.
    remaining = [g for g in G if g not in Q]
    remaining_positions = [row_index.get(float(g)) for g in remaining]
    
    submatrix = B_lookup_np[np.array(remaining_positions)][:, Q_col_positions]
    
    S_values = (submatrix * Q_arr).sum(axis=1)
    
    result_list = list(zip(remaining, S_values))
    result_list.sort(key=lambda tup: tup[1])
    return result_list

def store_results_to_csv(results, filename="results.csv"):
    """
    Store the results dictionary to a CSV file.
    Each row in the CSV contains:
      - Q configuration (as a hyphen-separated string)
      - Candidate gi
      - Corresponding S value.
    """
    data = []
    for Q, sorted_list in results.items():
        Q_str = '-'.join(map(str, Q))
        for gi, S in sorted_list:
            data.append({"Q": Q_str, "gi": gi, "S": S})
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")

def main():
    # Create G: an array of 36 elements (e.g., 1530 to 1565).
    G = [1530 + i for i in range(36)]
    
    results = {}
    # Generate all combinations Q of sizes 1, 2, 3, and 4 from G.
    for r in range(1, 5):
        for Q in itertools.combinations(G, r):
            sorted_sums = compute_sorted_sums_for_Q(G, Q)
            results[Q] = sorted_sums
    
    # For demonstration, print the first 5 Q combinations and their sorted results.
    for Q, sorted_list in list(results.items())[:5]:
        print(f"For Q = {Q}:")
        for gi, S in sorted_list:
            print(f"  gi = {gi}, S = {S}")
        print()
    
    # Save all results to a CSV file.
    store_results_to_csv(results, filename="results.csv")

if __name__ == "__main__":
    main()
