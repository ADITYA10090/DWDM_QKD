import pandas as pd
import math
import numpy as np

#############################################
# Functions for loading and querying the results CSV
#############################################

def load_results_from_csv(filename="results.csv"):
    """
    Load the results CSV file into a DataFrame.
    """
    df = pd.read_csv(filename)
    return df

def get_least_S_for_Q_excluding_CCh_from_csv(Q, CCh, filename="results.csv"):
    """
    For a given Q configuration and exclusion list CCh, load the results from CSV,
    filter for rows corresponding to Q, then return the candidate gi with the smallest S
    that is not in Q and not in CCh.
    
    Parameters:
      - Q: tuple or list of numbers representing the configuration.
      - CCh: list of numbers to exclude.
      - filename: path to the CSV file containing results.
      
    Returns:
      - A tuple (gi, S) where gi is the candidate with the smallest S not in Q or CCh.
      - If no candidate is found, returns None.
    """
    # Create the string representation of Q as stored in the CSV.
    Q_str = '-'.join(map(str, Q))
    
    # Load the results DataFrame.
    df = load_results_from_csv(filename)
    
    # Filter for rows where the Q column matches Q_str.
    df_Q = df[df["Q"] == Q_str]
    
    # Exclude rows where gi is in Q or in CCh.
    exclusion_set = set(Q) | set(CCh)
    df_filtered = df_Q[~df_Q["gi"].isin(exclusion_set)]
    
    if df_filtered.empty:
        return None
    
    # Get the row with the minimum S value.
    best_row = df_filtered.loc[df_filtered["S"].idxmin()]
    gi = best_row["gi"]
    S = best_row["S"]
    return gi, S

#############################################
# Functions for loading and querying the B_table
#############################################

def load_B_table(filename="B_table.csv"):
    """
    Load the precomputed B_table from a CSV file.
    The CSV is assumed to have rows indexed by 'a' values and columns labeled by 'b' values.
    """
    table = pd.read_csv(filename, index_col=0)
    # Ensure that the row index and column labels are integers.
    table.index = table.index.astype(int)
    table.columns = table.columns.astype(int)
    return table

def get_B_from_table(gi, q, B_table):
    """
    Retrieve B(gi, q) from the precomputed B_table.
    """
    try:
        return float(B_table.at[int(gi), int(q)])
    except KeyError:
        raise ValueError(f"B_table does not contain entry for gi={gi} and q={q}.")

def compute_S_for_candidate(gi, Q, B_table):
    """
    Compute the total S for a candidate gi given configuration Q.
    S(gi, Q) = sum over each q in Q of (q * B(gi, q))
    """
    total_S = 0
    for q in Q:
        B_val = get_B_from_table(gi, q, B_table)
        total_S += q * B_val
    return total_S

#############################################
# Main section: example usage
#############################################

if __name__ == "__main__":
    # Example Q configuration and exclusion list.
    Q_demo = [1535,1543]  # For instance, configuration with a single element 1535.
    CCh_demo = [1530, 1531, 1532, 1533, 1534, 1536, 1537, 1538, 1560, 1561, 1562, 1563, 1564, 1565]
    
    # First, get the best candidate (gi, S) from the results CSV.
    best_candidate = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo, filename="results.csv")
    if best_candidate:
        gi_best, S_best = best_candidate
        print(f"For Q = {Q_demo} excluding {CCh_demo}, the best candidate is gi = {gi_best} with S = {S_best}")
    else:
        print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")
    

    gi_best,S_best=best_candidate
    CCh_demo.append(gi_best)
    # Load the precomputed B_table.
    B_table = load_B_table("B_table.csv")
    
    # For each element in Q_demo, calculate the sum over all gi in CCh_demo
    # of (q * B(gi, q)) and print the value.
    print("\nSum of S values for each q in Q_demo over candidates in CCh_demo:")
    p_m_list=[]
    for q in Q_demo:
        total_for_q = 0
        for candidate in CCh_demo:
            try:
                # Calculate contribution for candidate using q
                S_val = q * get_B_from_table(candidate, q, B_table)
                total_for_q += S_val
            except ValueError as e:
                print(f"Candidate gi = {candidate}: {e}")
        p_m_list.append(total_for_q)
        print(f"For q = {q}, total sum = {total_for_q}")
    print(p_m_list)
