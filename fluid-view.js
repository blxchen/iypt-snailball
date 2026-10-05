// Coalesce playback updates: only one fluid request may be in flight.
export function createFluidController(onUpdate){
 let worker=null,generation=0,requestId=0,inFlight=false,desired=0,sent=-1,latest=null,error=null,configuration=null;
 function fail(message){error=message;inFlight=false;worker?.terminate();worker=null;onUpdate();}
 function send(){
  if(!worker||inFlight||Math.abs(desired-sent)<1e-7)return;
  sent=desired;inFlight=true;
  worker.postMessage({type:'advance',generation,requestId:++requestId,time:sent});
 }
 function restart(){
  generation++;sent=-1;latest=null;error=null;inFlight=!!worker;
  if(worker&&configuration)worker.postMessage({type:'reset',generation,...configuration});
 }
 if(typeof Worker!=='undefined'){
  try{
   worker=new Worker(new URL('./fluid-worker.js',import.meta.url),{type:'module'});
   worker.onmessage=e=>{
    const message=e.data;if(message.generation!==generation)return;
    if(message.type==='error'){fail('Fluid solver stopped: '+message.message);return;}
    if(message.type!=='field')return;
    latest=message;error=null;
    if(message.complete){inFlight=false;send();}
    onUpdate();
   };
   worker.onerror=()=>fail('Fluid worker unavailable. Reload the page to retry.');
  }catch(exception){worker=null;error='Fluid worker could not start: '+exception.message;}
 }
 return {
  reset(parameters,trajectory,grid=40){configuration={parameters,trajectory,grid};desired=0;restart();},
  advance(time){
   if(!Number.isFinite(time)||time<0)return;
   // A seek backwards starts a new generation; old replies cannot overwrite it.
   const rewind=time<desired-1e-7;desired=time;if(rewind)restart();send();
  },
  get current(){return latest;},get error(){return error;},get available(){return !!worker;}
 };
}
