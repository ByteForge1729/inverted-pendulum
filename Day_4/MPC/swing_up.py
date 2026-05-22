"""
──────────────────────────────────────────────────────────────────────
SIGN CONVENTION (matches simulation code)
    θ = 0     → upright   (unstable equilibrium)
    θ = ±π   → hanging    (stable equilibrium)

    This is the OPPOSITE of Åström's paper convention.

ENERGY FORMULA (simplified pendulum energy, Åström form)
    E = ½mL²θ̇² + mgL·cos(θ)

    At upright  (θ=0,  θ̇=0): E* = +mgL   ← target
    At hanging  (θ=π,  θ̇=0): E  = −mgL
    Energy deficit at hanging:  E − E* = −2mgL  (negative → need to add energy)

LYAPUNOV ANALYSIS
    V  = ½(E − E*)²
    V̇  = (E − E*) · Ė
    Ė  = −mL · ẍ · θ̇ · cos(θ) · m/(M+m)   [derived from EOM, this convention]

    For V̇ < 0:  (E−E*) · F · θ̇ · cos(θ) > 0
    ⟹  sign(F) = sign( (E−E*) · θ̇ · cos(θ) )

CONTROL LAW
    F = clip( k · (E − E*), ±F_max ) · sign( θ̇ · cos(θ) )

GAIN CHOICE  k = F_max / (m·g·L)
──────────────────────────────────────────────────────────────────────
"""

import numpy as np

# ── System parameters (must match cart_pole_dynamics.py exactly) ──────────────
M = 1.0     # cart mass   (kg)
m = 0.3     # pole mass   (kg)
L = 0.8     # pole length (m)
g = 9.81    # gravity     (m/s²)

# ── Derived constants ─────────────────────────────────────────────────────────
MAX_FORCE = 20.0                    # actuator limit (N)
E_STAR    = m * g * L               # target energy at upright = +2.354 J

# ── Gain: k = F_max / (mgL)  ──────────────────────────────────────────────────
k_e = MAX_FORCE / (m * g * L)       # ≈ 8.50 N/J

# ── Wall penalty ──────────────────────────────────────────────────────────────
# Full corrective force when cart is exactly at the boundary.
X_LIMIT  = 2.0                      # cart travel limit (m from centre)
k_wall   = MAX_FORCE / X_LIMIT      # = 10.0 N/m

# ── Handoff parameters ────────────────────────────────────────────────────────
ANGLE_THRESHOLD    = np.radians(25)          # rad  ≈ 25° from upright
VELOCITY_THRESHOLD = 3.0            # rad/s — pole must be arriving, not flying

# ── Dead-zone threshold ───────────────────────────────────────────────────────
# Below this |θ̇|, treat as "at rest" and apply a symmetry-breaking kick.
REST_THRESHOLD = 1e-2               # rad/s


# ── System characterisation on import ─────────────────────────────────────────
_n = MAX_FORCE / ((M + m) * g)
if _n >= 2.0:
    _regime = f"single swing, 2 switches (time-optimal regime)"
elif _n >= 4 / 3:
    _regime = f"single swing, 3 switches possible"
elif _n >= 1 / np.sqrt(3):
    _regime = f"2 swings needed"
else:
    _regime = f"multi-swing, may be slow"
print(f"[swing_up] n = F_max/((M+m)g) = {_n:.3f}  →  {_regime}")
print(f"[swing_up] k_e = {k_e:.3f} N/J  |  E* = {E_STAR:.3f} J  |  sat boundary = {E_STAR:.3f} J")


# ─────────────────────────────────────────────────────────────────────────────
def pendulum_energy(state):
    _, _, theta, theta_dot = state
    return 0.5 * m * L**2 * theta_dot**2 + m * g * L * np.cos(theta)


# ─────────────────────────────────────────────────────────────────────────────
def swing_up_force(state):
    """
    Returns:
    float : force to apply to cart (N), clamped to ±MAX_FORCE
    """
    x, _, theta, theta_dot = state

    # Current energy and error
    E_err = pendulum_energy(state) - E_STAR

    # ── Case 1: near rest ─────────────────────────────────────────────────────
    # θ̇ ≈ 0: sign(θ̇·cos(θ)) is undefined. Apply a fixed kick.
    # Sign chosen so the kick moves in a direction that the main law
    # will reinforce once θ̇ becomes nonzero.
    if abs(theta_dot) < REST_THRESHOLD:
        F = -np.sign(E_err) * 1.0      # gentle kick, ≈ 5% of F_max

    # ── Case 2: near horizontal ───────────────────────────────────────────────
    # cos(θ) ≈ 0: the cart force cannot change pendulum energy here
    # (Controllability lost at θ = ±π/2).
    # Coast through — momentum carries the bob over the top.
    elif abs(np.cos(theta)) < 0.05:
        F = 0.0

    # ── Case 3: normal operation ──────────────────────────────────────────────
    else:
        coupling = theta_dot * np.cos(theta)

        # Saturated magnitude (proportional to energy error, bounded)
        F_magnitude = np.clip(k_e * E_err, -MAX_FORCE, MAX_FORCE)

        # Direction: sign of coupling ensures V̇ ≤ 0
        F = F_magnitude * np.sign(coupling)

    # ── Wall penalty ──────────────────────────────────────────────────────────
    # Soft restoring force when cart approaches track boundaries.
    # Proportional to overshoot past X_LIMIT.
    if x > X_LIMIT:
        F -= k_wall * (x - X_LIMIT)
    elif x < -X_LIMIT:
        F -= k_wall * (x + X_LIMIT)

    return float(np.clip(F, -MAX_FORCE, MAX_FORCE))


# ─────────────────────────────────────────────────────────────────────────────
def should_handoff(state):
    """
    Returns True when the pole is inside the LQR region of attraction.

    Two conditions must both be satisfied:

      1. Angle:    |θ_wrapped| < ANGLE_THRESHOLD   (≈ 20° from upright)
      2. Velocity: |θ̇|        < VELOCITY_THRESHOLD (arriving, not passing through)

    The velocity condition is non-negotiable. A pole crossing 20° at
    high angular velocity is almost certainly outside the LQR basin —
    it would need to decelerate faster than LQR can manage.
    """
    _, _, theta, theta_dot = state

    # Wrap θ into [−π, π] centred on upright (θ = 0 in our convention)
    theta_w = (theta + np.pi) % (2 * np.pi) - np.pi

    angle_ok    = abs(theta_w)    < ANGLE_THRESHOLD
    velocity_ok = abs(theta_dot)  < VELOCITY_THRESHOLD

    return angle_ok and velocity_ok