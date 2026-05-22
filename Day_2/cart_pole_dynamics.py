# cart_pole_dynamics.py
# shared dynamics — imported by both notebook and pygame

import numpy as np

# system parameters
M_VAL = 1.0    # cart mass  (kg)
m_VAL = 0.3    # pole mass  (kg)
L_VAL = 0.8    # pole length (m)
g_VAL = 9.81   # gravity    (m/s²)

def dynamics_num(state, F=0.0):
    """
    Numerically evaluate cart-pole equations of motion.
    state : [x, x_dot, theta, theta_dot]
    F     : applied horizontal force on cart (N)
    returns: [x_dot, x_ddot, theta_dot, theta_ddot]
    """
    x, xd, th, thd = state
    M, m, L, g = M_VAL, m_VAL, L_VAL, g_VAL

    sin_t  = np.sin(th)
    cos_t  = np.cos(th)
    denom  = M + m * sin_t**2

    x_ddot  = (F - m * g * sin_t * cos_t
                 + m * L * thd**2 * sin_t) / denom

    th_ddot = ((M + m) * g * sin_t
                - m * L * thd**2 * sin_t * cos_t
                - F * cos_t) / (L * denom)

    return np.array([xd, x_ddot, thd, th_ddot])


def rk4_step(state, F, dt):
    """
    One Runge-Kutta 4th order step.
    Advances state by dt seconds under force F.
    """
    k1 = dynamics_num(state,        F)
    k2 = dynamics_num(state + k1 * dt/2, F)
    k3 = dynamics_num(state + k2 * dt/2, F)
    k4 = dynamics_num(state + k3 * dt,   F)
    return state + (k1 + 2*k2 + 2*k3 + k4) * dt / 6