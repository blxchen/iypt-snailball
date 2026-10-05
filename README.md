# SnailLab — IYPT 2027, problem 3

A responsive multi-page simulation and experimental analysis workspace for the snail ball. The existing card layout, navigation, animation, and visual style are retained. Geometry/mass controls support smaller experimental balls; shell mass is adjustable in the model constants. Python now supplies a real numerical and measurement backend. Both frontend and backend have no third-party runtime dependencies; optional Google Fonts fall back to system fonts offline.

## Run

```sh
python3 serve.py
```

Open **http://localhost:8000**. If an older SnailLab server is still running, stop it and restart to enable the API. Use `--port 8080` to change the port. The server binds to localhost. Browser ES modules require HTTP rather than opening `index.html` directly.

## Live motion, liquid presets, and 3D view

The default liquid is **100,000 cSt silicone oil at 25°C**, using nominal density 970 kg/m³ and dynamic viscosity 97 Pa·s. Presets also include 10,000 and 1,000 cSt silicone oils, nominal glycerol, and water. Selecting a preset changes both viscosity and density, including fluid mass, buoyancy correction, drag, and Reynolds estimates. Silicone properties come from the [manufacturer's typical-properties table](https://api.pennwhite.co.uk/pdf/TDS%20Silicone%20Oil.pdf); glycerol is a nominal approximate example from the supplied experimental guide, and water uses representative 20°C values consistent with [IAPWS](https://www.iapws.org/relguide/LiquidWater.pdf). These are editable nominal properties, not fitted experimental constants. The viscosity slider is logarithmic; the numeric field uses Pa·s. No temperature interpolation or non-Newtonian law is applied.

Drag in the perspective view to orbit the camera, scroll to zoom, or use arrow keys / +/- / Home with the canvas focused. **Reset view** restores the camera. The section view fixes a side-on projection. Sphere geometry, core displacement, shell rotation, and ramp markings are projected from 3D world coordinates. This uses a perspective Canvas renderer rather than an external WebGL library. The camera follows the shell; ramp displacement and shell markings reflect signed model displacement, including recoil.

**Follow playback** progressively reveals all motion graphs during playback and scrubbing, with axes scaling to the revealed data. The local gap-flow profile updates at the current simulation time. Disable it to inspect the complete trajectory. Computation is performed in advance for deterministic playback; this is a live reveal of numerical results, not sensor acquisition. Changing parameters recomputes and restarts the trajectory, continuing playback if it was running. Summary cards describe the full computed run.

Every plotted graph has its own **PNG** download button. Downloads include the current rendered trace and a title/metadata strip. CSV scope can be the full computed run or only the played samples, with an interpolated current-time endpoint. CSV includes signed velocity, local gap velocity, and shear stress as well as the previous motion and energy variables.

## Whole-cavity Navier–Stokes preview

The fluid motion is now computed by `fluid.js`, a **two-dimensional incompressible Navier–Stokes solver** in a meridional slice of the cavity. `fluid-worker.js` runs it off the UI thread. `fluid-view.js` manages worker updates, replay, and parameter resets. Playback coalesces updates into one active worker request and the latest pending timestamp. Rewinding resets the generation and rejects old replies; worker failures leave mechanical playback available. Paused scenes and play-button icons update only when their state changes.

- Staggered MAC velocities and cell-centred pressure on a 32 × 32, 40 × 40 (default), or 56 × 56 grid.
- Semi-Lagrangian advection of the velocity field.
- Implicit viscosity using `nu = eta/rho`; conjugate-gradient solves of the discrete Helmholtz equations.
- Pressure projection using conjugate gradients and connected-region pressure gauges.
- Body acceleration equal to gravity minus shell translational acceleration, in the translating, nonrotating shell-centre frame.
- Rasterized no-slip boundaries: shell angular motion and core-centre translation come from the existing mechanical ODE. Core spin is prescribed zero because the ODE omits that degree of freedom.

Select **Tracer motion**, **Velocity arrows**, **Pressure map**, or **Liquid only** under the scene. Tracers follow the computed velocity with midpoint integration; they are passive visualization markers, not bubbles or an invented flow wave. They are reseeded when overtaken by a moving raster boundary. The cavity stays fully filled, so no free-surface sloshing is rendered. All field geometry is a 2D slice projected through the existing 3D camera.

**Flow CSV** exports the latest field snapshot (`x,y,u,v,pressure` in SI units), its actual calculation timestamp, viscosity/density, and diagnostics. Pressure has a zero-mean gauge per connected fluid region. The local gap-profile graph and `/api/flow` remain separate analytical calculations; they are not the whole-cavity field.

This is **one-way coupling**: the mechanical trajectory drives fluid boundaries, but fluid stress is not fed back into the shell or core equations. The displayed field therefore does not replace the reduced mechanical drag closure. It is a qualitative preview, not a fully coupled, converged three-dimensional snail-ball simulation. Thin films can be below grid resolution; stair-step moving boundaries can create disconnected pockets and mass-compatibility defects. The pressure RHS has its mean removed separately in each region so the Poisson solve is well posed. The unresolved boundary compatibility remains visible in divergence RMS rather than being hidden. Numerical diagnostics also expose pressure/diffusion solve residuals and the number of grid cells across the minimum film.

Scrubbing backward restarts the solver, and forward seeking integrates from the current field; tracers are hidden when field time differs from the mechanical scene by more than 0.06 s. The status shows calculation time/catch-up state. High-speed or fine-grid runs can take longer to catch up. These limitations are also documented in the mathematical-model page.

Numerical background: [Jos Stam (1999), Stable Fluids](https://doi.org/10.1145/311535.311548). The projection method is adapted here to staggered storage and moving raster masks; it is not a verbatim implementation of the paper.

## Measurement workflow

Open **Research notebook**:

1. Enter any timestamps and distances in the editable table, or import a CSV. Add or remove samples freely. Clock timestamps (`1:02.5`, `1:02:03.5`) and frame numbers (`120f`, using your FPS) are accepted. At least three samples with unique times are needed; irregular sample spacing and backward motion are supported.
2. Select metres, centimetres, or millimetres. Changing the table's distance unit converts existing distances, uncertainty, and position origin. CSV imports always use SI distances and optional SI velocity.
3. Record trial name, fluid, temperature, and whether this is a reference run. Set position/time uncertainty and time/position origins to align a recording with the model's release. Temperature is metadata: viscosity is not automatically adjusted.
4. Click **Analyze measurements** to compute measured velocity, acceleration, angular velocity, mean-velocity uncertainty, model RMSE, and graphs in Python.
5. Use **Measure a selected interval** for arbitrary timestamp endpoints or distance markers. Position is interpolated within the measured range; distance-marker mode selects successive first crossings, including backward motion.
6. Export the derived measured CSV or an HTML report containing raw rows, setup, summary, interval calculation, references, and notes.

A reference-run flag records provenance. It does not replace the separate analytical rigid-body reference in the simulation graph or automatically compare multiple experimental trials.

### Video measurements

Load a browser-compatible local video in the notebook. Select two points along the ramp, uphill first, and enter their real separation to calibrate pixels. Seek to arbitrary timestamps or step by the nominal FPS; click the shell centre to add a measurement row. Distances are signed projections along the calibrated ramp axis. Switch to diameter mode and click opposing shell edges to measure radius.

Use a stationary, perpendicular side-view camera with a calibration ruler in the motion plane. Perspective distortion and lens distortion are not corrected; tracking is manual, not automatic computer vision. Browser seeking and nominal FPS do not guarantee decoded-frame accuracy for variable-frame-rate videos. Scale changes affect future clicks; existing distance rows retain their original values. The measured radius is reported but never silently substitutes the simulation's radius. Videos stay in the browser and are not sent to Python.

### Python sampling

The **Data analysis** page has a Python model sampler with a custom duration (up to 300 s) and a list of custom timestamps. It recomputes the existing model and exports all interpolated sample variables in SI units. This separate calculation does not change the live simulation controls. A one-million-step limit rejects computationally excessive stiff configurations.

## Pages

- **Simulation:** shaded animated shell and core, perspective/section views, playback and scrubbing, live geometry, mass, viscosity, incline and duration controls.
- **Data analysis:** velocity, displacement, acceleration, shell/orbital angular speed, kinetic energy/dissipation, torque, power, phase portrait, numerical diagnostics, custom Python sampling, CSV/PNG exports.
- **Experiments:** parameter sweeps, sensitivity CSV, locally saved simulation configurations.
- **Mathematical model:** derivation, assumptions, constants, and limitations.
- **Research notebook:** custom timestamp/distance table, measured CSV, calibrated video measurements, uncertainty, interval calculations, measured motion graphs, notes and report.

The computed fluid field runs locally in the browser worker and is held in memory. Browser localStorage stores notes, measurement rows, setup, latest analysis, and saved simulation configurations. Local video and calibration are held only in memory. Measurement calculations send JSON to the Python server on your own machine; no external data service is used.

## Python API

All endpoints return JSON in SI units; errors return `{"error":"..."}` with a 4xx status.

- `GET /api/health`: server readiness/version.
- `POST /api/simulate`: `{"parameters":{"duration":2,"eta":4.5},"timestamps":[0,0.2,1,2]}`. Returns trajectory, interpolated custom samples, constants, integration diagnostics, and statistics.
- `POST /api/analyze`: `{"rows":[{"t":0,"x":0},{"t":0.5,"x":10},{"t":1,"x":25}],"distance_unit":"mm","sigma_x":1,"sigma_t":0.01,"radius_mm":35}`. Add `compare_model:true` and `parameters` for position/velocity RMSE on overlapping timestamps.
- `POST /api/flow`: `{"eta":97,"gap_mm":0.5,"u0":0,"u1":0.001,"pressure_gradient":0}`. Returns the analytic local steady Couette–Poiseuille profile, shear, flow rate, and dissipation. Boundary velocities are m/s and pressure gradient Pa/m. This is a local Stokes boundary-value problem, not global sphere CFD.
- `POST /api/measure`: measurement fields plus `mode:"time",t_start:0.2,t_end:0.8`, or `mode:"distance",x_start:5,x_end:20`. Marker distances use the chosen distance unit and recording coordinate system. Timestamp endpoints use the recording clock; the configured time origin is subtracted.

Optional analysis fields: `fps`, `time_offset`, `position_offset`, `trial_name`, `temperature_c`, `fluid`, `reference`. Optional per-row `sigma_x` uses the selected distance unit, `sigma_t` is seconds, and supplied `v` is always m/s.

### Headless Python use

```sh
python3 -m backend.cli simulate --timestamps 0,0.5,1 --output simulation.json
python3 -m backend.cli analyze measurements.csv --unit mm --fps 60 --sigma-x 1 --sigma-t 0.01 --output analysis.json
```

For simulation, `--parameters config.json` reads a JSON object with any model settings. Parameter conventions match the frontend: R/r/gap in mm, shell in g, eta in Pa·s, rho in kg/m³, angle/q0 in degrees, duration in seconds. The inner ball is a homogeneous solid: core_density is kg/m³, defaulting to nominal steel at 7850. Core mass in grams follows r and core_density; legacy core input is replaced with this calculated mass. Only drag=1 (Newtonian gap shear) is accepted. Missing settings use defaults.

## Calculations and limits

`backend/model.py` independently implements the same two-coordinate Lagrangian model as `physics.js`. Explicit RK4 uses a damping-dependent timestep; accumulated dissipation exposes energy-balance error. Python and JavaScript default statistics are verified against each other.

For position samples at unequal times, interior velocity uses a three-point quadratic derivative, endpoint velocity a first difference, and acceleration a local three-point quadratic second derivative (including at endpoints). Supplied velocities are retained. No smoothing is applied. Instantaneous derivative uncertainties propagate independent position errors with sample times held fixed; they do **not** include timing jitter or correlated calibration errors. Interval/mean velocity uncertainty includes first-order independent endpoint position and time errors. Interpolated intervals can share source samples; their covariance is not included. Angular velocity and acceleration use the no-slip assumption, not an independently observed rotation.

The inner ball has **selectable material density**: steel (default 7850 kg/m³), aluminium (2700), copper (8940), tungsten (19250), or custom measured density. Every choice assumes a homogeneous solid and uses `mc = core_density*4*pi*r³/3`. Each preset links to its property source. At the default radius 23 mm it weighs **400.08 g**. Mass follows radius and selected density automatically. The preview uses material-specific shading. Density affects mass, buoyancy, inertia, ground forces and the trajectory; it is retained in saved configurations, CSV and reports. Presets are nominal and should be checked for the actual alloy. The current heavy-core, fixed-orbit model requires core density greater than liquid density; floating cores need a different orbit/contact model.

The corrected mechanical model distinguishes buoyant mass `m* = mc − md` from relative inertial mass `mi = mc + md²/mf`. The latter follows by expanding steel translation and the mean-fluid-centre kinetic energy. The shell uses its exact finite-thickness moment of inertia. Clockwise shell rotation and counterclockwise core-centre angle give relative rate `qdot + xdot/R`; both damping forces oppose it.

```text
T = ½(M + Is/R²) v² + m*l*cos(q)*v*w + ½mi*l²*w²
U = −M*g*x*sin(alpha) − m*g*l*cos(q−alpha)
c = eta*l²*2*pi*r²*integral(-1..1, (1+mu²)/(2*H(mu)) dmu)
H(mu) = sqrt(Ri² − l²*(1−mu²)) − l*mu − r
P = c*(w + v/R)² >= 0; d(T+U)/dt = −P
```

The gap-shear integral uses 256 midpoint panels. The previous additive bulk drag and empirical confinement multiplier have been removed. The closure estimates tangential shear; it omits pressure-driven resistance and independent core-spin shear. The default corrected trajectory does not reverse; displaced initial angles such as q0=30° can produce recoil from the equations. No random force, waveform, velocity clamp, or fitted reversal drives the animation.

The fixed orbit, fully filled cavity, neglected fluid circulation inertia, omitted free core spin, and one-way fluid preview remain explicit approximations. Ground friction and normal force are derived from total centre-of-mass acceleration; CSV exports them and the sampled required static-friction coefficient. The app does not integrate slip or lift-off. See [PHYSICS.md](PHYSICS.md) for the full derivation, sign conventions, units, boundary conditions, sources and validation limits.

`backend/flow.py` solves the steady local parallel-gap reduction of incompressible Navier–Stokes, `eta*u'' = dp/ds`, with specified boundary velocities. The live profile uses zero imposed pressure gradient and relative velocity `l*(qdot+omega)`. A full 3D moving-boundary Navier–Stokes solution is **not implemented**. The model can accelerate on some inclines. The rigid graph reference is a separate concentric, locked-core case.

## Supplied references

- [2027 IYPT reference kit, Problem 3 bibliography](https://studylib.net/doc/28702133/fdd-2027-iypt-reference-kit): context on centre of mass, viscosity, inertia, and nested-cylinder research. The kit describes itself as background material, not an official binding manual.
- [PhysicsMe experimental guidance](https://physicsme.ir/en/iypt/2027/snail-ball-en/): side-view filming, timed ramp descents, ordinary-ball references, and viscosity/incline comparisons. Example viscosity values are approximate and not automatically treated as measured constants.
- [Supplied YouTube short](https://www.youtube.com/shorts/olrLdwTAqfQ): retrieval failed, so no clip data or unverified content is used to tune reversals. The link is available in the reference panel.
- [Supplied YouTube reference](https://www.youtube.com/watch?v=5CdUEl9HgQw): linked for user review. Retrieval failed; no video content, quantitative data, or physical claims are inferred from it.
- [Balmforth, Bush, Vener & Young (2007), JFM 590, 295–318](https://pordlabs.ucsd.edu/wryoung/reprintPDFs/snailball.pdf), DOI 10.1017/S0022112007008051: primary background for nested-cylinder rocking/rolling and lubrication. The full published cylinder theory is not implemented here.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 verify.py  # macOS: uses the system JavaScriptCore library
python3 tests/check_http.py  # optional: checks a running server
```

Python tests additionally verify unscripted recoil, nonnegative dissipation, gap-dependent resistance, solid steel mass/inertia and cubic radius scaling, direct mean-fluid kinetic energy, positive mass matrices, instantaneous energy and damping signs, co-rotation, horizontal rest, deterministic repeatability, ground-contact force consistency, liquid mass changes, the local Stokes boundary conditions, and the pressure-balance equation. JavaScript checks cover orbit/zoom/reset, progressively revealed graphs, CSV scopes, and PNG export. Python tests cover irregular sampling, unit/origin conversion, frame and clock timestamps, backward motion, uncertainty, interval interpolation, custom model sampling, energy balance, viscosity sensitivity, validation, and HTTP-handler routing/errors. The JavaScriptCore harness covers syntax, five-page templates, chart/scene drawing, saving/sweeps, CSV import, video calibration/position/radius, and Python/JavaScript numerical parity. It is not a real-browser visual or video-decoder test. Fluid checks also exercise hydrostatic rest, moving-wall forcing, implicit-solve residuals, pressure projection relative to the raster mass-compatibility floor, and the worker reset/advance/rewind protocol. Playback regression checks cover rapid toggles, both play controls, restart/end replay, seeks, stable idle buttons, bounded worker queues, stale-response rejection, failure handling, and reset during an active solve. Fluid stress checks include a full default run, water, and the fine grid. HTTP checks verify JavaScript MIME types and module cache revalidation.
