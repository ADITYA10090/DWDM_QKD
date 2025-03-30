import math
import numpy as np
e=math.e
n_eff=0.3
y_dc=10**(-7)*(1e9)
error_corr_f=1.16
ed=0.015
Ts=250*(10**(-12))
T_d=100*(10**(-12))
alpha=0.046
L=40
I=0.00000001
delta_lambda=125
eta_d=0.3
f=1.16
Y1=1
mu=0.48
gamma_dc=1e-10

def SKR(p_m):
    # Constants
  h = 6.626e-34  # Planck's constant (Joule-second)
  c = 3.0e8      # Speed of light (m/s)


  def compute_C_f(I, alpha, L, delta_lambda, T_d, eta_d):
    # return (I * np.exp(-alpha * L) * L * delta_lambda * T_d * eta_d) / (2 * h * c)
    return (I * np.exp(-alpha * L) * L  * T_d * eta_d) / (2*h*delta_lambda*(10**(9)))

  def compute_C_b(I, alpha, L, delta_lambda, T_d, eta_d):
    return (I * (1 - np.exp(-2 * alpha * L)) / (2 * alpha) * delta_lambda * T_d * eta_d) / (2 * h * c)

  # Define the binary entropy function h(x)
  def binary_entropy(x):
    # print(x)
    if x == 0 or x == 1:
        return 0  # h(x) is 0 when x is 0 or 1
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

  # Function to compute P(Y_0)
  def compute_P_Y0(Q1, e1, f, Q_mu, E_mu):
    return Q1 * (1 - binary_entropy(e1)) - f * Q_mu * binary_entropy(E_mu)


  
  # Function to compute Q_mu
  def compute_Q_mu(Y0, eta, mu):
    return 1 - (1 - Y0) * np.exp(-eta * mu)

  # Function to compute E_mu
  def compute_E_mu(Y0, ed, eta, mu, Q_mu):
    return (Y0 / 2 + ed * (1 - np.exp(-eta * mu))) / Q_mu

  # Function to compute Q1
  def compute_Q1(Y1, mu):
    return Y1 * mu * np.exp(-mu)

  # Function to compute e1
  def compute_e1(Y0, ed, eta, Y1):
    return (Y0 / 2 + ed * eta) / Y1

  # Function to compute channel efficiency (eta)
  def compute_eta(eta_d, alpha, L):
    return (1 / 2) * eta_d * np.exp(-alpha * L)

  # Function to compute secret key generation rate (Rm)
  def compute_Rm(P_Y0, Ts):
    return max(0, P_Y0 / Ts)

  # Function to compute background yield (Y0)
  def compute_Y0(p_dc, p_m):
    return 1 - (1 - (p_dc + p_m))**2

  # Function to compute dark count probability (p_dc)
  def compute_p_dc(gamma_dc, T_d):
    return gamma_dc * T_d
  # Compute values



  # C_f = compute_C_f(I, alpha, L, delta_lambda, T_d, eta_d)
  C_f = 150
  # p_nm_FR = compute_p_nm( C_f)
  p_dc = compute_p_dc(gamma_dc, T_d)
  p_m=p_m*C_f
  Y0 = compute_Y0(p_dc, p_m)
  C_b = compute_C_b(I, alpha, L, delta_lambda, T_d, eta_d)
  # p_nm_BR = compute_p_nm( C_b, lambda_b, lambda_q)
  Q1 = compute_Q1(Y1, mu)
  eta = compute_eta(eta_d, alpha, L)
  Q_mu = compute_Q_mu(Y0, eta, mu)
  E_mu = compute_E_mu(Y0, ed, eta, mu, Q_mu)
  e1 = compute_e1(Y0, ed, eta, Y1)
  P_Y0 = compute_P_Y0(Q1, e1, f, Q_mu, E_mu)
  Rm = compute_Rm(P_Y0, Ts)

  # print(Q_mu)
  # print (Rm*10**(-7))
  return (Rm*10**(-7))
p_m_list=[5.28*1e-5]
total_keyrate=0
for p_m in p_m_list:
  total_keyrate+=SKR(p_m)

print(total_keyrate)