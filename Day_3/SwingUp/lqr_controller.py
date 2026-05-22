import sympy as sp
import numpy as np
from scipy.linalg import solve_continuous_are

# =====================================================
# SYSTEM PARAMETERS — change these to retune
# =====================================================
M_val = 1.0
m_val = 0.3
L_val = 0.8
g_val = 9.81

# maximum acceptable deviations (Bryson's Rule)
x_max   = 2.0
xd_max  = 5.0
th_max  = 20 * np.pi/180
thd_max = 10 * np.pi/180
F_max   = 15.0

# =====================================================
# SYMBOLIC EOM
# =====================================================
x, xd, th, thd = sp.symbols('x xd th thd')
F = sp.symbols('F')
M, m, L, g = sp.symbols('M m L g')

xdd, thdd = sp.symbols('xdd thdd')

T_cart = sp.Rational(1,2) * M * xd**2
vx_pole = xd + L * thd * sp.cos(th)
vy_pole = -L * thd * sp.sin(th)
T_pole  = sp.Rational(1,2) * m * (vx_pole**2 + vy_pole**2)
T = sp.simplify(T_cart + T_pole)
V = m * g * L * sp.cos(th)
Lag = T - V

dL_dxd  = sp.diff(Lag, xd)
dL_dx   = sp.diff(Lag, x)
dt_dL_dxd = (dL_dxd.diff(x)*xd + dL_dxd.diff(xd)*xdd +
             dL_dxd.diff(th)*thd + dL_dxd.diff(thd)*thdd)
eq1 = sp.Eq(dt_dL_dxd - dL_dx, F)

dL_dthd = sp.diff(Lag, thd)
dL_dth  = sp.diff(Lag, th)
dt_dL_dthd = (dL_dthd.diff(x)*xd + dL_dthd.diff(xd)*xdd +
              dL_dthd.diff(th)*thd + dL_dthd.diff(thd)*thdd)
eq2 = sp.Eq(dt_dL_dthd - dL_dth, 0)

sol      = sp.solve([eq1, eq2], [xdd, thdd])
xdd_expr = sp.simplify(sol[xdd])
thdd_expr = sp.simplify(sol[thdd])

# =====================================================
# LINEARIZATION — Jacobians at equilibrium
# =====================================================
f = sp.Matrix([xd, xdd_expr, thd, thdd_expr])

A_sym = f.jacobian([x, xd, th, thd])
B_sym = f.jacobian([F])

eq_point = {x: 0, xd: 0, th: 0, thd: 0, F: 0}
A_lin = sp.simplify(A_sym.subs(eq_point))
B_lin = sp.simplify(B_sym.subs(eq_point))

# =====================================================
# SUBSTITUTE NUMERICAL VALUES
# =====================================================
params = {M: M_val, m: m_val, L: L_val, g: g_val}

A_num = np.array(A_lin.subs(params).tolist(), dtype=float)
B_num = np.array(B_lin.subs(params).tolist(), dtype=float)

# =====================================================
# LQR — solve Riccati → compute K
# =====================================================
Q = np.diag([
    1/x_max**2,
    1/xd_max**2,
    1/th_max**2,
    1/thd_max**2
])
R = np.array([[1/F_max**2]])

P = solve_continuous_are(A_num, B_num, Q, R)
K = np.linalg.inv(R) @ B_num.T @ P

# =====================================================
# CONTROL LAW
# =====================================================
def lqr_force(state):
    """
    state = [x, xdot, theta, thetadot]
    returns scalar force F = -Kx
    """
    return float(-K @ np.array(state))


if __name__ == "__main__":
    print("K =", np.round(K, 4))
    print("A =")
    print(np.round(A_num, 4))
    print("Closed-loop eigenvalues:")
    print(np.linalg.eigvals(A_num - B_num @ K))