import numpy as np
from scipy.linalg import expm, solve_discrete_are
import quadprog


# ── System parameters (must match cart_pole_dynamics.py) ──────────────────────
M  = 1.0;  m = 0.3;  L = 0.8;  g = 9.81
n  = 4     # states:  [x, x_dot, theta, theta_dot]
nu = 1     # inputs:  [F]

# ── MPC design parameters ─────────────────────────────────────────────────────
N  = 20    # prediction horizon (steps)
dt = 0.02  # timestep — must match simulation (50 Hz)

MAX_FORCE = 20.0   # hard force limit (N)
X_LIMIT   = 1.8    # hard cart position limit (m) — tighter than physical wall

# State cost: penalises [x, x_dot, theta, theta_dot] deviations
# Control cost: penalises large forces
Q = np.diag([5.0, 0.1, 10.0, 1.0])
R = np.array([[0.01]])


# ── 1. Linearised continuous model  ẋ = A_c x + B_c u ────────────────────────
# Derived from Lagrangian mechanics, linearised around upright (theta=0).
# A_c[3][2] is positive → upright is unstable (the term we're fighting).

A_c = np.array([
    [0,  1,               0,  0],
    [0,  0,        -m*g/M,  0],
    [0,  0,               0,  1],
    [0,  0,  (M+m)*g/(M*L),  0],
])

B_c = np.array([[0], [1/M], [0], [-1/(M*L)]])


# ── 2. Discretise via Zero-Order Hold  x_{k+1} = A_d x_k + B_d u_k ──────────
# Augmented matrix exponential handles singular A_c cleanly.
# Here we are looking at the discretization  of the linearzied dynamics.

M_aug          = np.zeros((n + nu, n + nu))
M_aug[:n, :n]  = A_c
M_aug[:n, n:]  = B_c
M_d = expm(M_aug * dt)

A_d = M_d[:n, :n]
B_d = M_d[:n, n:]


# ── 3. Terminal cost P  via DARE ──────────────────────────────────────────────
# P = LQR cost-to-go: penalises the terminal state x_N as if LQR runs forever
# from that point. Connects the finite MPC horizon to infinite-horizon optimality.

P = solve_discrete_are(A_d, B_d, Q, R)


# ── 4. Prediction matrices  X = A_pred x_0 + B_pred U ────────────────────────
# Unroll N steps of dynamics into one matrix equation.
# B_pred[k, j] = A_d^(k-j) @ B_d  (input j propagates k-j steps to reach state k+1)

A_powers = [np.eye(n)]
for _ in range(N):
    A_powers.append(A_powers[-1] @ A_d)

A_pred = np.zeros((N * n, n))
B_pred = np.zeros((N * n, N * nu))

for k in range(N):
    A_pred[k*n:(k+1)*n, :] = A_powers[k + 1]
    for j in range(k + 1):
        B_pred[k*n:(k+1)*n, j*nu:(j+1)*nu] = A_powers[k - j] @ B_d


# ── 5. QP cost matrices  (offline — fixed forever) ───────────────────────────
# H is the Hessian of the QP objective. Never changes → computed once here.
# g = BtQA @ x_0 is the only thing recomputed each timestep.

Q_bar = np.zeros((N * n, N * n))
R_bar = np.zeros((N * nu, N * nu))
for k in range(N):
    Q_bar[k*n:(k+1)*n, k*n:(k+1)*n] = Q if k < N - 1 else P
    R_bar[k*nu:(k+1)*nu, k*nu:(k+1)*nu] = R

H    = B_pred.T @ Q_bar @ B_pred + R_bar
BtQA = B_pred.T @ Q_bar @ A_pred   # precomputed for fast g = BtQA @ x0


# ── 6. Constraint matrices  (offline — state bounds become linear in U) ───────
# Cart position at step k = first element of x_k.
# E_bar extracts cart position from all N predicted states simultaneously.
# EB @ U is the contribution of control inputs to cart position.
# EA @ x0 is the "free response" — where the cart drifts with zero force.

E_bar = np.zeros((N, N * n))
for k in range(N):
    E_bar[k, k*n] = 1.0       # select x_cart from state k

EB = E_bar @ B_pred            # constant — offline
EA = E_bar @ A_pred            # constant — offline


# ── 7. Online MPC solve ───────────────────────────────────────────────────────

_U_prev = np.zeros(N * nu)     # warm-start cache

def mpc_force(state):
    global _U_prev
    x0 = np.asarray(state, dtype=float)

    # Linear term — updates every call
    g = BtQA @ x0

    # State constraint right-hand sides
    free    = EA @ x0
    d_upper = X_LIMIT * np.ones(N) - free
    d_lower = X_LIMIT * np.ones(N) + free

    # quadprog format: minimise  0.5 U^T G U - a^T U
    # subject to  C^T U >= b
    #
    # Our objective:  0.5 U^T H U + g^T U  →  G=H, a=-g
    #
    # Constraints stacked as C^T U >= b:
    #   Force lower:     I U  >= -F_max  →  C^T row = +I,  b = -F_max
    #   Force upper:    -I U  >= -F_max  →  C^T row = -I,  b = -F_max
    #   Position upper: -EB U >= -d_upper →  C^T row = -EB, b = -d_upper
    #   Position lower:  EB U >= -d_lower →  C^T row = +EB, b = -d_lower

    I_N = np.eye(N * nu)
    C_T = np.vstack([ I_N, -I_N, -EB,      EB      ])
    b   = np.hstack([-MAX_FORCE * np.ones(2 * N * nu),
                     -d_upper, -d_lower])

    try:
        U_sol = quadprog.solve_qp(H, -g, C_T.T, b)[0]
    except ValueError:
        # QP infeasible (e.g. cart already past wall) — fall back to warm start
        U_sol = _U_prev

    _U_prev = U_sol
    return float(np.clip(U_sol[0], -MAX_FORCE, MAX_FORCE))


# ── 8. Switch helpers ─────────────────────────────────────────────────────────

def should_use_mpc(state):
    _, _, theta, theta_dot = state
    theta_w = (theta + np.pi) % (2 * np.pi) - np.pi
    return abs(theta_w) < np.radians(25) and abs(theta_dot) < 3.0

def mpc_fallback_needed(state):
    _, _, theta, _ = state
    theta_w = (theta + np.pi) % (2 * np.pi) - np.pi
    return abs(theta_w) > np.radians(35)