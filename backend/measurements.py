"""Arbitrary-time trajectory analysis with explicit SI conversion and error assumptions."""
import math
import statistics
from .model import number, interpolate, constants, parameters

UNITS={'m':1.,'cm':.01,'mm':.001}

def timestamp(value,fps=30):
    if isinstance(value,str):
        value=value.strip()
        if value.lower().endswith('f'):
            frame=number(value[:-1],'frame number')
            if frame<0 or frame!=int(frame):
                raise ValueError('Frame numbers must be nonnegative integers.')
            rate=number(fps,'FPS')
            if rate<=0:
                raise ValueError('FPS must be positive.')
            value=frame/rate
        elif ':' in value:
            parts=value.split(':')
            if len(parts) not in (2,3):
                raise ValueError('Use seconds, mm:ss.s, hh:mm:ss.s, or a frame number followed by f.')
            parsed=[number(part,'timestamp') for part in parts]
            if any(x<0 for x in parsed) or any(x>=60 for x in parsed[1:]) or any(x!=int(x) for x in parsed[:-1]):
                raise ValueError('Invalid clock timestamp.')
            value=sum(v*60**(len(parsed)-1-i) for i,v in enumerate(parsed))
    result=number(value,'timestamp')
    if result<0:
        raise ValueError('Timestamps must be nonnegative.')
    return result

def normalize(payload):
    if not isinstance(payload,dict):
        raise ValueError('Measurement request must be an object.')
    rows=payload.get('rows')
    if not isinstance(rows,list) or not 3<=len(rows)<=10000:
        raise ValueError('Provide 3–10000 timestamp/distance rows.')
    unit=payload.get('distance_unit','m')
    if unit not in UNITS:
        raise ValueError('Distance unit must be m, cm, or mm.')
    scale=UNITS[unit]
    fps=number(payload.get('fps',30),'FPS')
    if not 0<fps<=10000:
        raise ValueError('FPS must be positive and at most 10000.')
    time_offset=timestamp(payload.get('time_offset',0),fps)
    position_offset=number(payload.get('position_offset',0),'position origin')*scale
    sx=number(payload.get('sigma_x',0),'position uncertainty')*scale
    st=number(payload.get('sigma_t',0),'time uncertainty')
    if sx<0 or st<0:
        raise ValueError('Uncertainties cannot be negative.')
    result=[]
    for i,row in enumerate(rows):
        if not isinstance(row,dict):
            raise ValueError(f'Row {i+1} must be an object.')
        t=timestamp(row.get('t'),fps)-time_offset
        if t<0:
            raise ValueError(f'Row {i+1} precedes the selected time origin.')
        z=dict(t=t,x=number(row.get('x'),'distance')*scale-position_offset,
               sigma_x=number(row.get('sigma_x',sx/scale),'position uncertainty')*scale,
               sigma_t=number(row.get('sigma_t',st),'time uncertainty'))
        if z['sigma_x']<0 or z['sigma_t']<0:
            raise ValueError('Uncertainties cannot be negative.')
        if row.get('v') is not None:
            z['v']=number(row['v'],'velocity')  # optional velocity is always SI
        result.append(z)
    result.sort(key=lambda z:z['t'])
    if any(b['t']<=a['t'] for a,b in zip(result,result[1:])):
        raise ValueError('Timestamps must be unique.')
    return result

def differentiation(rows,key,order=1):
    result=[]
    n=len(rows)
    for i,row in enumerate(rows):
        if order==1 and (i==0 or i==n-1):
            indices=[0,1] if i==0 else [n-2,n-1]
            dt=rows[indices[1]]['t']-rows[indices[0]]['t']
            weights=[-1/dt,1/dt]
        else:
            indices=[0,1,2] if i==0 else [n-3,n-2,n-1] if i==n-1 else [i-1,i,i+1]
            times=[rows[j]['t'] for j in indices]
            weights=[]
            for j,t in enumerate(times):
                others=[v for k,v in enumerate(times) if k!=j]
                denom=(t-others[0])*(t-others[1])
                weights.append((2*row['t']-sum(others))/denom if order==1 else 2/denom)
        value=sum(weight*rows[j][key] for weight,j in zip(weights,indices))
        sigma=math.sqrt(sum((weight*rows[j]['sigma_x'])**2 for weight,j in zip(weights,indices)))
        if not math.isfinite(value) or not math.isfinite(sigma):
            raise ValueError('Sample spacing is too small for stable differentiation.')
        result.append((value,sigma))
    return result

def analyze(payload):
    data=normalize(payload)
    velocities=differentiation(data,'x')
    accelerations=differentiation(data,'x',2)
    radius=number(payload.get('radius_mm',35),'outer radius')/1000
    if radius<=0:
        raise ValueError('Outer radius must be positive.')
    for z,(v,sv),(a,sa) in zip(data,velocities,accelerations):
        supplied='v' in z
        z.update(v=z.get('v',v),a=a,sigma_v=None if supplied else sv,sigma_a=sa,
                 velocity_source='supplied' if supplied else 'position finite difference')
        z['omega']=z['v']/radius
        z['angular_acceleration']=a/radius
    duration=data[-1]['t']-data[0]['t']
    dx=data[-1]['x']-data[0]['x']
    summary=dict(samples=len(data),duration=duration,displacement=dx,
                 path_length=sum(abs(b['x']-a['x']) for a,b in zip(data,data[1:])),
                 mean_velocity=dx/duration,peak_velocity=max(z['v'] for z in data),
                 mean_velocity_sigma=math.sqrt(data[0]['sigma_x']**2+data[-1]['sigma_x']**2+
                    (dx/duration)**2*(data[0]['sigma_t']**2+data[-1]['sigma_t']**2))/duration,
                 velocity_sd=statistics.stdev(z['v'] for z in data))
    return dict(data=data,summary=summary,units='SI: s, m, m/s, m/s², rad/s',
                assumptions='Instantaneous derivative uncertainties use independent position errors only, with timestamps held fixed. Interval/mean velocity uncertainties use independent endpoint position and time errors. No smoothing. Angular quantities assume rolling without slip.',
                metadata={key:payload.get(key) for key in ('trial_name','temperature_c','fluid','reference')})

def interval(payload):
    analysis=analyze(payload)
    data=analysis['data']
    if payload.get('mode','time')=='distance':
        scale=UNITS[payload.get('distance_unit','m')]
        offset=number(payload.get('position_offset',0),'position origin')*scale
        x1=number(payload.get('x_start'),'start distance')*scale-offset
        x2=number(payload.get('x_end'),'end distance')*scale-offset
        def crossing(x,after):
            for a,b in zip(data,data[1:]):
                if b['t']<after:
                    continue
                if a['x']==b['x']:
                    if x==a['x']:
                        return max(after,a['t'])
                    continue
                f=(x-a['x'])/(b['x']-a['x'])
                t=a['t']+f*(b['t']-a['t'])
                if 0<=f<=1 and t>=after:
                    return t
            raise ValueError('The selected distance is not crossed in chronological order within the measured trajectory.')
        t1=crossing(x1,data[0]['t'])
        t2=crossing(x2,t1)
    elif payload.get('mode','time')=='time':
        fps=payload.get('fps',30)
        origin=timestamp(payload.get('time_offset',0),fps)
        t1=timestamp(payload.get('t_start'),fps)-origin
        t2=timestamp(payload.get('t_end'),fps)-origin
    else:
        raise ValueError('mode must be time or distance.')
    if t2<=t1:
        raise ValueError('The end timestamp must follow the start timestamp.')
    a,b=interpolate(data,t1),interpolate(data,t2)
    dt=t2-t1
    dx=b['x']-a['x']
    v=dx/dt
    # Endpoint independence is an approximation when interpolants share input samples.
    sigma=math.sqrt(a['sigma_x']**2+b['sigma_x']**2+v*v*(a['sigma_t']**2+b['sigma_t']**2))/dt
    return dict(t_start=t1,t_end=t2,x_start=a['x'],x_end=b['x'],duration=dt,
                displacement=dx,mean_velocity=v,sigma_velocity=sigma,
                uncertainty_method='First-order independent endpoint approximation; interpolation and calibration covariance are not included.',
                method='Linear interpolation; distance mode selects the first chronological crossing of each marker.')
