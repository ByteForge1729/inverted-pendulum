# Tutorials

Short, applied tutorials for every Python library used in this project. Each one assumes you already know Python (loops, functions, lists) but has **never** opened the library before. Every function gets a one-line description, a full signature, a minimal example, and a pendulum-flavoured example. No walls of text.

## The tutorials

| # | Library          | What it covers                                                                   | Format | Read time |
|---|------------------|----------------------------------------------------------------------------------|--------|-----------|
| 1 | numpy            | arrays, math functions, broadcasting, save/load with `.npz`                      | .ipynb | 20 min    |
| 2 | scipy            | `solve_ivp` for ODEs — signature, method choice, examples up to cart-pole         | .ipynb | 25 min    |
| 3 | sympy            | symbols, `diff`, `solve`, `subs`, `lambdify`, deriving a pendulum EOM            | .ipynb | 30 min    |
| 4 | matplotlib       | figure/axes model, plotting, subplots, `FuncAnimation`, phase portraits          | .ipynb | 30 min    |
| 5 | pygame           | game loop, draw primitives, events, fonts, real-time physics integration         | .md    | 20 min    |
| 6 | python-control   | state-space, LQR, poles, stability — applied to the linearised pendulum          | .ipynb | 25 min    |
| 7 | manim            | mathematical animation engine — "compute in Python, animate in Manim" workflow   | .md    | 30 min    |

## How to use this as a cheat sheet

Every tutorial **ends with a Functions Used In This Project quick-reference table**. Once you've read a tutorial through, the only thing you'll come back for is that table. Bookmark the bottom of each notebook.

When you want to look up "what were the arguments to `solve_ivp` again?", don't re-read the tutorial — jump to its quick-reference table.

## Recommended order if you're learning from scratch

1. **numpy** — everything else is built on it
2. **matplotlib** — you'll want to see what your arrays look like
3. **scipy** — once you can plot, simulate something
4. **sympy** — derive an equation, lambdify it, hand it to scipy
5. **pygame** — make it move in real time
6. **python-control** — design a controller for it
7. **manim** — render the explainer video

## If you just need one function

Open the relevant tutorial's quick-reference table at the bottom and Ctrl-F. The tables list every function used in this project with its signature and a one-line description.
