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
    df["gi"] = pd.to_numeric(df["gi"], errors="coerce")
    df["S"] = pd.to_numeric(df["S"], errors="coerce")
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

def plot_cumulative_distribution(Q, iterations_data):
    """
    Plot the cumulative distribution using data from all previous iterations.
    For each iteration, plot:
      - Q channels (blue circles) at that iteration's y-value.
      - The entire exclusion list (cch_demo) for that iteration in red asterisks.
      - The candidate (if any) as a green triangle.
    
    The y-value for each iteration is the total channel count, calculated as:
      total_channels = len(Q) + len(CCh) + (1 if candidate exists else 0)
    """
    plt.figure(figsize=(10, 10))
    
    for data in iterations_data:
        y = data['y']
        # Plot Q channels (blue circles).
        plt.scatter(list(Q), [y] * len(Q), color='blue', marker='o', s=100,
                    label="Q Channels" if data is iterations_data[0] else "")
        # Plot the exclusion list (cch_demo) for this iteration in red.
        plt.scatter(data['CCh'], [y] * len(data['CCh']), color='red', marker='*', s=150,
                    label="Excluded Channels" if data is iterations_data[0] else "")
        # Plot candidate if available.
        if data['candidate'] is not None:
            plt.scatter([data['candidate']], [y], color='green', marker='^', s=150,
                        label="Candidate" if data is iterations_data[0] else "")
    
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Total Channel Count")
    plt.title("Cumulative Data Distribution Across Iterations")
    plt.xlim(1530, 1565)
    # Set y-axis limits based on the maximum total channels across iterations.
    max_y = max([data['y'] for data in iterations_data]) if iterations_data else 10
    plt.ylim(0, max_y + 10)
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Fixed Q configuration (wavelength positions)
    Q_demo = (1530, 1537, 1538)
    
    # List to store cumulative data for each iteration.
    # Each element is a dictionary with keys: 'y', 'CCh', and 'candidate'
    iterations_data = []
    
    # Run 10 iterations.
    for i in range(10):
        print(f"\nIteration {i+1}:")
        
        # Load the exclusion list; if not available, use a default list.
        CCh_demo = load_exclusion_list()
        if not CCh_demo:
            CCh_demo = [1531, 1532, 1533, 1534, 1535, 1536, 1539, 1540, 1541, 1560, 1561, 1562, 1563, 1564, 1565]
        
        # Find a candidate for the given Q configuration.
        candidate_result = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo)
        if candidate_result:
            candidate_gi, candidate_S = candidate_result
            print(f"Candidate with smallest S is gi={candidate_gi} with S={candidate_S}")
            # Update the exclusion list with the new candidate.
            CCh_demo.append(int(candidate_gi))
            save_exclusion_list(CCh_demo)
        else:
            print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")
        
        # Compute the total channels for this iteration.
        total_channels = len(Q_demo) + len(CCh_demo) + (1 if candidate_result is not None else 0)
        
        # Store the current iteration data.
        iteration_info = {
            'y': total_channels,
            'CCh': list(CCh_demo),  # make a copy of the current exclusion list
            'candidate': candidate_result[0] if candidate_result is not None else None
        }
        iterations_data.append(iteration_info)
        
        # Plot the cumulative distribution including data from all iterations so far.
        plot_cumulative_distribution(Q_demo, iterations_data)
