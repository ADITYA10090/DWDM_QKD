import pandas as pd
import json
import os

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

def load_exclusion_list(filename="exclusion_list.json"):
    """
    Load the exclusion list from a JSON file.
    If the file does not exist or is empty/invalid, return an empty list.
    """
    if os.path.exists(filename):
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Return an empty list if JSON is malformed.
                    return []
    return []


def save_exclusion_list(CCh, filename="exclusion_list.json"):
    """
    Save the exclusion list to a JSON file.
    """
    with open(filename, "w") as file:
        json.dump(CCh, file)

# Optional: Test the function if this file is run as a script.
if __name__ == "__main__":
    # Example Q configuration.
    Q_demo = (1530, 1537, 1538)
    
    # Load exclusion list from file; if file not found, use a default list.
    CCh_demo = load_exclusion_list()
    if not CCh_demo:
        CCh_demo = [1531, 1532, 1533,1534,1535,1536, 1557, 1558, 1560, 1561, 1562, 1563, 1564, 1565]
    
    result = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo)
    if result:
        gi, S = result
        print(f"Candidate with smallest S is gi={gi} with S={S}")
        # Convert gi to a Python int before appending.
        CCh_demo.append(int(gi))
        # Save the updated exclusion list back to file.
        save_exclusion_list(CCh_demo)
    else:
        print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")

