// 2D incompressible Navier–Stokes on a staggered MAC grid with moving raster walls.
// Semi-Lagrangian advection + implicit viscosity + pressure projection (one-way coupling).
export class FluidSolver {
 constructor(k,p,n=40){this.k=k;this.params={...p};this.n=n;this.s=n+3;this.h=2*k.Ri/n;this.size=this.s*this.s;this.u=new Float64Array(this.size);this.v=new Float64Array(this.size);this.pressure=new Float64Array(this.size);this.kind=new Uint8Array(this.size);this.umask=new Uint8Array(this.size);this.vmask=new Uint8Array(this.size);this.cells=[];this.ufaces=[];this.vfaces=[];this.time=0;this.steps=0;this.particles=[];this.diagnostics={divergence:0,beforeProjection:0,pressureResidual:0,diffusionResidual:0,maxSpeed:0,grid:n,gapCells:p.gap/1000/this.h};this.geometry({q:p.q0*Math.PI/180,w:0,omega:0});this.seed();}
 geometry(z){const {k,s,n,h}=this;this.state=z;this.cx=k.l*Math.sin(z.q);this.cy=-k.l*Math.cos(z.q);this.cu=k.l*Math.cos(z.q)*z.w;this.cv=k.l*Math.sin(z.q)*z.w;this.cells=[];this.ufaces=[];this.vfaces=[];this.kind.fill(0);this.umask.fill(0);this.vmask.fill(0);
  for(let j=1;j<=n;j++)for(let i=1;i<=n;i++){const x=-k.Ri+(i-.5)*h,y=-k.Ri+(j-.5)*h,id=i+j*s;if((x-this.cx)**2+(y-this.cy)**2<k.r*k.r)this.kind[id]=2;else if(x*x+y*y<k.Ri*k.Ri){this.kind[id]=1;this.cells.push(id);}}
  for(let j=1;j<=n;j++)for(let i=1;i<=n+1;i++){const id=i+j*s;if(this.kind[id]===1&&this.kind[id-1]===1){this.umask[id]=1;this.ufaces.push(id);}}
  for(let j=1;j<=n+1;j++)for(let i=1;i<=n;i++){const id=i+j*s;if(this.kind[id]===1&&this.kind[id-s]===1){this.vmask[id]=1;this.vfaces.push(id);}}
  this.components=[];const seen=new Uint8Array(this.size);for(const first of this.cells){if(seen[first])continue;const group=[first];seen[first]=1;for(let j=0;j<group.length;j++)for(const offset of [-1,1,-s,s]){const id=group[j]+offset;if(this.kind[id]===1&&!seen[id]){seen[id]=1;group.push(id);}}this.components.push(group);}
  this.boundaries();
 }
 boundaries(){const {s,n,h,k,state:z}=this;for(let j=0;j<n+3;j++)for(let i=0;i<n+3;i++){const id=i+j*s,xu=-k.Ri+(i-1)*h,yu=-k.Ri+(j-.5)*h,xv=-k.Ri+(i-.5)*h,yv=-k.Ri+(j-1)*h;
  if(!this.umask[id])this.u[id]=(this.kind[id]===2||this.kind[id-1]===2||(xu-this.cx)**2+(yu-this.cy)**2<k.r*k.r)?this.cu:z.omega*yu;
  if(!this.vmask[id])this.v[id]=(this.kind[id]===2||this.kind[id-s]===2||(xv-this.cx)**2+(yv-this.cy)**2<k.r*k.r)?this.cv:-z.omega*xv;
 }}
 bilinear(field,x,y,component){const {h,s,k,n}=this,ix=Math.max(0,Math.min(n+1,(x+k.Ri)/h+(component==='u'?1:.5))),iy=Math.max(0,Math.min(n+1,(y+k.Ri)/h+(component==='v'?1:.5))),i=Math.floor(ix),j=Math.floor(iy),a=ix-i,b=iy-j,id=i+j*s;return (1-b)*((1-a)*field[id]+a*field[id+1])+b*((1-a)*field[id+s]+a*field[id+s+1]);}
 velocity(x,y){return {u:this.bilinear(this.u,x,y,'u'),v:this.bilinear(this.v,x,y,'v')};}
 inside(x,y,margin=0){return x*x+y*y<(this.k.Ri-margin)**2&&(x-this.cx)**2+(y-this.cy)**2>(this.k.r+margin)**2;}
 // Conjugate gradients solve both SPD Helmholtz diffusion systems and the pressure Poisson system.
 cg(ids,apply,b,x,tolerance=1e-6,maxIterations=220){const r=new Float64Array(this.size),d=new Float64Array(this.size),ad=new Float64Array(this.size),ax=new Float64Array(this.size);apply(x,ax);let rr=0,bb=0;for(const id of ids){r[id]=b[id]-ax[id];d[id]=r[id];rr+=r[id]*r[id];bb+=b[id]*b[id];}const initial=rr,target=Math.max(1e-24,bb*tolerance*tolerance);let iter=0;
  for(;iter<maxIterations&&rr>target;iter++){apply(d,ad);let den=0;for(const id of ids)den+=d[id]*ad[id];if(den<=1e-30)break;const alpha=rr/den;let next=0;for(const id of ids){x[id]+=alpha*d[id];r[id]-=alpha*ad[id];next+=r[id]*r[id];}const beta=next/rr;for(const id of ids)d[id]=r[id]+beta*d[id];rr=next;}
  return {relativeResidual:Math.sqrt(rr/Math.max(bb,1e-24)),iterations:iter,initialResidual:Math.sqrt(initial)};
 }
 diffuse(field,mask,ids,dt){const a=this.params.eta/this.params.rho*dt/(this.h*this.h),s=this.s,b=new Float64Array(this.size),out=field.slice();for(const id of ids){b[id]=field[id];for(const offset of [-1,1,-s,s])if(!mask[id+offset])b[id]+=a*field[id+offset];}
  const apply=(x,y)=>{for(const id of ids){let value=(1+4*a)*x[id];for(const offset of [-1,1,-s,s])if(mask[id+offset])value-=a*x[id+offset];y[id]=value;}};
  const result=this.cg(ids,apply,b,out);for(const id of ids)field[id]=out[id];return result.relativeResidual;
 }
 divergenceRMS(){let sum=0;for(const id of this.cells){const d=(this.u[id+1]-this.u[id]+this.v[id+this.s]-this.v[id])/this.h;sum+=d*d;}return Math.sqrt(sum/Math.max(1,this.cells.length));}
 project(dt){const {s,h,kind,cells}=this,rho=this.params.rho,b=new Float64Array(this.size);const before=this.divergenceRMS();for(const id of cells)b[id]=-rho*h/dt*(this.u[id+1]-this.u[id]+this.v[id+s]-this.v[id]);let compatibility=0;for(const group of this.components){let mean=0;for(const id of group)mean+=b[id];mean/=group.length;compatibility+=group.length*(mean*dt/(rho*h*h))**2;for(const id of group)b[id]-=mean;}this.diagnostics.boundaryCompatibility=Math.sqrt(compatibility/Math.max(1,cells.length));
  const apply=(x,y)=>{for(const id of cells){let count=0,sum=0;for(const offset of [-1,1,-s,s])if(kind[id+offset]===1){count++;sum+=x[id+offset];}y[id]=count*x[id]-sum;}};
  const result=this.cg(cells,apply,b,this.pressure,1e-6,320);for(const group of this.components){let gauge=0;for(const id of group)gauge+=this.pressure[id];gauge/=group.length;for(const id of group)this.pressure[id]-=gauge;}
  for(const id of this.ufaces)this.u[id]-=dt/rho*(this.pressure[id]-this.pressure[id-1])/h;
  for(const id of this.vfaces)this.v[id]-=dt/rho*(this.pressure[id]-this.pressure[id-s])/h;
  this.diagnostics.beforeProjection=before;this.diagnostics.divergence=this.divergenceRMS();this.diagnostics.pressureResidual=result.relativeResidual;
 }
 step(dt,z){if(!(dt>0&&dt<=.05))throw Error('Fluid timestep must be positive and at most 0.05 s.');this.geometry(z);const oldU=this.u.slice(),oldV=this.v.slice(),{s,h,k}=this;
  for(const [field,ids,component] of [[this.u,this.ufaces,'u'],[this.v,this.vfaces,'v']])for(const id of ids){const i=id%s,j=Math.floor(id/s),x=-k.Ri+(i-(component==='u'?1:.5))*h,y=-k.Ri+(j-(component==='v'?1:.5))*h,u=this.bilinear(oldU,x,y,'u'),v=this.bilinear(oldV,x,y,'v');field[id]=this.bilinear(component==='u'?oldU:oldV,x-dt*u,y-dt*v,component);}
  this.diagnostics.diffusionResidual=Math.max(this.diffuse(this.u,this.umask,this.ufaces,dt),this.diffuse(this.v,this.vmask,this.vfaces,dt));
  // The frame translates with the shell but does not rotate: gravity minus shell acceleration.
  const fx=k.g*Math.sin(k.alpha)-(z.a||0),fy=-k.g*Math.cos(k.alpha);for(const id of this.ufaces)this.u[id]+=dt*fx;for(const id of this.vfaces)this.v[id]+=dt*fy;this.project(dt);this.boundaries();this.time+=dt;this.steps++;
  let max=0;for(const id of this.cells){const u=(this.u[id]+this.u[id+1])/2,v=(this.v[id]+this.v[id+s])/2;max=Math.max(max,Math.hypot(u,v));}this.diagnostics.maxSpeed=max;
  for(let j=0;j<this.particles.length;j++){const point=this.particles[j],v0=this.velocity(point.x,point.y),mid=this.velocity(point.x+dt*v0.u/2,point.y+dt*v0.v/2);point.px=point.x;point.py=point.y;const x=point.x+dt*mid.u,y=point.y+dt*mid.v;if(this.inside(x,y,this.h*.15)){point.x=x;point.y=y;}else this.seedParticle(point,j+this.steps);}
 }
 seedParticle(point,index){for(let j=0;j<500;j++){const phase=(index*137+j*71+this.steps*23)%997,angle=phase/997*Math.PI*2,radius=this.k.Ri*Math.sqrt(((index*313+j*109+57)%991)/991)*.96,x=radius*Math.cos(angle),y=radius*Math.sin(angle);if(this.inside(x,y,this.h*.15)){point.x=point.px=x;point.y=point.py=y;return;}}point.x=point.px=0;point.y=point.py=this.k.Ri*.85;}
 seed(){this.particles=Array.from({length:130},(_,i)=>{const p={};this.seedParticle(p,i);return p;});}
 snapshot(){const cells=[];for(const id of this.cells){const i=id%this.s,j=Math.floor(id/this.s);cells.push({x:-this.k.Ri+(i-.5)*this.h,y:-this.k.Ri+(j-.5)*this.h,u:(this.u[id]+this.u[id+1])/2,v:(this.v[id]+this.v[id+this.s])/2,pressure:this.pressure[id]});}return {t:this.time,eta:this.params.eta,rho:this.params.rho,grid:this.n,diagnostics:{...this.diagnostics},cells};}
}
