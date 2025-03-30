import pandas as pd
import json
import os
import matplotlib.pyplot as plt

def load_results_from_csv(filename="results.csv"):
    """
    Load the results CSV file into a DataFrame.
    Ensure that 'gi' and 'S' columns are numeric.
    """
    df = pd.read_csv(filename)
    # Convert columns to numeric; errors become NaN
    df["gi"] = pd.to_numeric(df["gi"], errors="coerce")
    df["S"] = pd.to_numeric(df["S"], errors="coerce")
    # Drop rows with missing values in critical columns
    df = df.dropna(subset=["gi", "S"])
    return df

def get_least_S_for_Q_excluding_CCh_from_csv(Q, CCh, filename="results.csv"):
    """
    For a given Q configuration and exclusion list CCh, load the results from CSV,
    filter for rows corresponding to Q, then return the candidate gi with the smallest S
    that is not in Q and not in CCh.
    Returns:
      - A tuple (gi, S) for the candidate with the smallest S, or None if not found.
    """
    Q_str = '-'.join(map(str, Q))
    df = load_results_from_csv(filename)
    print("Total rows in CSV:", len(df))
    
    df_Q = df[df["Q"] == Q_str]
    print("Rows after filtering Q:", len(df_Q))
    
    exclusion_set = set(Q) | set(CCh)
    df_filtered = df_Q[~df_Q["gi"].isin(exclusion_set)]
    print("Rows after excluding Q and CCh:", len(df_filtered))
    
    if df_filtered.empty:
        return None
    
    best_row = df_filtered.loc[df_filtered["S"].idxmin()]
    candidate_gi = best_row["gi"]
    candidate_S = best_row["S"]
    print(f"Found candidate: gi={candidate_gi}, S={candidate_S}")
    return candidate_gi, candidate_S

def load_exclusion_list(filename="exclusion_list.json"):
    """
    Load the exclusion list from a JSON file.
    Returns an empty list if the file does not exist or is invalid.
    """
    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                content = file.read().strip()
                if content:
                    return json.loads(content)
        except json.JSONDecodeError:
            return []
    return []

def save_exclusion_list(CCh, filename="exclusion_list.json"):
    """
    Save the exclusion list to a JSON file.
    """
    with open(filename, "w") as file:
        json.dump(CCh, file)

def plot_channel_assignment(Q, CCh, candidate, csv_filename="results.csv", scale_factor=100):
    """
    Plot channel assignment with scaled y-axis values to enhance visibility of differences.
      - x-axis: assigned wavelength (gi)
      - y-axis: scaled total channels (S * scale_factor)
    
    Groups:
      - Available candidates (not in Q or CCh) are plotted in grey.
      - Q channels are plotted in blue.
      - Excluded channels (CCh) are plotted in red with rounded markers.
      - The selected candidate is plotted solely in green.
    """
    df = load_results_from_csv(csv_filename)
    
    Q_set = set(Q)
    CCh_set = set(CCh)
    all_exclusions = Q_set.union(CCh_set)
    
    # Create a new column for scaled S values.
    df["S_scaled"] = df["S"] * scale_factor
    
    # Compute boolean masks.
    mask_Q = df["gi"].isin(Q_set)
    mask_CCh = df["gi"].isin(CCh_set)
    mask_available = ~df["gi"].isin(all_exclusions)
    
    # Remove candidate from available candidates if candidate exists.
    if candidate is not None:
        candidate_gi, candidate_S = candidate
        mask_candidate = (df["gi"] == candidate_gi)
        mask_available = mask_available & (~mask_candidate)
    
    plt.figure(figsize=(8, 20))
    
    # Plot available candidates in grey.
    available_df = df.loc[mask_available]
    plt.scatter(available_df["gi"], available_df["S_scaled"], 
                color='grey', marker='o', s=80, label="Available Candidates")
    
    # Plot Q channels in blue.
    Q_df = df.loc[mask_Q]
    plt.scatter(Q_df["gi"], Q_df["S_scaled"], 
                color='blue', marker='o', s=80, label="Q Channels")
    
    # Plot Excluded channels in red.
    CCh_df = df.loc[mask_CCh]
    plt.scatter(CCh_df["gi"], CCh_df["S_scaled"], 
                color='red', marker='o', s=80, label="Excluded Channels")
    
    # Plot the selected candidate solely in green.
    if candidate is not None:
        candidate_gi, candidate_S = candidate
        plt.scatter([candidate_gi], [candidate_S * scale_factor], 
                    color='green', marker='^', s=120, label="Selected Candidate")
    
    plt.xlabel("Assigned Wavelength (Channel gi)")
    plt.ylabel(f"Total Channels (S) x {scale_factor}")
    plt.title("Channel Assignment with Scaled Y-Axis")
    # plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    Q_demo = (1530, 1537, 1538)
    
    CCh_demo = load_exclusion_list()
    if not CCh_demo:
        CCh_demo = [1531, 1532, 1533, 1534, 1535, 1536, 1539, 1540, 1541, 1560, 1561, 1562, 1563, 1564, 1565]
    
    candidate_result = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo)
    if candidate_result:
        candidate_gi, candidate_S = candidate_result
        print(f"Candidate with smallest S is gi={candidate_gi} with S={candidate_S}")
        CCh_demo.append(int(candidate_gi))
        save_exclusion_list(CCh_demo)
    else:
        print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")
    
    plot_channel_assignment(Q_demo, CCh_demo, candidate_result)
