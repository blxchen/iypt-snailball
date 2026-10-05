"""SI numerical mirror of physics.js; reduced mechanical model, not CFD."""
import math
from bisect import bisect_left

STEEL_DENSITY = 7850.  # Nominal kg/m³, NIST steel material-property table.

def core_mass(radius_mm,density):
    return density * 4*math.pi/3*(radius_mm/1000)**3

def steel_mass(radius_mm):
    return core_mass(radius_mm,STEEL_DENSITY)

DEFAULTS = dict(R=35, r=23, shell=28, core_density=STEEL_DENSITY, core=steel_mass(23)*1000, eta=97, rho=970,
                angle=5, gap=0.5, duration=12, q0=0, drag=1)
LIMITS = dict(core_density=(1,30000), R=(5, 100), r=(1, 80), shell=(1, 2000), core=(1, 5000),
              eta=(0, 200), rho=(100, 3000), angle=(0, 45), gap=(0.05, 10),
              duration=(0.01, 300), q0=(-180, 180), drag=(0,1))
MAX_STEPS = 1_000_000

def number(value, name):
    if isinstance(value, bool) or value is None:
        raise ValueError(f'{name} must be a finite number.')
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f'{name} must be a finite number.') from None
    if not math.isfinite(result):
        raise ValueError(f'{name} must be a finite number.')
    return result

def parameters(values=None):
    if values is not None and not isinstance(values, dict):
        raise ValueError('parameters must be an object.')
    values = values or {}
    unknown = set(values) - set(DEFAULTS)
    if unknown:
        raise ValueError('Unknown parameters: ' + ', '.join(sorted(unknown)))
    p = {key: number(values.get(key, default), key) for key, default in DEFAULTS.items()}
    # Legacy core input is a derived output now; radius and material density determine solid mass.
    p['core'] = core_mass(p['r'],p['core_density'])*1000
    for key, (lo, hi) in LIMITS.items():
        if key == 'core':
            continue
        if not lo <= p[key] <= hi:
            raise ValueError(f'{key} must be between {lo} and {hi}.')
    if p["drag"] != 1:
        raise ValueError("Use drag = 1 for the physical gap-shear model.")
    return p

def constants(p):
    R, r, Ri = p['R']/1000, p['r']/1000, p['R']/1000-.001
    l = Ri-r-p['gap']/1000
    if l <= 0:
        raise ValueError('The core and film must fit inside the 1 mm shell.')
    mf = p['rho'] * 4*math.pi/3*(Ri**3-r**3)
    mc = core_mass(p['r'],p.get('core_density',STEEL_DENSITY))
    md = p['rho']*4*math.pi/3*r**3
    m = mc-md
    mi = mc+md*md/mf
    if m <= 0:
        raise ValueError('The core must be heavier than the fluid it displaces.')
    M = p['shell']/1000+mc+mf
    I = 2/5*p['shell']/1000*(R**5-Ri**5)/(R**3-Ri**3)
    Icore = 2/5*mc*r*r
    integral=0.
    for j in range(256):
        mu=-1+(j+.5)/128
        film=math.sqrt(Ri*Ri-l*l*(1-mu*mu))-l*mu-r
        integral+=(1+mu*mu)/2/film/128
    c = p['eta']*l*l*2*math.pi*r*r*integral
    A,b,D=M+I/R**2,m*l,mi*l*l
    minimumDeterminant=A*D-b*b
    dampingRateBound=c*(A+D/R**2+2*b/R)/minimumDeterminant
    frequencyBound=math.sqrt(m*9.81*l*A/minimumDeterminant)
    return dict(minimumDeterminant=minimumDeterminant,dampingRateBound=dampingRateBound,
                frequencyBound=frequencyBound,R=R,r=r,Ri=Ri,l=l,mc=mc,md=md,mi=mi,Icore=Icore,coreDensity=p.get('core_density',STEEL_DENSITY),
                m=m,mf=mf,M=M,I=I,A=M+I/R**2,b=m*l,D=mi*l*l,c=c,alpha=math.radians(p['angle']),g=9.81)

def derivative(y,k):
    _,v,q,w = y
    rel = w+v/k['R']
    B = k['b']*math.cos(q)
    f = k['M']*k['g']*math.sin(k['alpha'])+k['b']*math.sin(q)*w*w-k['c']/k['R']*rel
    h = -k['m']*k['g']*k['l']*math.sin(q-k['alpha'])-k['c']*rel
    det = k['A']*k['D']-B*B
    return (v,(f*k['D']-B*h)/det,w,(k['A']*h-B*f)/det)

def interpolate(data,t):
    if t < data[0]['t'] or t > data[-1]['t']:
        raise ValueError('Requested timestamp is outside the trajectory.')
    i = bisect_left([z['t'] for z in data],t)
    if i == 0 or (i < len(data) and data[i]['t'] == t):
        return dict(data[i])
    a,b = data[i-1],data[i]
    f = (t-a['t'])/(b['t']-a['t'])
    return {key: a[key]+f*(b[key]-a[key]) if isinstance(a[key],(int,float)) and isinstance(b[key],(int,float)) else a[key] for key in a}

def statistics(data):
    last = data[-1]
    return dict(mean=last['x']/last['t'], peak=max(z['v'] for z in data),
                distance=last['x'], loss=last['loss'],
                Re=max(z['Re'] for z in data) if all(z['Re'] is not None for z in data) else None,
                min_normal=min(z['normal'] for z in data),
                required_friction=max(z['mu_required'] for z in data) if all(z['mu_required'] is not None for z in data) else None,
                residual=max(abs(z['residual']) for z in data))

def simulate(values=None,timestamps=None):
    p = parameters(values)
    k = constants(p)
    dt = min(.002,.08/k['frequencyBound'],.08/k['dampingRateBound'] if k['dampingRateBound'] else math.inf)
    steps = math.ceil(p['duration']/dt)
    if steps > MAX_STEPS:
        raise ValueError('This configuration requires over one million integration steps. Reduce duration or viscosity, or increase the film gap.')
    if timestamps is not None:
        if not isinstance(timestamps,list) or not 1 <= len(timestamps) <= 2000:
            raise ValueError('timestamps must contain 1–2000 values.')
        timestamps = [number(t,'timestamp') for t in timestamps]
        if any(t<0 or t>p['duration'] for t in timestamps):
            raise ValueError('Custom timestamps must lie within the simulation duration.')
    h = p['duration']/steps
    stride = max(1,steps//1000)
    y = (0.,0.,math.radians(p['q0']),0.)
    loss = 0.
    def energy(z):
        _,v,q,w=z
        T=.5*k['A']*v*v+k['b']*math.cos(q)*v*w+.5*k['D']*w*w
        U=-k['M']*k['g']*z[0]*math.sin(k['alpha'])-k['m']*k['g']*k['l']*math.cos(q-k['alpha'])
        return T,U
    initial=sum(energy(y))
    data=[]
    def add(z,d,f):
        return tuple(a+f*b for a,b in zip(z,d))
    for i in range(steps+1):
        d=derivative(y,k)
        power=k['c']*(y[3]+y[1]/k['R'])**2
        if i%stride==0 or i==steps:
            T,U=energy(y)
            friction=k['M']*d[1]+k['b']*(math.cos(y[2])*d[3]-math.sin(y[2])*y[3]**2)-k['M']*k['g']*math.sin(k['alpha'])
            normal=k['M']*k['g']*math.cos(k['alpha'])+k['b']*(math.sin(y[2])*d[3]+math.cos(y[2])*y[3]**2)
            data.append(dict(t=i*h,x=y[0],v=y[1],a=d[1],q=y[2],w=y[3],
                             omega=y[1]/k['R'],torque=-k['c']*(y[3]+y[1]/k['R']),
                             shell_torque=-k['c']*(y[3]+y[1]/k['R']),
                             relative_angular_velocity=y[3]+y[1]/k['R'],angular_acceleration=d[1]/k['R'],
                             core_angular_acceleration=d[3],friction=friction,normal=normal,
                             mu_required=abs(friction)/normal if normal>0 else None,
                             power=power,kinetic=T,potential=U,loss=loss,
                             shear=p['eta']*k['l']*(y[3]+y[1]/k['R'])/(p['gap']/1000),
                             gap_velocity=k['l']*(y[3]+y[1]/k['R']),
                             residual=T+U+loss-initial,
                             Re=p['rho']*abs(k['l']*(y[3]+y[1]/k['R']))*2*k['r']/p['eta'] if p['eta'] else None))
        if i==steps:
            break
        d2=derivative(add(y,d,h/2),k)
        d3=derivative(add(y,d2,h/2),k)
        d4=derivative(add(y,d3,h),k)
        nxt=tuple(y[j]+h/6*(d[j]+2*d2[j]+2*d3[j]+d4[j]) for j in range(4))
        loss+=h/2*(power+k['c']*(nxt[3]+nxt[1]/k['R'])**2)
        if not all(math.isfinite(v) for v in nxt):
            raise ValueError('Integrator diverged; revise the parameters.')
        y=nxt
    result=dict(parameters=p,k=k,data=data,dt=h,steps=steps,statistics=statistics(data),
                model='Solid core with configurable material density; mean-fluid translation inertia; fixed-orbit Lagrangian mechanics with gap-shear Rayleigh dissipation. One-way 2D fluid preview; core spin and fluid circulation inertia omitted.',
                reynolds_defined=p['eta']>0)
    if timestamps is not None:
        result['samples']=[interpolate(data,t) for t in timestamps]
        result['sampling']='Linear interpolation of the output trajectory (approximately 1000 samples).'
    return result
