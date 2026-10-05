import {FluidSolver} from './fluid.js';
import {constants} from './physics.js';
let solver=null,trajectory=[],target=0,generation=0,requestId=0,lastPublish=-1,timer=null;
function stateAt(t){let lo=0,hi=trajectory.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(trajectory[m].t<=t)lo=m;else hi=m;}const a=trajectory[lo],b=trajectory[hi],f=Math.max(0,Math.min(1,(t-a.t)/(b.t-a.t||1)));return Object.fromEntries(Object.keys(a).map(key=>[key,a[key]===null||b[key]===null?null:a[key]+(b[key]-a[key])*f]));}
function publish(){const field=solver.snapshot();self.postMessage({type:'field',generation,requestId,complete:target-solver.time<=1e-8,field,particles:solver.particles.map(p=>({...p})),target});lastPublish=solver.time;}
function cancelPump(){if(timer!==null)clearTimeout(timer);timer=null;}
function pump(){
 timer=null;if(!solver)return;
 try{
  let count=0;
  while(target-solver.time>1e-8&&count++<6){const at=stateAt(solver.time),boundarySpeed=Math.max(Math.abs(solver.k.Ri*at.omega),Math.abs(solver.k.l*at.w)),dt=Math.min(1/60,target-solver.time,solver.h*.5/Math.max(boundarySpeed,1e-6));solver.step(dt,stateAt(solver.time+dt));}
  if(solver.time-lastPublish>=1/30||target-solver.time<=1e-8)publish();
  if(target-solver.time>1e-8){const epoch=generation;timer=setTimeout(()=>{if(epoch===generation)pump();},0);}
 }catch(error){target=solver.time;self.postMessage({type:'error',generation,message:error.message});}
}
self.onmessage=e=>{
 const message=e.data;
 try{
  if(message.type==='reset'){
   cancelPump();generation=message.generation;requestId=0;trajectory=message.trajectory;
   solver=new FluidSolver(constants(message.parameters),message.parameters,message.grid||40);
   target=0;lastPublish=-1;publish();
  }else if(message.type==='advance'&&message.generation===generation&&solver){
   cancelPump();requestId=message.requestId;
   if(message.time<solver.time-1e-7){solver=new FluidSolver(solver.k,solver.params,solver.n);lastPublish=-1;}
   target=Math.max(0,Math.min(message.time,trajectory.at(-1).t));pump();
  }
 }catch(error){self.postMessage({type:'error',generation,message:error.message});}
};
