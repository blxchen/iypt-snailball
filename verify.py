"""Numerical and JavaScript syntax checks using macOS system JavaScriptCore."""
import ctypes as C
import pathlib
import sys
import json
root = pathlib.Path(__file__).parent
js = C.CDLL('/System/Library/Frameworks/JavaScriptCore.framework/JavaScriptCore')
ptr = C.c_void_p
js.JSGlobalContextCreate.argtypes = [ptr]
js.JSGlobalContextCreate.restype = ptr
js.JSStringCreateWithUTF8CString.argtypes = [C.c_char_p]
js.JSStringCreateWithUTF8CString.restype = ptr
js.JSEvaluateScript.argtypes = [ptr, ptr, ptr, ptr, C.c_int, C.POINTER(ptr)]
js.JSEvaluateScript.restype = ptr
js.JSValueToStringCopy.argtypes = [ptr, ptr, C.POINTER(ptr)]
js.JSValueToStringCopy.restype = ptr
js.JSStringGetMaximumUTF8CStringSize.argtypes = [ptr]
js.JSStringGetMaximumUTF8CStringSize.restype = C.c_size_t
js.JSStringGetUTF8CString.argtypes = [ptr, C.c_char_p, C.c_size_t]
js.JSStringGetUTF8CString.restype = C.c_size_t
js.JSStringRelease.argtypes = [ptr]
js.JSGlobalContextRelease.argtypes = [ptr]
ctx = js.JSGlobalContextCreate(None)
def to_string(value):
    string = js.JSValueToStringCopy(ctx, value, None)
    size = js.JSStringGetMaximumUTF8CStringSize(string)
    buf = C.create_string_buffer(size)
    js.JSStringGetUTF8CString(string, buf, size)
    js.JSStringRelease(string)
    return buf.value.decode()
def evaluate(source):
    string = js.JSStringCreateWithUTF8CString(source.encode())
    exception = ptr()
    result = js.JSEvaluateScript(ctx, string, None, None, 1, C.byref(exception))
    js.JSStringRelease(string)
    if exception.value:
        raise RuntimeError(to_string(exception))
    return to_string(result)
evaluate((root / 'physics.js').read_text().replace('export ', ''))
fluid_source=(root / 'fluid.js').read_text().replace('export ', '')
evaluate(fluid_source)
app_source='\n'.join(line for line in (root / 'app.js').read_text().splitlines() if not line.startswith('import '))
measurement_source=(root / 'measurements.js').read_text().replace('export ', '')
evaluate('new Function(' + json.dumps(app_source) + ')')
evaluate('new Function(' + json.dumps(measurement_source) + ')')
liquid_source=(root / 'liquids.js').read_text().replace('export ', '')
scene_source=(root / 'scene3d.js').read_text().replace('export ', '')
fluid_view_source=(root / 'fluid-view.js').read_text().replace('export ', '').replace('import.meta.url', '"http://localhost:8000/fluid-view.js"')
evaluate('new Function(' + json.dumps(fluid_view_source) + ')')
evaluate('new Function(' + json.dumps(scene_source) + ')')
print(evaluate('''
(function(){
 const r=simulate(defaults),s=stats(r);
 function check(ok,label){if(!ok)throw Error(label);return label;}
 let checks=[];
 checks.push(check(r.data.every(z=>Object.values(z).every(Number.isFinite)),'finite state trajectory'));
 checks.push(check(r.data[0].x===0&&r.data[0].v===0,'rest initial conditions'));
 checks.push(check(Math.abs(r.data.at(-1).t-defaults.duration)<1e-9,'requested duration'));
 checks.push(check(r.data.every(z=>z.power>=0),'nonnegative dissipation'));
 checks.push(check(s.residual<1e-5,'energy balance'));
 const high=stats(simulate({...defaults,eta:150}));
 checks.push(check(high.mean<s.mean,'higher viscosity slows mean motion'));
 let rejected=false;try{simulate({...defaults,R:25,r:30});}catch(e){rejected=true;}
 checks.push(check(rejected,'invalid geometry rejected'));
 const low=simulate({...defaults,eta:0,duration:2});
 checks.push(check(stats(low).residual<1e-7,'undamped mechanical energy conservation'));
 const configurations=[{angle:20},{eta:.1},{R:60},{r:20},{gap:.1,eta:20,duration:2},{q0:30}];
 for(const cfg of configurations){const test=simulate({...defaults,...cfg});checks.push(check(test.data.every(z=>Number.isFinite(z.v)),'finite parameter test '+JSON.stringify(cfg)));}
 return JSON.stringify({checks,defaultStatistics:s,highViscosityMean:high.mean,steps:r.steps},null,2);
})()
'''))

# Minimal DOM/canvas harness checks page generation and drawing without a GUI browser.
evaluate("""
var elements = {}, storage = {}, drawCommands = 0, clickedDownloads=[];
var location = {hash:'#simulation'};
var gradient = {addColorStop:function(){}};
var drawing = new Proxy({}, {get:function(obj,key){
 if(key==='createLinearGradient'||key==='createRadialGradient')return function(){return gradient;};
 return function(){drawCommands++;};
},set:function(){return true;}});
function fakeElement(id){return {id:id,innerHTML:'',textContent:'',value:'',style:{},listeners:{},classList:{add:function(){},remove:function(){},toggle:function(){}},addEventListener:function(name,fn){this.listeners[name]=fn;},setAttribute:function(){},getAttribute:function(){return 'graph';},setPointerCapture:function(){},getBoundingClientRect:function(){return {width:720,height:id==='scene'?328:210,left:0,top:0};},getContext:function(){return drawing;},checkValidity:function(){return true;},toDataURL:function(){return 'data:image/png;base64,test';},click:function(){clickedDownloads.push({href:this.href,name:this.download});}};}
var document={querySelector:function(selector){
 var id=selector.slice(1);
 if(selector[0]==='#' && (['app','content','toast'].includes(id)||(elements.content&&elements.content.innerHTML.includes('id="'+id+'"'))))return elements[id]||(elements[id]=fakeElement(id));
 return null;
},querySelectorAll:function(){return [];},createElement:function(){return fakeElement('new');},body:{append:function(){}}};
var localStorage={getItem:function(k){return storage[k]||null;},setItem:function(k,v){storage[k]=v;}};
var window={devicePixelRatio:1,innerWidth:1200,addEventListener:function(){},scrollTo:function(){}};
function requestAnimationFrame(){return 1;}
function setTimeout(){return 1;}
function clearTimeout(){}
""")
evaluate(measurement_source)
evaluate(liquid_source)
evaluate((root / 'materials.js').read_text().replace('export ', ''))
evaluate(scene_source)
evaluate(fluid_view_source)
evaluate((root / 'equations.js').read_text().replace('export ', ''))
evaluate('\n'.join(line for line in (root / 'model-page.js').read_text().replace('export ', '').splitlines() if not line.startswith('import ')))
evaluate(app_source)
print(evaluate("""
(function(){
 const titles=['The science of a slow roll.','Every motion tells a story.','Change one thing. Discover more.','The equations behind the motion.','From simulation to evidence.'];
 for(let i=0;i<navItems.length;i++){
  location.hash='#'+navItems[i][0];layout();
  if(!elements.content.innerHTML.includes(titles[i]))throw Error('Missing page '+navItems[i][0]);
  drawCharts();drawScene();
 }
 location.hash='#simulation';layout();
 elements['save-run'].listeners.click();
 if(saved.length!==1||!storage['snaillab-runs'])throw Error('Run was not persisted');
 location.hash='#experiments';layout();
 document.querySelector('#sweep-key').value='eta';document.querySelector('#sweep-from').value='1';document.querySelector('#sweep-to').value='10';
 elements['run-sweep'].listeners.click();
 if(!sweep||sweep.rows.length!==5)throw Error('Sweep failed');
 if(drawCommands<1000)throw Error('Canvas renderers did not draw');
 return 'PASS: five page templates, chart/scene rendering, local save, five-value sweep.';
})()
"""))
evaluate("""
location.hash='#notebook';layout();
importCSV({target:{files:[{size:100,text:async function(){return 't,x\\n0,0\\n0.1,0.001\\n0.2,0.0022';}}]}});
""")
print(evaluate("""
(function(){if(observations.length!==3)throw Error('CSV import failed');if(Math.abs(observations[1].v-.011)>1e-9)throw Error('Velocity differentiation failed');return 'PASS: measured CSV parsing and finite differences.';})()
"""))

print(evaluate("""
(function(){
 const original={...p};updateParameters({...p,r:20,core:1});
 if(Math.abs(p.core-steelMass(20)*1000)>1e-10||Math.abs(run.k.mc-steelMass(20))>1e-12)throw Error('Radius and displayed steel mass disagree');
 if(!simulation().includes('Inner ball material')||simulation().includes('data-number="core"'))throw Error('Independent non-steel core control remains');
 if(experiments().includes('<option value="core">'))throw Error('Independent mass sweep remains');
 updateParameters(original);
 const undamped=simulate({...defaults,eta:0,duration:.1});
 if(stats(undamped).Re!==null||undamped.data.some(z=>z.Re!==null))throw Error('Undefined inviscid Reynolds number reported as zero');
 const expected=derivative([0,.03,.4,-.03/run.k.R],run.k),undampedDerivative=derivative([0,.03,.4,-.03/run.k.R],{...run.k,c:0});
 if(expected.some((value,i)=>value!==undampedDerivative[i]))throw Error('Co-rotation produces spurious orbital dissipation');
 return 'PASS: radius-derived solid steel mass, physical UI controls, undefined inviscid Reynolds number, and rotational sign consistency.';
})()
"""))

print(evaluate("""
(function(){
 location.hash='#simulation';layout();const original={...p};
 elements['core-material'].listeners.change({target:{value:'aluminium'}});
 if(p.core_density!==2700||matchingMaterial(p)?.id!=='aluminium'||Math.abs(p.core-2700*4*Math.PI/3*(p.r/1000)**3*1000)>1e-9)throw Error('Material selection failed to calculate mass');
 elements['core-density'].listeners.change({target:{value:'5300',checkValidity:()=>true}});
 if(matchingMaterial(p)!==null||p.core_density!==5300||!simulation().includes('Custom solid'))throw Error('Measured density does not select custom material');
 let captured='';const oldDownload=download;download=value=>{captured=value;};csv();
 if(!captured.includes('density_kg_m3: 5300'))throw Error('CSV loses core density');
 report();if(!captured.includes('Density 5300 kg/m³'))throw Error('Report still describes a steel core');
 download=oldDownload;
 elements['save-run'].listeners.click();if(saved.at(-1).p.core_density!==5300)throw Error('Saved material density lost');
 const copper=materials.find(material=>material.id==='copper');
 renderOrbitScene(elements.scene,sample(elapsed),run.k,'#e3a238',false,null,'off',copper.palette);
 updateParameters(original);
 return 'PASS: material selector, custom measured density, derived mass, saved density, CSV/report metadata, and material rendering.';
})()
"""))

# Check numerical parity against the independent Python implementation.
from backend.model import simulate as python_simulate
python_stats=python_simulate()['statistics']
js_stats=json.loads(evaluate('JSON.stringify(stats(simulate(defaults)))'))
for key in python_stats:
    if abs(python_stats[key]-js_stats[key])>1e-9:
        raise AssertionError(f'Python/JavaScript mismatch for {key}')
print('PASS: Python and JavaScript model statistics agree within 1e-9.')
for density in (2700,8940,19250,5300):
    cfg={'core_density':density,'duration':.2}
    python_result=python_simulate(cfg)
    js_result=json.loads(evaluate('JSON.stringify(simulate({...defaults,...'+json.dumps(cfg)+'}))'))
    for key in ('mc','md','mi','Icore','coreDensity','M'):
        if abs(python_result['k'][key]-js_result['k'][key])>1e-12:
            raise AssertionError(f'Material parity mismatch: {density}, {key}')
    if abs(python_result['data'][-1]['v']-js_result['data'][-1]['v'])>1e-10:
        raise AssertionError(f'Material trajectory parity mismatch: {density}')
print('PASS: Python/JavaScript mass, inertia, buoyancy and trajectory parity across materials.')

print(evaluate("""
(function(){
 if(parseMeasurementTimestamp('1:02.5')!==62.5||parseMeasurementTimestamp('120f',60)!==2)throw Error('Custom timestamp parser failed');
 let rejected=false;try{parseMeasurementTimestamp('1:60');}catch(e){rejected=true;}
 if(!rejected)throw Error('Invalid timestamp was accepted');
 video={readyState:2,videoWidth:720,videoHeight:210,currentTime:1,duration:2};
 calibration=[{x:0,y:100},{x:100,y:100}];calibrationLength=100;calibrationUnit='mm';trackingMode='track';
 measurementState.rows=[];measurementState.unit='mm';
 location.hash='#notebook';layout();
 const canvas=elements['tracking-frame'];
 canvas.listeners.click({target:canvas,clientX:30,clientY:100});
 if(measurementState.rows.length!==1||Math.abs(measurementState.rows[0].x-30)>1e-9)throw Error('Calibrated centre tracking failed');
 trackingMode='radius';radiusPoints=[];
 elements['tracking-frame'].listeners.click({target:canvas,clientX:10,clientY:100});
 elements['tracking-frame'].listeners.click({target:canvas,clientX:30,clientY:100});
 if(Math.abs(measuredRadius-.01)>1e-9)throw Error('Calibrated radius measurement failed');
 return 'PASS: custom timestamps, calibrated video position, calibrated shell radius.';
})()
"""))

print(evaluate("""
(function(){
 location.hash='#simulation';layout();
 const canvas=elements.scene;
 const initialYaw=camera.yaw;
 canvas.listeners.pointerdown({pointerId:1,clientX:100,clientY:100});
 canvas.listeners.pointermove({pointerId:1,clientX:150,clientY:130});
 if(camera.yaw===initialYaw)throw Error('Orbit camera did not rotate');
 canvas.listeners.pointerup({pointerId:1});
 const initialZoom=camera.zoom;
 canvas.listeners.wheel({deltaY:-100,preventDefault:function(){}});
 if(camera.zoom<=initialZoom)throw Error('Camera did not zoom');
 resetCamera();
 if(Math.abs(camera.yaw-.35)>1e-10)throw Error('Camera reset failed');
 const oldChart=chart;let shown=[];
 chart=function(id,series,options){if(id==='velocity')shown=series[0].data;return oldChart(id,series,options);};
 elapsed=.5;liveCharts=true;drawCharts();
 if(shown.at(-1).t!==.5||shown.some(z=>z.t>.5))throw Error('Live graph reveals future samples');
 const oldLength=shown.length;elapsed=1;drawCharts();
 if(shown.length<=oldLength)throw Error('Live graph did not advance');
 liveCharts=false;drawCharts();
 if(shown.at(-1).t!==p.duration)throw Error('Full trajectory mode failed');
 chart=oldChart;liveCharts=true;
 let captured='';const oldDownload=download;download=function(value){captured=value;};
 exportScope='played';csv();
 const playedRows=captured.split('\\n').filter(z=>z&&!z.startsWith('#')).slice(1);
 if(playedRows.length<2||playedRows.some(z=>Number(z.split(',')[0])>elapsed))throw Error('Played CSV includes future rows');
 exportScope='full';csv();
 if(!captured.includes('scope: full'))throw Error('CSV scope missing');
 download=oldDownload;
 exportGraph('velocity');
 if(!clickedDownloads.at(-1).name.endsWith('.png')||!clickedDownloads.at(-1).href.startsWith('data:image/png'))throw Error('PNG export failed');
 if(!simulate({...defaults,q0:30,duration:2}).data.some(z=>z.v<-.001))throw Error('Model recoil missing for displaced initial core');
 if(matchingLiquid(defaults)?.id!=='silicone100k')throw Error('Default liquid mismatch');
 return 'PASS: orbit/zoom/reset, progressive live graphs, full/played CSV, PNG export, unscripted recoil, liquid default.';
})()
"""))

print(evaluate("""
(function(){
 const cfg={...defaults},solver=new FluidSolver(constants(cfg),cfg,32);
 for(let i=0;i<10;i++)solver.step(1/60,{q:0,w:0,omega:0,a:0});
 const rest=solver.snapshot();
 if(!rest.cells.every(z=>Object.values(z).every(Number.isFinite)))throw Error('Non-finite fluid state');
 if(rest.diagnostics.maxSpeed>1e-5)throw Error('Hydrostatic fluid does not remain at rest: '+rest.diagnostics.maxSpeed);
 const driven=new FluidSolver(constants(cfg),cfg,32);
 for(let i=0;i<12;i++)driven.step(1/60,{q:0,w:0,omega:1,a:0});
 const d=driven.diagnostics;
 if(d.maxSpeed<.001)throw Error('Moving shell does not drive liquid');
 if(d.divergence>d.boundaryCompatibility+1e-4||d.pressureResidual>1e-5)throw Error('Pressure projection failed: '+JSON.stringify(d));
 const snap=driven.snapshot();
 if(!snap.cells.every(z=>Object.values(z).every(Number.isFinite)))throw Error('Non-finite driven state');
 return 'PASS: Navier–Stokes hydrostatic rest, viscous moving-wall response, pressure projection; '+JSON.stringify(d);
})()
"""))

# Exercise the worker reset/advance/rewind message protocol without a browser.
worker_source='\n'.join(line for line in (root / 'fluid-worker.js').read_text().splitlines() if not line.startswith('import '))
evaluate('var flowWorkerSource='+json.dumps(worker_source))
print(evaluate("""
(function(){
 const messages=[],queue=[],fakeSelf={postMessage:function(message){messages.push(message);}},run=simulate({...defaults,duration:.2});
 new Function('self','setTimeout',flowWorkerSource)(fakeSelf,function(fn){queue.push(fn);});
 fakeSelf.onmessage({data:{type:'reset',generation:7,parameters:{...defaults,duration:.2},trajectory:run.data,grid:32}});
 fakeSelf.onmessage({data:{type:'advance',generation:7,time:.05}});
 let loops=0;while(queue.length&&loops++<500)queue.shift()();
 const field=messages.at(-1);
 if(field.type!=='field'||Math.abs(field.field.t-.05)>1e-7)throw Error('Fluid worker did not reach requested time');
 if(!field.field.cells.every(c=>Object.values(c).every(Number.isFinite)))throw Error('Non-finite worker field');
 if(field.particles.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)))throw Error('Non-finite tracers');
 fakeSelf.onmessage({data:{type:'advance',generation:7,time:.01}});
 while(queue.length&&loops++<1000)queue.shift()();
 if(Math.abs(messages.at(-1).field.t-.01)>1e-7)throw Error('Fluid rewind failed');
 return 'PASS: fluid worker initialization, prescribed-boundary advance, finite field/tracers, replay after scrubbing.';
})()
"""))

print(evaluate("""
(function(){
 const cfg={...defaults},f=new FluidSolver(constants(cfg),cfg,32);
 for(let i=0;i<10;i++){const t=(i+1)/60;f.step(1/60,{q:t*.3,w:.3,omega:1,a:0});}
 const snapshot={field:f.snapshot(),particles:f.particles};
 for(const mode of ['tracers','velocity','pressure'])renderOrbitScene(elements.scene,sample(elapsed),run.k,'#e3a238',false,snapshot,mode);
 if(!snapshot.field.cells.every(cell=>Object.values(cell).every(Number.isFinite)))throw Error('Moving-core field is not finite');
 if(f.diagnostics.diffusionResidual>1e-5||f.diagnostics.pressureResidual>1e-5)throw Error('Fluid linear solve did not converge');
 const waterCfg={...defaults,eta:.001002,rho:998.2},water=new FluidSolver(constants(waterCfg),waterCfg,32);
 for(let i=0;i<10;i++)water.step(1/60,{q:0,w:0,omega:1,a:0});
 if(Math.abs(water.diagnostics.maxSpeed-f.diagnostics.maxSpeed)<1e-7)throw Error('Liquid changes do not affect the flow');
 return 'PASS: moving-core NS field, velocity/tracer/pressure rendering, converged linear solves, liquid-dependent flow.';
})()
"""))


# Playback regressions use actual handlers and animation ticks; monitor DOM writes.
print(evaluate("""
(function(){
 location.hash='#simulation';layout();playing=false;elapsed=0;lastTime=null;
 const button=elements.play;let html=button.innerHTML,writes=0;
 Object.defineProperty(button,'innerHTML',{configurable:true,get:()=>html,set:value=>{writes++;html=value;}});
 syncPlayback();const baseline=writes;
 for(let time=100;time<2000;time+=16)tick(time);
 if(writes!==baseline)throw Error('Idle playback continually replaces the button icon');
 button.listeners.click();tick(2000);tick(2100);
 if(!playing||Math.abs(elapsed-.1)>1e-9)throw Error('Play does not advance elapsed time');
 elements['graph-play'].listeners.click();const paused=elapsed;tick(2200);tick(2300);
 if(playing||elapsed!==paused)throw Error('Graph pause does not stop scene playback');
 for(let i=0;i<20;i++)button.listeners.click();
 if(playing)throw Error('Rapid play/pause clicks change parity');
 elements.timeline.listeners.input({target:{value:'2.5'}});
 if(elapsed!==2.5)throw Error('Timeline seek failed');
 elements.restart.listeners.click();
 if(playing||elapsed!==0)throw Error('Restart did not reset paused playback');
 elapsed=p.duration;button.listeners.click();tick(3000);tick(3100);
 if(!playing||Math.abs(elapsed-.1)>1e-9)throw Error('Play at the end does not restart');
 elapsed=p.duration-.01;tick(3200);
 if(playing||elapsed!==p.duration)throw Error('Playback does not stop at duration');
 const oldRAF=requestAnimationFrame,oldDraw=drawScene;let scheduled=0;
 requestAnimationFrame=()=>{scheduled++;};drawScene=()=>{throw Error('test renderer failure');};sceneDirty=true;
 try{tick(3300);}catch(error){if(error.message!=='test renderer failure')throw error;}
 requestAnimationFrame=oldRAF;drawScene=oldDraw;
 if(scheduled!==1)throw Error('Renderer error kills animation scheduling');
 delete button.innerHTML;button.innerHTML=html;
 return 'PASS: idle button stability, play/pause, rapid clicks, both controls, seek, restart, end replay, animation scheduling after rendering failure.';
})()
"""))

# A stalled worker must not accumulate one command per animation frame.
print(evaluate("""
(function(){
 const originalWorker=globalThis.Worker,originalURL=globalThis.URL;
 const workers=[];
 globalThis.URL=function(path,base){return base+path;};
 globalThis.Worker=class{constructor(){this.messages=[];workers.push(this);}postMessage(message){this.messages.push(message);}terminate(){this.terminated=true;}};
 try{
  let updates=0;const controller=createFluidController(()=>updates++),worker=workers[0];
  controller.reset(defaults,run.data,32);
  for(let i=0;i<100;i++)controller.advance(i/100);
  if(worker.messages.length!==1)throw Error('Fluid requests queued before initialization');
  let generation=worker.messages[0].generation;
  const reply=(t,complete=true,gen=generation)=>worker.onmessage({data:{type:'field',generation:gen,complete,field:{t}}});
  reply(0);
  if(worker.messages.length!==2||worker.messages.at(-1).time!==.99)throw Error('Latest time is not coalesced');
  for(let i=100;i<200;i++)controller.advance(i/100);
  if(worker.messages.length!==2)throw Error('Fluid request flood while busy');
  reply(.5,false);if(worker.messages.length!==2)throw Error('Intermediate field releases backpressure');
  reply(.99);if(worker.messages.at(-1).time!==1.99||worker.messages.length!==3)throw Error('Latest pending time lost');
  controller.advance(.2);const reset=worker.messages.at(-1);
  if(reset.type!=='reset'||reset.generation===generation||controller.current!==null)throw Error('Seek does not invalidate old flow');
  reply(1.99);if(controller.current!==null)throw Error('Stale pre-seek snapshot accepted');
  generation=reset.generation;reply(0);
  if(worker.messages.at(-1).time!==.2)throw Error('Seek replay target lost');
  worker.onerror();const count=worker.messages.length;controller.advance(.4);
  if(controller.available||!controller.error||!worker.terminated||worker.messages.length!==count)throw Error('Failed worker still receives requests');
  if(!updates)throw Error('Controller never reports updates');
  return 'PASS: bounded worker queue, latest-target coalescing, intermediate progress, seek generations, stale reply rejection, graceful worker failure.';
 }finally{globalThis.Worker=originalWorker;globalThis.URL=originalURL;}
})()
"""))


print(evaluate("""
(function(){
 const messages=[],queue=[],fakeSelf={postMessage:message=>messages.push(message)};
 const trajectory=simulate({...defaults,duration:1});
 let nextTimer=0;const cancelled=new Set();
 new Function('self','setTimeout','clearTimeout',flowWorkerSource)(fakeSelf,fn=>{queue.push({id:++nextTimer,fn});return nextTimer;},id=>cancelled.add(id));
 const reset=gen=>fakeSelf.onmessage({data:{type:'reset',generation:gen,parameters:{...defaults,duration:1},trajectory:trajectory.data,grid:32}});
 reset(1);fakeSelf.onmessage({data:{type:'advance',generation:1,time:1,requestId:1}});
 if(!queue.length)throw Error('Long advance did not yield');
 reset(2);fakeSelf.onmessage({data:{type:'advance',generation:2,time:.3,requestId:2}});
 const start=messages.length;let count=0;
 while(queue.length&&count++<1000){const timer=queue.shift();if(!cancelled.has(timer.id))timer.fn();}
 if(queue.length||messages.slice(start).some(message=>message.generation!==2))throw Error('Reset leaves old pump running');
 const result=messages.at(-1);
 if(!result.complete||result.requestId!==2||Math.abs(result.field.t-.3)>1e-8)throw Error('Reset during solve lost target or acknowledgement');
 return 'PASS: active solver reset cancels previous scheduled work and acknowledges only the current generation.';
})()
"""))

print(evaluate("""
(function(){
 const cases=[{eta:defaults.eta,rho:defaults.rho,duration:12,grid:40},{eta:.001002,rho:998.2,duration:2,grid:32},{eta:defaults.eta,rho:defaults.rho,duration:.5,grid:56}];
 for(const config of cases){
  const cfg={...defaults,...config},trajectory=simulate(cfg).data,solver=new FluidSolver(constants(cfg),cfg,config.grid);
  let index=0,steps=0;
  while(solver.time<cfg.duration-1e-8){
   while(index<trajectory.length-2&&trajectory[index+1].t<=solver.time)index++;
   const state=trajectory[index],speed=Math.max(Math.abs(solver.k.Ri*state.omega),Math.abs(solver.k.l*state.w));
   const dt=Math.min(1/60,cfg.duration-solver.time,solver.h*.5/Math.max(speed,1e-6));
   while(index<trajectory.length-2&&trajectory[index+1].t<=solver.time+dt)index++;
   const a=trajectory[index],b=trajectory[index+1],f=(solver.time+dt-a.t)/(b.t-a.t);
   const z=Object.fromEntries(Object.keys(a).map(key=>[key,a[key]+f*(b[key]-a[key])]));
   solver.step(dt,z);steps++;
   if(steps>100000)throw Error('Fluid time step stalls');
   if(!Object.values(solver.diagnostics).every(Number.isFinite))throw Error('Non-finite fluid diagnostics during full playback');
  }
  if(!solver.snapshot().cells.every(cell=>Object.values(cell).every(Number.isFinite)))throw Error('Non-finite full-run flow');
  if(solver.particles.some(point=>!Number.isFinite(point.x)||!Number.isFinite(point.y)))throw Error('Non-finite full-run tracers');
 }
 return 'PASS: complete 12-second default fluid run, water playback, and fine-grid playback remain finite.';
})()
"""))

print(evaluate("""
(function(){
 if(formatPlotValue(8.61e-8)==='0.000'||Number(formatPlotValue(8.61e-8))===0)throw Error('Small acceleration rounded to zero');
 if(formatPlotValue(-1.28e-8).indexOf('-')!==0||formatPlotValue(0)!=='0.000')throw Error('Plot formatter loses signs or exact zero');
 return 'PASS: chart values retain scientific precision for small nonzero acceleration.';
})()
"""))

# Native equation markup must be valid MathML with the right operator arities.
import re
import xml.etree.ElementTree as ET
markup=evaluate("Object.keys(equationGroups).map(equationBlock).join('')+modelSymbols()")
blocks=re.findall(r'<math\b.*?</math>',markup,flags=re.S)
arity={'mfrac':2,'msub':2,'msup':2,'mover':2,'msubsup':3}
for block in blocks:
    math_tree=ET.fromstring(block)
    for element in math_tree.iter():
        tag=element.tag.rsplit('}',1)[-1]
        if tag in arity and len(element)!=arity[tag]:
            raise AssertionError(f'Invalid MathML {tag} arity')
        if tag=='mtr' and len(element)!=3:
            raise AssertionError('Equation alignment must have three cells')
if len(blocks)<25:
    raise AssertionError('Missing equation or symbol markup')
print(f'PASS: {len(blocks)} valid MathML equation/symbol blocks, fractions, indices, derivatives and aligned rows.')
print(evaluate("""
(function(){
 const original={...p};location.hash='#model';layout();
 if(!elements.content.innerHTML.includes('Verified sources')||!elements.content.innerHTML.includes('Local shear approximation'))throw Error('Equation provenance missing');
 if(!elements.content.innerHTML.includes('symbol-table')||elements.content.innerHTML.includes('class="equation"'))throw Error('Equations remain unformatted');
 document.querySelector('#advanced-gap').value=p.gap;document.querySelector('#advanced-shell').value=p.shell;document.querySelector('#advanced-rho').value=p.rho;document.querySelector('#advanced-q0').value=p.q0;
 elements['apply-advanced'].listeners.click();
 if(Math.abs(run.k.mc-p.core/1000)>1e-12)throw Error('Model controls broken after layout change');
 let html='';const originalDownload=download;download=value=>{html=value;};report();download=originalDownload;
 if(!html.includes('<math')||!html.includes('Verified sources')||html.includes('<script'))throw Error('Export does not retain offline equations/sources');
 updateParameters(original);
 return 'PASS: equation provenance, definitions/units, model controls and offline typeset report.';
})()
"""))

js.JSGlobalContextRelease(ctx)
print('PASS: application JavaScript parses; numerical checks pass.')
