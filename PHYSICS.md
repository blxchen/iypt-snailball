# Snail Ball — equations, assumptions and evidence

The **Mathematical model** page typesets these equations with native MathML. The exported HTML report includes the same mathematical notation and source notes. Neither needs an external equation-rendering service.

This is a reduced mechanical model with a separate, one-way two-dimensional fluid preview. Published research motivates the approach; it does not validate the app's approximate spherical resistance law.

## 1. Notation and units

Internal calculations use SI units. User inputs in millimetres, grams and degrees are converted before integration. A dot denotes differentiation with respect to time.

| Symbol | Meaning | SI unit |
|---|---|---|
| $R, R_i, r$ | Outer radius, cavity radius, solid-ball radius | m |
| $\delta, h, \ell$ | Shell thickness, prescribed minimum film, orbit radius | m |
| $x, \dot x, \ddot x$ | Shell displacement, velocity, acceleration downhill | m, m/s, m/s² |
| $q, \dot q, \ddot q$ | Core-centre angle, orbital rate, orbital acceleration | rad, rad/s, rad/s² |
| $\omega$ | Clockwise shell angular speed | rad/s |
| $s$ | Relative orbital angular rate | rad/s |
| $\rho_c, \rho_f$ | Homogeneous core density, liquid density | kg/m³ |
| $m_c, m_d, m_f$ | Core, displaced-liquid, remaining-liquid masses | kg |
| $m^*, m_{\mathrm I}$ | Buoyant mass, relative inertial mass | kg |
| $I_s, I_c$ | Shell and solid-core moments of inertia | kg·m² |
| $\eta, c$ | Dynamic viscosity, orbital resistance | Pa·s, kg·m²/s |
| $T, U, P$ | Kinetic energy, potential energy, dissipated power | J, J, W |
| $\alpha, g$ | Incline angle, gravitational acceleration | rad, m/s² |

Positive $x$ points downhill, while the transverse coordinate points outward normal to the ramp. Positive $q$ rotates the core-centre vector counterclockwise from the downward ramp normal. Positive shell speed $\omega$ is clockwise. Thus

$$
\omega=\frac{\dot x}{R},\qquad s=\dot q+\omega.
$$

Co-rotation of the core centre with the shell means $\dot q=-\omega$, so $s=0$. Here $s$ is an angular rate; bold $\mathbf u$ below denotes fluid velocity.

## 2. Geometry and material mass

For a full cavity and a prescribed minimum film thickness,

$$
R_i=R-\delta,\qquad \ell=R_i-r-h>0,\qquad \delta=1\ \mathrm{mm}.
$$

$$
V_c=\frac{4\pi r^3}{3},\qquad V_f=\frac{4\pi}{3}(R_i^3-r^3).
$$

$$
m_c=\rho_c V_c,\qquad m_d=\rho_f V_c,\qquad m_f=\rho_f V_f,
\qquad M=m_s+m_c+m_f.
$$

The core is a homogeneous, rigid solid. Mass follows radius and `core_density`; legacy independent `core` input is replaced with the calculated mass. Steel remains the default: nominal 7850 kg/m³ gives approximately **400.08 g** at $r=23$ mm. Aluminium, copper, tungsten and custom measured density are also available. Nominal density is not a measurement of a particular alloy or porous/composite ball; a nonuniform core needs a different inertia model.

Exact uniform spherical-shell inertia and solid-sphere inertia are

$$
I_s=\frac{2m_s}{5}\frac{R^5-R_i^5}{R^3-R_i^3},
\qquad I_c=\frac{2}{5}m_c r^2.
$$

The reduced mechanics does not integrate free core spin. $I_c$ is used in the separate locked rigid reference.

**Status:** direct geometric derivation. The fixed orbit omits settling, changing film thickness, contact evolution and surface roughness dynamics.

## 3. Buoyancy and relative inertia

Define the core-centre displacement relative to the shell as

$$
\mathbf e=\ell(\sin q,-\cos q),
\qquad \dot{\mathbf e}=\ell\dot q(\cos q,\sin q).
$$

For a full uniform cavity minus the displaced sphere, the mean liquid centre relative to the shell is $-(m_d/m_f)\mathbf e$. Therefore its mean velocity is $(\dot x,0)-(m_d/m_f)\dot{\mathbf e}$.

Expanding core and mean-liquid translational kinetic energy gives two distinct masses:

$$
m^*=m_c-m_d,\qquad m_{\mathrm I}=m_c+\frac{m_d^2}{m_f}.
$$

Buoyant mass $m^*$ appears in gravity and the velocity cross term; it is **not** the relative inertial mass $m_{\mathrm I}$. With

$$
A=M+\frac{I_s}{R^2},\qquad B=m^*\ell\cos q,\qquad D=m_{\mathrm I}\ell^2,
$$

we obtain

$$
T=\frac12 A\dot x^2+B\dot x\dot q+\frac12D\dot q^2,
\qquad
U=-Mgx\sin\alpha-m^*g\ell\cos(q-\alpha).
$$

**Status:** sphere-specific derivation inspired by the buoyancy/mean-liquid inertia treatment in [Balmforth et al., §2.1, equations (2.1)–(2.2)](https://personal.math.ubc.ca/~njb/Research/sbx1.pdf). Their system uses cylinders. Internal liquid circulation energy is omitted here, so the reduced kinetic energy is not the complete fluid kinetic energy.

## 4. Local gap-shear approximation

Let $\mu$ be the cosine of the angle from the nearest-gap axis. The radial surface separation is

$$
H(\mu)=\sqrt{R_i^2-\ell^2(1-\mu^2)}-\ell\mu-r.
$$

Approximate local tangential shear dissipates $\eta|U_t|^2/H$ per unit surface area. Azimuthal averaging of the tangential projection of relative centre-translation speed $\ell s$ gives $(1+\mu^2)/2$. Integrating over the spherical surface gives

$$
c=2\pi\eta\ell^2r^2\int_{-1}^{1}\frac{1+\mu^2}{2H(\mu)}\,d\mu.
$$

The Rayleigh dissipation function and resisting generalized forces are

$$
\mathcal R=\frac12cs^2,\qquad P=cs^2\ge0,
\qquad Q_x=-\frac{cs}{R},\qquad Q_q=-cs.
$$

**Status:** an explicitly approximate closure derived for this app, not a published exact eccentric-sphere resistance. It omits pressure-driven resistance and independent core-spin/surface-rotation shear. A thin minimum film supports a local near-gap interpretation, not quantitative accuracy over the entire sphere. The integral uses 256 midpoint panels; no fitted confinement multiplier or extra bulk-drag term is added. Only `drag=1` is accepted.

## 5. Equations integrated by the solver

Using $L=T-U$ and $Q_j=-\partial\mathcal R/\partial\dot z_j$ in Euler–Lagrange equations,

$$
\frac{d}{dt}\frac{\partial L}{\partial\dot z_j}
-\frac{\partial L}{\partial z_j}=Q_j,
\qquad (z_1,z_2)=(x,q),
$$

gives

$$
\begin{aligned}
A\ddot x+B\ddot q
 &=Mg\sin\alpha+m^*\ell\sin q\,\dot q^2-\frac{cs}{R},\\
B\ddot x+D\ddot q
 &=-m^*g\ell\sin(q-\alpha)-cs.
\end{aligned}
$$

**Status:** directly derived for this model using the analytical-mechanics framework described in [MIT Dynamics, Lecture 20](https://ocw.mit.edu/courses/16-07-dynamics-fall-2009/resources/mit16_07f09_lec20/). Both `physics.js` and `backend/model.py` integrate these equations. Initial conditions are $x=\dot x=\dot q=0$ and the selected initial angle $q_0$.

No random force, waveform, fitted terminal speed or scripted reversal drives the animation. Displaced initial angles can cause recoil through the coupled coordinates.

## 6. Energy and numerical resolution

The equations imply

$$
\frac{d}{dt}(T+U)=-P,
\qquad E_{\mathrm{res}}=T+U+\int_0^t P\,dt-E_0.
$$

RK4 integrates motion; trapezoidal integration accumulates dissipation. Conservative bounds on damping and gravitational oscillation rates set the numerical step:

$$
\Delta_{\min}=AD-(m^*\ell)^2,
$$

$$
\lambda_{\max}=\frac{c(A+D/R^2+2m^*\ell/R)}{\Delta_{\min}},
\qquad \Omega_{\max}=\sqrt{\frac{m^*g\ell A}{\Delta_{\min}}},
$$

$$
\Delta t\le\min\left(0.002\ \mathrm s,
\frac{0.08}{\lambda_{\max}},\frac{0.08}{\Omega_{\max}}\right).
$$

A zero damping rate removes that step restriction. The factor 0.08 is a numerical resolution target, not a physical drag coefficient. Computations requiring more than one million steps are rejected. Energy residuals and convergence checks assess numerical implementation, not experimental correctness of the closure.

## 7. Stationary orbit and the flat velocity trace

For positive downhill incline and $c>0$, setting both accelerations and $\dot q$ to zero gives

$$
MR\sin\alpha\le m^*\ell,
\qquad \dot x_\infty=\frac{MgR^2\sin\alpha}{c},
$$

$$
q_\infty=\alpha-\arcsin\left(\frac{MR\sin\alpha}{m^*\ell}\right).
$$

A strict interior existence condition is needed for the displayed branch; existence alone does not prove stability. The default numerical trajectory relaxes to **48.1395874662 mm/s**, with core angle **−21.4895111589°**. A stored sample near 6 s has acceleration approximately $-1.28\times10^{-5}$ m/s², and the 12 s sample approximately $8.61\times10^{-11}$ m/s². Finite-time acceleration is not clamped to zero. Gravity still supplies about 22.16 mW, balanced by viscous dissipation.

**Status:** equilibrium derived from the implemented ODE. `tests/test_terminal.py` checks velocity differences, equilibrium substitution, power balance and half-step convergence. This plateau does not establish that the real device has a stationary core or a fixed gap.

## 8. Ground contact and the rigid reference

The total centre-of-mass displacement relative to the shell is $(m^*/M)\mathbf e$. Newton's law therefore requires

$$
\begin{aligned}
F&=M\ddot x+m^*\ell(\cos q\,\ddot q-\sin q\,\dot q^2)-Mg\sin\alpha,\\
N&=Mg\cos\alpha+m^*\ell(\sin q\,\ddot q+\cos q\,\dot q^2).
\end{aligned}
$$

Rolling without slip requires $N>0$ and measured static friction $\mu_s\ge |F|/N$. The model exports required forces but does not integrate slip or lift-off. Reported extrema are over saved samples; unresolved narrow peaks are possible.

The separate concentric locked reference uses

$$
I_{\mathrm{ref}}=I_s+I_c+\frac{8\pi\rho_f}{15}(R_i^5-r^5),
\qquad a_{\mathrm{ref}}=\frac{g\sin\alpha}{1+I_{\mathrm{ref}}/(MR^2)}.
$$

**Status:** direct momentum balance and concentric inertia integration. This reference is not the zero-viscosity limit of the eccentric model.

## 9. Two-dimensional fluid preview

In the translating, nonrotating shell-centre frame,

$$
\nabla\cdot\mathbf u=0,
$$

$$
\rho_f\left(\frac{\partial\mathbf u}{\partial t}
+(\mathbf u\cdot\nabla)\mathbf u\right)
=-\nabla p+\eta\nabla^2\mathbf u+\rho_f\mathbf g_{\mathrm{eff}},
$$

$$
\mathbf g_{\mathrm{eff}}=(g\sin\alpha-\ddot x,-g\cos\alpha).
$$

The no-slip prescribed boundaries and initial condition are

$$
\mathbf u_{\mathrm{wall}}=(\omega y,-\omega x),\qquad
\mathbf u_{\mathrm{core}}=\ell\dot q(\cos q,\sin q),\qquad
\mathbf u(t=0)=\mathbf0.
$$

Core spin is prescribed zero. The worker uses a staggered MAC grid, semi-Lagrangian advection, implicit viscosity with $\nu=\eta/\rho_f$, and pressure projection. [Stam (1999), §2.2](https://www.dgp.toronto.edu/people/stam/reality/Research/pdf/ns.pdf) supports that method family; it does not validate this moving-boundary implementation.

**Status:** one-way, qualitative 2D preview. Computed fluid stress is not fed back into the mechanics. Rasterized circular walls, unresolved films and disconnected-region compatibility defects limit accuracy. Divergence, linear-solve residuals and gap-cell counts expose these limits. Tracers follow computed velocity; initial placement and reseeding are visualization choices, not physical forcing.

## 10. Analytical local gap profile

For a steady parallel film, $y$ is the across-film coordinate and $\xi$ the along-film coordinate. The local Newtonian creeping-flow equation and boundary conditions are

$$
\eta\frac{d^2u}{dy^2}=\frac{dp}{d\xi},
\qquad u(0)=U_0,\quad u(h)=U_1.
$$

Integrating twice gives

$$
u(y)=U_0+\frac{(U_1-U_0)y}{h}
+\frac{1}{2\eta}\frac{dp}{d\xi}y(y-h),
$$

$$
\tau(y)=\eta\frac{U_1-U_0}{h}
+\frac{dp}{d\xi}\left(y-\frac h2\right).
$$

The Python `/api/flow` endpoint evaluates this analytical profile. The live graph uses zero imposed pressure gradient and relative orbital translation speed $\ell s$. It is separate from the whole-cavity field and does not determine the global eccentric pressure gradient.

The orbital Reynolds estimate is

$$
\mathrm{Re}=\frac{\rho_f|\ell s|\,2r}{\eta}.
$$

It is undefined at zero viscosity and exported as null. High Reynolds number weakens a creeping-flow interpretation; low Reynolds number alone does not validate the approximate resistance law.

## 11. Primary sources and what they support

1. **Balmforth, Bush, Vener & Young (2007).** [Dissipative descent: rocking and rolling down an incline](https://personal.math.ubc.ca/~njb/Research/sbx1.pdf). *Journal of Fluid Mechanics* **590**, 295–318. [DOI: 10.1017/S0022112007008051](https://doi.org/10.1017/S0022112007008051). Motivates nested-cylinder buoyancy, mean-fluid inertia and lubrication. This app is a sphere adaptation with a simpler fixed-gap closure.
2. **S. Widnall, MIT Dynamics (2009), Lecture 20.** [Energy Methods: Lagrange's Equations](https://ocw.mit.edu/courses/16-07-dynamics-fall-2009/resources/mit16_07f09_lec20/). Supports the analytical-mechanics derivation framework.
3. **J. Stam (1999).** [Stable Fluids](https://www.dgp.toronto.edu/people/stam/reality/Research/pdf/ns.pdf). *SIGGRAPH '99*. [DOI: 10.1145/311535.311548](https://doi.org/10.1145/311535.311548). Supports the advection/implicit-viscosity/projection method family.
4. **Material property sources.** [NIST steel table](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101567); [Plansee material-density table](https://www.plansee.com/100/content/Plansee_100Jahre-Festschrift_EN.pdf); [Copper Development Association](https://archive.copper.org/resources/properties/129_6/characteristics_properties.php); [Plansee tungsten](https://plansee-group.com/en/company/tungsten). Supports nominal presets, not measured density of an arbitrary alloy. Some property pages are available through indexed records when direct retrieval is unavailable.

## 12. Verification and experimental limits

Automated checks cover material-dependent mass and inertia, cubic radius scaling, direct versus reduced kinetic energy, positive mass matrices, instantaneous energy balance, damping signs, co-rotation, horizontal rest, deterministic repeatability, ground-contact balances, Python/JavaScript parity, terminal convergence and finite fluid fields.

Quantitative validation still requires measured material density, geometry, fill level, film/roughness, viscosity at temperature, ramp friction and repeated shell/core trajectories with uncertainties. Free core spin, changing contact, 3D flow, partial fill/sloshing, internal fluid circulation inertia and thermal changes require extending the model.
