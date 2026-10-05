// Energy-consistent, two-coordinate reduced model. All internal quantities are SI.
export const STEEL_DENSITY=7850; // Nominal steel, kg/m³; NIST material-property table.
export function coreMass(radiusMm,density){return density*4*Math.PI/3*(radiusMm/1000)**3;}
export function steelMass(radiusMm){return coreMass(radiusMm,STEEL_DENSITY);}
export const defaults={R:35,r:23,shell:28,core_density:STEEL_DENSITY,core:steelMass(23)*1000,eta:97,rho:970,angle:5,gap:0.5,duration:12,q0:0,drag:1};
export function normalizeParameters(values){
 const p={...defaults,...values};
 for(const key of Object.keys(defaults)){if(!Number.isFinite(p[key]))throw Error(key+' must be finite.');}
 if(p.R<=1||p.r<=0||p.shell<=0||p.rho<=0||p.eta<0||p.gap<=0||p.duration<=0)throw Error('Geometry, mass, density, gap and duration must be positive; viscosity cannot be negative.');
 if(p.drag!==1)throw Error('Use drag = 1 for the physical gap-shear model.');
 if(p.core_density<1||p.core_density>30000)throw Error('Inner-ball density must be between 1 and 30000 kg/m³.');
 // core is retained in exports for compatibility; mass follows radius and density.
 p.core=coreMass(p.r,p.core_density)*1000;return p;
}
export function constants(values){
 const p=normalizeParameters(values);
 const R=p.R/1000,r=p.r/1000,Ri=R-.001,l=Ri-r-p.gap/1000;
 if(l<=0) throw Error('The inner ball and film must fit inside the 1 mm shell.');
 const volume=4*Math.PI/3*(Ri**3-r**3),mf=p.rho*volume,mc=coreMass(p.r,p.core_density),md=p.rho*4*Math.PI*r**3/3,m=mc-md,mi=mc+md*md/mf;
 if(m<=0)throw Error('The core must be heavier than the fluid it displaces.');
 const M=p.shell/1000+mc+mf,I=2/5*(p.shell/1000)*(R**5-Ri**5)/(R**3-Ri**3),Icore=2/5*mc*r*r;
 const A=M+I/R**2,b=m*l,D=mi*l*l;let integral=0;for(let j=0;j<256;j++){const mu=-1+(j+.5)/128,h=Math.sqrt(Ri*Ri-l*l*(1-mu*mu))-l*mu-r;integral+=(1+mu*mu)/2/h/128;}const c=p.eta*l*l*2*Math.PI*r*r*integral;
 const minimumDeterminant=A*D-b*b;
 const dampingRateBound=c*(A+D/R**2+2*b/R)/minimumDeterminant;
 const frequencyBound=Math.sqrt(m*9.81*l*A/minimumDeterminant);
 return {minimumDeterminant,dampingRateBound,frequencyBound,R,r,Ri,l,mc,md,mi,Icore,coreDensity:p.core_density,m,mf,M,I,A,b,D,c,alpha:p.angle*Math.PI/180,g:9.81};
}
export function derivative(y,k){const [x,v,q,w]=y,rel=w+v/k.R,B=k.b*Math.cos(q),f=k.M*k.g*Math.sin(k.alpha)+k.b*Math.sin(q)*w*w-k.c/k.R*rel,h=-k.m*k.g*k.l*Math.sin(q-k.alpha)-k.c*rel,det=k.A*k.D-B*B;return [v,(f*k.D-B*h)/det,w,(k.A*h-B*f)/det];}
export function simulate(values){const p=normalizeParameters(values),k=constants(p),out=[],dt=Math.min(.002,.08/k.dampingRateBound,.08/k.frequencyBound),steps=Math.ceil(p.duration/dt),h=p.duration/steps;if(steps>1000000)throw Error('This configuration requires over one million integration steps. Reduce duration or viscosity, or increase the film gap.');let y=[0,0,p.q0*Math.PI/180,0],loss=0;const stride=Math.max(1,Math.floor(steps/1000));
 const energy=z=>.5*k.A*z[1]**2+k.b*Math.cos(z[2])*z[1]*z[3]+.5*k.D*z[3]**2-k.M*k.g*z[0]*Math.sin(k.alpha)-k.m*k.g*k.l*Math.cos(z[2]-k.alpha),E0=energy(y);
 for(let i=0;i<=steps;i++){const d=derivative(y,k),power=k.c*(y[3]+y[1]/k.R)**2;if(i%stride===0||i===steps){const friction=k.M*d[1]+k.b*(Math.cos(y[2])*d[3]-Math.sin(y[2])*y[3]**2)-k.M*k.g*Math.sin(k.alpha),normal=k.M*k.g*Math.cos(k.alpha)+k.b*(Math.sin(y[2])*d[3]+Math.cos(y[2])*y[3]**2);const kinetic=.5*k.A*y[1]**2+k.b*Math.cos(y[2])*y[1]*y[3]+.5*k.D*y[3]**2;out.push({t:i*h,x:y[0],v:y[1],a:d[1],q:y[2],w:y[3],omega:y[1]/k.R,torque:-k.c*(y[3]+y[1]/k.R),shell_torque:-k.c*(y[3]+y[1]/k.R),relative_angular_velocity:y[3]+y[1]/k.R,angular_acceleration:d[1]/k.R,core_angular_acceleration:d[3],friction,normal,mu_required:normal>0?Math.abs(friction)/normal:null,power,kinetic,potential:energy(y)-kinetic,loss,residual:energy(y)+loss-E0,shear:p.eta*k.l*(y[3]+y[1]/k.R)/(p.gap/1000),gap_velocity:k.l*(y[3]+y[1]/k.R),Re:p.eta>0?p.rho*Math.abs(k.l*(y[3]+y[1]/k.R))*2*k.r/p.eta:null});}
 if(i===steps)break;
 const add=(z,d,s)=>z.map((v,j)=>v+s*d[j]),d2=derivative(add(y,d,h/2),k),d3=derivative(add(y,d2,h/2),k),d4=derivative(add(y,d3,h),k),next=y.map((v,j)=>v+h/6*(d[j]+2*d2[j]+2*d3[j]+d4[j]));loss+=h/2*(power+k.c*(next[3]+next[1]/k.R)**2);y=next;
 if(!y.every(Number.isFinite))throw Error('Integrator diverged. Reduce the duration or revise the geometry.');
 }return {parameters:p,data:out,k,dt:h,steps};}
export function stats(run){const d=run.data,last=d.at(-1),mean=last.x/last.t,peak=Math.max(...d.map(z=>z.v));return {mean,peak,distance:last.x,loss:last.loss,Re:d.some(z=>z.Re===null)?null:Math.max(...d.map(z=>z.Re)),min_normal:Math.min(...d.map(z=>z.normal)),required_friction:d.some(z=>z.mu_required===null)?null:Math.max(...d.map(z=>z.mu_required)),residual:Math.max(...d.map(z=>Math.abs(z.residual)))};}
