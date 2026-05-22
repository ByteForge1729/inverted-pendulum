using DifferentialEquations, Plots

# Parameters
g  = 9.81   # gravity (m/s²)
L  = 1.0    # pendulum length (m)
b  = 0.4    # damping coefficient
A  = 0.0    # driving amplitude (set > 0 for forced oscillation)
ω  = 2.0    # driving frequency (rad/s)

p = (g, L, b, A, ω)  # pack parameters

# ODE definition
function pendulum!(du, u, p, t)
    g, L, b, A, ω = p
    θ, ω_dot = u[1], u[2]
    du[1] = ω_dot
    du[2] = -b * ω_dot - (g/L) * sin(θ) + A * cos(ω * t)
end

# Initial conditions: θ₀ = 45°, ω₀ = 0
u0    = [π/4, 0.0]
tspan = (0.0, 20.0)

# Solve
prob = ODEProblem(pendulum!, u0, tspan, p)
sol  = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8)

# Plot angle over time
plot(sol, idxs=(0,1),
    xlabel="Time (s)", ylabel="θ (rad)",
    title="Simple Pendulum", label="θ(t)", lw=2)

# 1. Define the time steps for the animation
frames = 0:0.1:20.0  # From 0 to 20s in 0.1s increments

# 2. Create the animation object
anim = @animate for t in frames
    # Get the state at time 't' (Julia interpolates automatically!)
    u = sol(t)
    θ = u[1]
    
    # Calculate the (x, y) coordinates of the pendulum bob
    x = L * sin(θ)
    y = -L * cos(θ)
    
    # Plot the "arm" and the "bob"
    # We set xlim and ylim so the camera stays still
    plot([0, x], [0, y], lw=3, label="", xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), 
         aspect_ratio=:equal, title="Time: $(round(t, digits=2))s")
    scatter!([x], [y], markersize=10, label="Bob", color=:red)
end