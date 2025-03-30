import pandas as pd
import itertools
import sys

# Import the CSV-based candidate function from the separate module.
from least_candidate_from_csv import get_least_S_for_Q_excluding_CCh_from_csv

def load_results_df(filename="results.csv"):
    """
    Load the results CSV into a DataFrame.
    """
    return pd.read_csv(filename)

def get_first_fit_candidate(Q, CCh, df_all):
    """
    For a given Q and CCh, scan from candidate 1565 down to 1530.
    For the given Q (stored in CSV as a hyphen-separated string),
    return the first candidate (and its S value) that is not in Q or CCh.
    If none is found, return None.
    """
    Q_str = '-'.join(map(str, Q))
    df_Q = df_all[df_all["Q"] == Q_str]
    exclusion_set = set(Q) | set(CCh)
    
    # Scan from 1565 down to 1530.
    for candidate in range(1565, 1529, -1):
        if candidate not in exclusion_set:
            row = df_Q[df_Q["gi"] == candidate]
            if not row.empty:
                S_val = row.iloc[0]["S"]
                return candidate, S_val
    return None

def main():
    # Define candidate set G.
    G = list(range(1530, 1566))
    
    # Load the CSV results DataFrame.
    df_all = load_results_df("results.csv")
    
    # Iterate over all Q combinations (sizes 1 to 4).
    for size_Q in range(1, 5):
        for Q in itertools.combinations(G, size_Q):
            # For each Q, define available candidates for CCh (exclude those in Q).
            available_for_CCh = set(G) - set(Q)
            # For CCh, consider combinations of sizes 1 to 3 from available candidates.
            for size_CCh in range(1, 4):
                for CCh in itertools.combinations(available_for_CCh, size_CCh):
                    # Get candidate from the CSV-based function.
                    result_csv = get_least_S_for_Q_excluding_CCh_from_csv(Q, CCh, filename="results.csv")
                    # Get candidate from the first fit algorithm.
                    result_first_fit = get_first_fit_candidate(Q, CCh, df_all)
                    # print(Q,result_csv,result_first_fit)
                    # Compare the results. If they differ, print details and break.
                    if result_csv != result_first_fit:
                        print("Mismatch found!")
                        print("Q configuration:", Q)
                        print("Exclusion list (CCh):", CCh)
                        if result_csv:
                            print("CSV function returns: gi = {}, S = {}".format(result_csv[0], result_csv[1]))
                        else:
                            print("CSV function returns: None")
                        
                        if result_first_fit:
                            print("First fit algorithm returns: gi = {}, S = {}".format(result_first_fit[0], result_first_fit[1]))
                        else:
                            print("First fit algorithm returns: None")
                        
                        sys.exit(0)
    
    print("All combinations produced matching results.")

if __name__ == "__main__":
    main()
