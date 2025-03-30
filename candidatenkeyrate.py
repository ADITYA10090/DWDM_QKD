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
    """
    Q_str = '-'.join(map(str, Q))
    df = load_results_from_csv(filename)
    df_Q = df[df["Q"] == Q_str]
    exclusion_set = set(Q) | set(CCh)
    df_filtered = df_Q[~df_Q["gi"].isin(exclusion_set)]
    
    if df_filtered.empty:
        return None
    
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
# SKR (Secret Key Rate) Calculation Functions
#############################################

def SKR(p_m):
    # Constants
    h = 6.626e-34  # Planck's constant (J·s)
    c = 3.0e8      # Speed of light (m/s)
    
    # Parameters/constants
    gamma_dc = 1e-10
    T_d = 100*(10**(-12))
    I = 0.0000000008
    alpha = 0.046
    L = 50
    delta_lambda = 125
    eta_d = 0.3
    ed = 0.015
    Ts = 250*(10**(-12))
    f = 1.16
    Y1 = 1
    mu = 0.48
    
    # Helper functions
    def compute_C_f(I, alpha, L, delta_lambda, T_d, eta_d):
        return (I * np.exp(-alpha * L) * L  * T_d * eta_d) / (2 * h * delta_lambda * (10**(9)))
    
    def compute_C_b(I, alpha, L, delta_lambda, T_d, eta_d):
        return (I * (1 - np.exp(-2 * alpha * L)) / (2 * alpha) * delta_lambda * T_d * eta_d) / (2 * h * c)
    
    def binary_entropy(x):
        if x == 0 or x == 1:
            return 0
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)
    
    def compute_P_Y0(Q1, e1, f, Q_mu, E_mu):
        return Q1 * (1-binary_entropy(e1)) - f * Q_mu * binary_entropy(E_mu)
    
    def compute_Q_mu(Y0, eta, mu):
        return 1 - (1 - Y0) * np.exp(-eta * mu)
    
    def compute_E_mu(Y0, ed, eta, mu, Q_mu):
        return (Y0 / 2 + ed * (1 - np.exp(-eta * mu))) / Q_mu
    
    def compute_Q1(Y1, mu):
        return Y1 * mu * np.exp(-mu)
    
    def compute_e1(Y0, ed, eta, Y1):
        return (Y0 / 2 + ed * eta) / Y1
    
    def compute_eta(eta_d, alpha, L):
        return (1 / 2) * eta_d * np.exp(-alpha * L)
    
    def compute_Rm(P_Y0, Ts):
        return max(0, P_Y0 / Ts)
    
    def compute_Y0(p_dc, p_m):
        return 1 - (1 - (p_dc + p_m))**2
    
    def compute_p_dc(gamma_dc, T_d):
        return gamma_dc * T_d

    # Compute constant factors
    C_f = compute_C_f(I, alpha, L, delta_lambda, T_d, eta_d)  # Alternatively, you can compute C_f using compute_C_f(...)
    p_dc = compute_p_dc(gamma_dc, T_d)
    # Adjust p_m with the factor C_f
    p_m_adjusted = p_m * C_f
    Y0 = compute_Y0(p_dc, p_m_adjusted)
    C_b = compute_C_b(I, alpha, L, delta_lambda, T_d, eta_d)
    Q1 = compute_Q1(Y1, mu)
    eta = compute_eta(eta_d, alpha, L)
    Q_mu = compute_Q_mu(Y0, eta, mu)
    E_mu = compute_E_mu(Y0, ed, eta, mu, Q_mu)
    e1 = compute_e1(Y0, ed, eta, Y1)
    P_Y0 = compute_P_Y0(Q1, e1, f, Q_mu, E_mu)
    Rm = compute_Rm(P_Y0, Ts)
    print(binary_entropy(e1),binary_entropy(E_mu))
    # Return Rm scaled by 10^(-7)
    return Rm * 1e-7

#############################################
# Main Section: Combine CSV processing and SKR calculation
#############################################

if __name__ == "__main__":
    # Define Q configuration and exclusion list.
    Q_demo = [1537,1564]
    CCh_demo = [1530, 1531, 1532, 1533, 1534, 1536, 1538, 1560, 1561, 1562, 1563, 1565]
    
    # Get the best candidate from the results CSV.
    best_candidate = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, CCh_demo, filename="results.csv")
    if best_candidate:
        gi_best, S_best = best_candidate
        print(f"For Q = {Q_demo} excluding {CCh_demo}, the best candidate is gi = {gi_best} with S = {S_best}")
    else:
        print(f"No candidate found for Q = {Q_demo} excluding {CCh_demo}")
        exit()
    
    # Add the best candidate to the exclusion list.
    CCh_demo.append(gi_best)
    
    # Load the precomputed B_table.
    B_table = load_B_table("B_table.csv")
    
    # Calculate the sum over all candidates in CCh_demo for each q in Q_demo.
    print("\nSum of S values for each q in Q_demo over candidates in CCh_demo:")
    p_m_list = []
    for q in Q_demo:
        total_for_q = 0
        for candidate in CCh_demo:
            try:
                S_val = q * get_B_from_table(candidate, q, B_table)
                total_for_q += S_val
            except ValueError as e:
                print(f"Candidate gi = {candidate}: {e}")
        p_m_list.append(total_for_q)
        print(f"For q = {q}, total sum = {total_for_q}")
    print(f"\np_m_list = {p_m_list}")
    
    # Now, use the p_m_list to compute the total secret key rate (Rm)
    total_keyrate = 0
    for p_m in p_m_list:
        constant=SKR(p_m)
        total_keyrate += constant
    
    print(f"\nTotal Secret Key Rate (Rm): {total_keyrate}")
