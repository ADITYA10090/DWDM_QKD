# least_candidate_from_csv.py

import pandas as pd

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

# Optional: Test the function if this file is run as a script.
if __name__ == "__main__":
    # Example Q configuration and exclusion list.
    Q_demo = [1530,1537,1539]
    CCh_demo = [1531,1532,1533,1534,1535,1536,1538,1540,1560,1561,1562,1563,1564,1565]
    
    result = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo)
    if result:
        gi, S = result
        print(f"For Q = {Q_demo} excluding {CCh_demo}, the candidate with the smallest S is gi = {gi} with S = {S}")
    else:
        print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")
