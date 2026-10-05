// Dependency-free perspective renderer. Every geometric position comes from the ODE state.
export const camera={yaw:.35,pitch:.30,zoom:1};
export function resetCamera(){camera.yaw=.35;camera.pitch=.30;camera.zoom=1;}
export function bindOrbit(canvas,onChange){if(!canvas)return;let pointer=null;
 canvas.addEventListener('pointerdown',e=>{pointer={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture?.(e.pointerId);canvas.classList.add('orbiting');});
 canvas.addEventListener('pointermove',e=>{if(!pointer||pointer.id!==e.pointerId)return;camera.yaw-=(e.clientX-pointer.x)*.008;camera.pitch=Math.max(-.15,Math.min(1.35,camera.pitch+(e.clientY-pointer.y)*.006));pointer.x=e.clientX;pointer.y=e.clientY;onChange();});
 const release=e=>{if(pointer?.id===e.pointerId){pointer=null;canvas.classList.remove('orbiting');}};
 canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
 canvas.addEventListener('wheel',e=>{e.preventDefault();camera.zoom=Math.max(.55,Math.min(2.4,camera.zoom*Math.exp(-e.deltaY*.001)));onChange();},{passive:false});
 canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','Home'].includes(e.key))return;e.preventDefault();if(e.key==='Home')resetCamera();if(e.key==='ArrowLeft')camera.yaw-=.1;if(e.key==='ArrowRight')camera.yaw+=.1;if(e.key==='ArrowUp')camera.pitch=Math.min(1.35,camera.pitch+.1);if(e.key==='ArrowDown')camera.pitch=Math.max(-.15,camera.pitch-.1);if(e.key==='+')camera.zoom=Math.min(2.4,camera.zoom*1.1);if(e.key==='-')camera.zoom=Math.max(.55,camera.zoom/1.1);onChange();});
}
export function renderOrbitScene(canvas,state,k,liquidColor='#d5b677',section=false,fluid=null,fluidMode='tracers',corePalette=null){const rect=canvas.getBoundingClientRect(),W=rect.width,H=rect.height,dpr=window.devicePixelRatio||1;if(!W||!H)return;canvas.width=W*dpr;canvas.height=H*dpr;const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const R=k.R,alpha=k.alpha,yaw=section?0:camera.yaw,pitch=section?0:camera.pitch,dist=R*7.5/camera.zoom,focal=Math.min(W,H)*1.45,centerY=R*.62,ox=W*.46,oy=H*.55;
 // Orbit camera rotates in world coordinates; inclination remains a physical world angle.
 const projection=([x,y,z])=>{const X=x*Math.cos(alpha)+y*Math.sin(alpha),Y=-x*Math.sin(alpha)+y*Math.cos(alpha)-centerY;const u=Math.cos(yaw)*X-Math.sin(yaw)*z,z1=Math.sin(yaw)*X+Math.cos(yaw)*z,v=Math.cos(pitch)*Y-Math.sin(pitch)*z1,depth=dist-Math.sin(pitch)*Y-Math.cos(pitch)*z1;return {x:ox+focal*u/depth,y:oy-focal*v/depth,depth,scale:focal/depth};};
 const line=(points,color,width=1)=>{ctx.beginPath();points.forEach((p,i)=>{const q=projection(p);i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y);});ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();};
 const poly=(points,fill,stroke)=>{ctx.beginPath();points.forEach((p,i)=>{const q=projection(p);i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y);});ctx.closePath();ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=.6;ctx.stroke();}};
 ctx.clearRect(0,0,W,H);
 const half=R*5,width=R*2.4,thick=R*.15;
 poly([[-half,-thick,-width],[half,-thick,-width],[half,0,-width],[-half,0,-width]],'#b5a4cc');
 poly([[-half,0,width],[half,0,width],[half,-thick,width],[-half,-thick,width]],'#a69abd');
 poly([[-half,0,-width],[half,0,-width],[half,0,width],[-half,0,width]],'#c7bcdf','#b7a8cc');
 const spacing=R*.6,shift=((state.x%spacing)+spacing)%spacing;
 for(let j=-9;j<=9;j++){const x=j*spacing-shift;line([[x,.00002,-width],[x,.00002,width]],'#ede6f26a',.7);}
 for(let j=-3;j<=3;j++)line([[-half,.00003,j*R*.65],[half,.00003,j*R*.65]],'#ede6f24a',.6);
 // Contact shadow, projected onto the ramp rather than painted at a fixed screen angle.
 for(let j=12;j>0;j--){const radius=R*(.22+j*.07),points=Array.from({length:40},(_,i)=>{const t=i*Math.PI/20;return [radius*Math.cos(t),.00005,radius*.78*Math.sin(t)];});poly(points,`rgba(54,37,71,${.013+j*.0007})`);}
 const center=projection([0,R,0]),radius=R*center.scale;
 // Render the filled cavity separately from the clear shell. Tint is a visual aid.
 const cavityRadius=radius*k.Ri/R;
 const liquid=ctx.createRadialGradient(center.x-cavityRadius*.35,center.y-cavityRadius*.4,cavityRadius*.03,center.x+cavityRadius*.15,center.y+cavityRadius*.2,cavityRadius*1.15);
 liquid.addColorStop(0,'#fffaf49a');liquid.addColorStop(.25,liquidColor+'70');liquid.addColorStop(.65,liquidColor+'a0');liquid.addColorStop(1,liquidColor+'ca');
 ctx.fillStyle=liquid;ctx.beginPath();ctx.arc(center.x,center.y,cavityRadius,0,Math.PI*2);ctx.fill();
 ctx.strokeStyle=liquidColor+'cc';ctx.lineWidth=1.5;ctx.stroke();
 const glass=ctx.createRadialGradient(center.x-radius*.4,center.y-radius*.5,radius*.04,center.x,center.y,radius*1.2);glass.addColorStop(0,'#ffffff35');glass.addColorStop(.6,'#ffffff08');glass.addColorStop(1,'#ad92c735');ctx.fillStyle=glass;ctx.beginPath();ctx.arc(center.x,center.y,radius,0,Math.PI*2);ctx.fill();
 // These are passive markers/field samples from the computed 2D slice, not bubbles.
 if(fluid&&fluidMode!=='off'){
  if(fluidMode==='tracers'){for(const point of fluid.particles){const a=projection([point.px,R+point.py,0]),b=projection([point.x,R+point.y,0]);ctx.strokeStyle='#fffc';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.fillStyle='#fff9';ctx.beginPath();ctx.arc(b.x,b.y,1.3,0,Math.PI*2);ctx.fill();}}
  else if(fluidMode==='velocity'){for(let j=0;j<fluid.field.cells.length;j+=5){const cell=fluid.field.cells[j],a=projection([cell.x,R+cell.y,0]);const scale=Math.min(.04,fluid.field.grid?R*.3/Math.max(fluid.field.diagnostics.maxSpeed,1e-6):.04),b=projection([cell.x+cell.u*scale,R+cell.y+cell.v*scale,0]);ctx.strokeStyle='#ffffffc0';ctx.lineWidth=.9;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);const angle=Math.atan2(b.y-a.y,b.x-a.x);ctx.lineTo(b.x-3*Math.cos(angle-.5),b.y-3*Math.sin(angle-.5));ctx.moveTo(b.x,b.y);ctx.lineTo(b.x-3*Math.cos(angle+.5),b.y-3*Math.sin(angle+.5));ctx.stroke();}}
  else if(fluidMode==='pressure'){const span=Math.max(1e-8,...fluid.field.cells.map(cell=>Math.abs(cell.pressure)));for(const cell of fluid.field.cells){const point=projection([cell.x,R+cell.y,0]),fraction=cell.pressure/span;ctx.fillStyle=fraction>0?`rgba(224,105,62,${Math.abs(fraction)*.65})`:`rgba(70,137,214,${Math.abs(fraction)*.65})`;ctx.beginPath();ctx.arc(point.x,point.y,Math.max(1,radius*2/fluid.field.grid),0,Math.PI*2);ctx.fill();}}
 }
 const coreWorld=[k.l*Math.sin(state.q),R-k.l*Math.cos(state.q),0],core=projection(coreWorld),r=k.r*core.scale;
 const palette=corePalette||['#f7fbff','#d8e0e8','#9ca9b5','#65717c','#303942','#84929f'];const metal=ctx.createRadialGradient(core.x-r*.4,core.y-r*.45,r*.02,core.x+r*.18,core.y+r*.24,r*1.12);metal.addColorStop(0,palette[0]);metal.addColorStop(.17,palette[1]);metal.addColorStop(.4,palette[2]);metal.addColorStop(.65,palette[3]);metal.addColorStop(.88,palette[4]);metal.addColorStop(1,palette[5]);ctx.fillStyle=metal;ctx.beginPath();ctx.arc(core.x,core.y,r,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#5f526466';ctx.lineWidth=.6;ctx.stroke();
 // A transparent foreground tint places the visible core inside the liquid volume.
 ctx.fillStyle=liquidColor+'18';ctx.beginPath();ctx.arc(center.x,center.y,cavityRadius,0,Math.PI*2);ctx.fill();
 // Longitude/latitude lines mark true shell rolling, including reverse rotation.
 const roll=-state.x/R;
 const shellPoint=(theta,phi)=>{const x=R*Math.sin(theta)*Math.cos(phi),y=R*Math.cos(theta),z=R*Math.sin(theta)*Math.sin(phi);return [x*Math.cos(roll)-y*Math.sin(roll),R+x*Math.sin(roll)+y*Math.cos(roll),z];};
 for(let j=0;j<5;j++){const phi=j*Math.PI/5;line(Array.from({length:65},(_,i)=>shellPoint(i*Math.PI/32,phi)),j===0?'#f8f5ffb0':'#e3d6f260',j===0?1.25:.75);}
 for(let j=1;j<4;j++)line(Array.from({length:65},(_,i)=>shellPoint(j*Math.PI/4,i*Math.PI/32)),'#e5d8f16a',.75);
 const rim=ctx.createLinearGradient(center.x-radius,center.y-radius,center.x+radius,center.y+radius);rim.addColorStop(0,'#fff');rim.addColorStop(.4,'#e8dbf7');rim.addColorStop(.8,'#a38cb6');rim.addColorStop(1,'#d5c6e4');ctx.strokeStyle=rim;ctx.lineWidth=2;ctx.beginPath();ctx.arc(center.x,center.y,radius,0,Math.PI*2);ctx.stroke();ctx.strokeStyle='#fff9';ctx.lineWidth=3;ctx.beginPath();ctx.arc(center.x-radius*.03,center.y-radius*.02,radius*.88,3.5,4.65);ctx.stroke();
 if(section){line([[0,R,0],coreWorld],'#6e548b',1);ctx.fillStyle='#82659a';ctx.font='10px sans-serif';ctx.fillText('ℓ',core.x+7,(center.y+core.y)/2);}
 const gravity=projection([R*2.1,R*2,0]),ground=projection([R*2.1+R*.65*Math.sin(alpha),R*2-R*.65*Math.cos(alpha),0]);ctx.strokeStyle='#a89ab7';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(gravity.x,gravity.y);ctx.lineTo(ground.x,ground.y);ctx.stroke();ctx.fillStyle='#a89ab7';ctx.font='10px sans-serif';ctx.fillText('g',ground.x+6,ground.y);ctx.fillText(`R = ${(R*1000).toFixed(1)} mm`,center.x+radius+15,center.y-radius*.75);ctx.fillText(`α = ${(alpha*180/Math.PI).toFixed(1)}°`,25,H-45);
 return {center,radius,core};
}
