"""Exact local parallel-gap Stokes solution, not a global snail-ball CFD solver."""
from .model import number

def gap_flow(payload):
    eta=number(payload.get('eta',97),'viscosity')
    h=number(payload.get('gap_mm',.5),'gap')/1000
    u0=number(payload.get('u0',0),'first boundary velocity')
    u1=number(payload.get('u1',0),'second boundary velocity')
    dp=number(payload.get('pressure_gradient',0),'pressure gradient')
    if eta<=0 or h<=0:
        raise ValueError('Viscosity and gap must be positive.')
    profile=[]
    for i in range(65):
        y=h*i/64
        u=u0+(u1-u0)*y/h+dp/(2*eta)*y*(y-h)
        gradient=(u1-u0)/h+dp/(2*eta)*(2*y-h)
        profile.append(dict(y=y,u=u,shear=eta*gradient))
    power=eta*(u1-u0)**2/h+dp**2*h**3/(12*eta)
    return dict(profile=profile,volume_flux_per_width=h*(u0+u1)/2-dp*h**3/(12*eta),
                dissipation_per_area=power,equation='eta d²u/dy² = dp/ds; incompressible parallel-gap creeping flow.',
                limitations='Local steady Couette–Poiseuille solution. The global pressure gradient, eccentric 3D fluid motion, and liquid inertia are not solved.')
