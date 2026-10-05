// Native MathML: structured, accessible equations without a network dependency.
export const mathMarkup={
 i:value=>`<mi>${value}</mi>`,n:value=>`<mn>${value}</mn>`,o:value=>`<mo>${value}</mo>`,
 row:(...values)=>`<mrow>${values.join('')}</mrow>`,
 sub:(base,index)=>`<msub>${base}<mtext>${index}</mtext></msub>`,
 pow:(base,power)=>`<msup>${base}<mn>${power}</mn></msup>`,
 frac:(a,b)=>`<mfrac><mrow>${a}</mrow><mrow>${b}</mrow></mfrac>`,
 dot:(base,count=1)=>`<mover accent="true">${base}<mo>${count===2?'¨':'˙'}</mo></mover>`,
 par:value=>`<mrow><mo>(</mo>${value}<mo>)</mo></mrow>`,
 fn:(name,value)=>`<mi mathvariant="normal">${name}</mi><mo>⁡</mo><mrow>${value}</mrow>`,
 root:value=>`<msqrt>${value}</msqrt>`
};
const {i,n,o,row,sub,pow,frac,dot,par,fn,root}=mathMarkup;
const R=i('R'),r=i('r'),l=i('ℓ'),q=i('q'),x=i('x'),g=i('g'),c=i('c'),a=i('α'),eta=i('η'),s=i('s'),v=dot(x),w=dot(q),xdd=dot(x,2),qdd=dot(q,2);
const Ri=sub(R,'i'),ms=sub(i('m'),'s'),mc=sub(i('m'),'c'),mf=sub(i('m'),'f'),md=sub(i('m'),'d'),mi=sub(i('m'),'I'),mstar='<msup><mi>m</mi><mo>∗</mo></msup>',rho=sub(i('ρ'),'f'),rhoc=sub(i('ρ'),'c'),Vc=sub(i('V'),'c'),Vf=sub(i('V'),'f'),Is=sub(i('I'),'s'),Ic=sub(i('I'),'c');
const eq=(lhs,rhs,relation='=')=>[lhs,rhs,relation],plus=o('+'),minus=o('−'),sin=value=>fn('sin',value),cos=value=>fn('cos',value),half=frac(n(1),n(2));
export const equationGroups={
 geometry:{label:'Geometry and volume',rows:[eq(Ri,R+minus+i('δ')),eq(l,Ri+minus+r+minus+i('h')),eq(Vc,frac(n(4)+i('π'),n(3))+pow(r,3)),eq(Vf,frac(n(4)+i('π'),n(3))+par(pow(Ri,3)+minus+pow(r,3)))]},
 mass:{label:'Material, buoyancy and inertia',rows:[eq(mc,rhoc+Vc),eq(md,rho+Vc),eq(mf,rho+Vf),eq(mstar,mc+minus+md),eq(mi,mc+plus+frac(pow(md,2),mf)),eq(i('M'),ms+plus+mc+plus+mf),eq(Is,frac(n(2),n(5))+ms+frac(pow(R,5)+minus+pow(Ri,5),pow(R,3)+minus+pow(Ri,3))),eq(Ic,frac(n(2),n(5))+mc+pow(r,2))]},
 rates:{label:'Coordinates and relative motion',rows:[eq(i('ω'),frac(v,R)),eq(s,w+plus+i('ω'))]},
 coefficients:{label:'Mass-matrix coefficients',rows:[eq(i('A'),i('M')+plus+frac(Is,pow(R,2))),eq(i('B'),mstar+l+cos(q)),eq(i('D'),mi+pow(l,2))]},
 motion:{label:'Coupled equations integrated by the solver',rows:[eq(i('A')+xdd+plus+i('B')+qdd,i('M')+g+sin(a)+plus+mstar+l+sin(q)+pow(w,2)+minus+frac(c+s,R)),eq(i('B')+xdd+plus+i('D')+qdd,minus+mstar+g+l+sin(par(q+minus+a))+minus+c+s)]},
 energy:{label:'Mechanical energy and Rayleigh dissipation',rows:[eq(i('T'),half+i('A')+pow(v,2)+plus+i('B')+v+w+plus+half+i('D')+pow(w,2)),eq(i('U'),minus+i('M')+g+x+sin(a)+minus+mstar+g+l+cos(par(q+minus+a))),eq(i('ℛ'),half+c+pow(s,2)),eq(i('P'),c+pow(s,2)),eq(frac(o('d')+par(i('T')+plus+i('U')),o('d')+i('t')),minus+i('P'))]},
 gap:{label:'Local gap-shear closure',rows:[eq(i('H')+par(i('μ')),root(pow(Ri,2)+minus+pow(l,2)+par(n(1)+minus+pow(i('μ'),2)))+minus+l+i('μ')+minus+r),eq(c,eta+pow(l,2)+n(2)+i('π')+pow(r,2)+'<msubsup><mo>∫</mo><mrow><mo>−</mo><mn>1</mn></mrow><mn>1</mn></msubsup>'+frac(n(1)+plus+pow(i('μ'),2),n(2)+i('H')+par(i('μ')))+o('d')+i('μ'))]},
 fluid:{label:'Incompressible flow in the translating shell frame',rows:[eq(o('∇')+o('·')+'<mi mathvariant="bold">u</mi>',n(0)),eq(rho+par(frac(o('∂')+'<mi mathvariant="bold">u</mi>',o('∂')+i('t'))+plus+par('<mi mathvariant="bold">u</mi>'+o('·')+o('∇'))+'<mi mathvariant="bold">u</mi>'),minus+o('∇')+i('p')+plus+eta+pow(o('∇'),2)+'<mi mathvariant="bold">u</mi>'+plus+rho+'<msub><mi mathvariant="bold">g</mi><mtext>eff</mtext></msub>')]},
 boundaries:{label:'Body acceleration and no-slip boundaries',rows:[eq('<msub><mi mathvariant="bold">g</mi><mtext>eff</mtext></msub>',par(g+sin(a)+minus+xdd+o(',')+minus+g+cos(a))),eq(sub('<mi mathvariant="bold">u</mi>','wall'),par(i('ω')+i('y')+o(',')+minus+i('ω')+x)),eq(sub('<mi mathvariant="bold">u</mi>','core'),par(l+cos(q)+w+o(',')+l+sin(q)+w))]},
 profile:{label:'Steady local Couette–Poiseuille profile',rows:[eq(eta+frac('<msup><mo>d</mo><mn>2</mn></msup>'+i('u'),o('d')+pow(i('y'),2)),frac(o('d')+i('p'),o('d')+i('ξ'))),eq(i('u')+par(i('y')),sub(i('U'),'0')+plus+frac(par(sub(i('U'),'1')+minus+sub(i('U'),'0'))+i('y'),i('h'))+plus+frac(frac(o('d')+i('p'),o('d')+i('ξ'))+i('y')+par(i('y')+minus+i('h')),n(2)+eta))]},
 terminal:{label:'Stationary-orbit existence and terminal speed',rows:[eq(i('M')+R+sin(a),mstar+l,'≤'),eq(sub(v,'∞'),frac(i('M')+g+pow(R,2)+sin(a),c)),eq(sub(q,'∞'),a+minus+fn('arcsin',par(frac(i('M')+R+sin(a),mstar+l))))]},
 contact:{label:'Contact forces required for rolling without slip',rows:[eq(i('F'),i('M')+xdd+plus+mstar+l+par(cos(q)+qdd+minus+sin(q)+pow(w,2))+minus+i('M')+g+sin(a)),eq(i('N'),i('M')+g+cos(a)+plus+mstar+l+par(sin(q)+qdd+plus+cos(q)+pow(w,2))),eq(sub(i('μ'),'required'),frac(o('|')+i('F')+o('|'),i('N')))]},
 reynolds:{label:'Orbital Reynolds estimate',rows:[eq(i('Re'),frac(rho+o('|')+l+s+o('|')+n(2)+r,eta))]}
};
export function equationBlock(key){const group=equationGroups[key];if(!group)throw Error('Unknown equation group: '+key);return `<figure class="math-block"><figcaption>${group.label}</figcaption><div class="math-scroll"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="${group.label}"><mtable columnalign="right center left" rowspacing="0.65em">${group.rows.map(([lhs,rhs,relation])=>`<mtr><mtd><mrow>${lhs}</mrow></mtd><mtd><mo>${relation}</mo></mtd><mtd><mrow>${rhs}</mrow></mtd></mtr>`).join('')}</mtable></math></div></figure>`;}
export function inlineSymbol(markup){return `<math xmlns="http://www.w3.org/1998/Math/MathML">${markup}</math>`;}
export function modelSymbols(){const entries=[
 [R+'<mo>,</mo>'+Ri+'<mo>,</mo>'+r,'Outer radius, cavity radius, inner-ball radius','m'],
 [l+'<mo>,</mo>'+i('h')+'<mo>,</mo>'+i('δ'),'Core orbit radius, minimum film, shell thickness','m'],
 [x+'<mo>,</mo>'+v+'<mo>,</mo>'+xdd,'Shell displacement, velocity, acceleration','m; m/s; m/s²'],
 [q+'<mo>,</mo>'+w+'<mo>,</mo>'+qdd,'Core-centre angle, orbital rate, orbital acceleration','rad; rad/s; rad/s²'],
 [i('ω')+'<mo>,</mo>'+s,'Clockwise shell rate, relative orbital rate','rad/s'],
 [mc+'<mo>,</mo>'+md+'<mo>,</mo>'+mf,'Core, displaced liquid, remaining liquid masses','kg'],
 [mstar+'<mo>,</mo>'+mi,'Buoyant mass and relative inertial mass','kg'],
 [rhoc+'<mo>,</mo>'+rho,'Solid-core density and liquid density','kg/m³'],
 [Is+'<mo>,</mo>'+Ic,'Shell and solid-core moments of inertia','kg·m²'],
 [eta+'<mo>,</mo>'+c,'Dynamic viscosity and orbital resistance','Pa·s; kg·m²/s'],
 [i('T')+'<mo>,</mo>'+i('U')+'<mo>,</mo>'+i('P'),'Kinetic energy, potential energy, dissipated power','J; J; W'],
 [i('α')+'<mo>,</mo>'+g,'Ramp angle and gravitational acceleration','rad; m/s²'],
 [ms+'<mo>,</mo>'+i('M'),'Shell mass and total apparatus mass','kg'],
 [i('A')+'<mo>,</mo>'+i('B')+'<mo>,</mo>'+i('D'),'Mass-matrix coefficients','kg; kg·m; kg·m²'],
 [i('H')+'<mo>,</mo>'+i('μ'),'Radial gap and direction cosine','m; dimensionless'],
 ['<mi mathvariant="bold">u</mi>'+o(',')+i('p'),'Fluid velocity and pressure','m/s; Pa'],
 [i('y')+'<mo>,</mo>'+i('ξ'),'Across-film and along-film coordinates','m'],
 [sub(i('U'),'0')+'<mo>,</mo>'+sub(i('U'),'1'),'Local gap boundary speeds','m/s'],
 [i('F')+'<mo>,</mo>'+i('N')+'<mo>,</mo>'+sub(i('μ'),'required'),'Ramp friction, normal force, required friction ratio','N; N; dimensionless']
 ];return `<div class="table-scroll"><table class="data-table symbol-table"><thead><tr><th>Symbol</th><th>Meaning</th><th>SI unit</th></tr></thead><tbody>${entries.map(([symbol,meaning,unit])=>`<tr><td>${inlineSymbol(row(symbol))}</td><td>${meaning}</td><td>${unit}</td></tr>`).join('')}</tbody></table></div>`;}
export function verifiedSources(){return `<section class="card body-card full model-sources"><h2>Verified sources and their scope</h2><ol>
<li><a href="https://personal.math.ubc.ca/~njb/Research/sbx1.pdf" target="_blank" rel="noopener">Balmforth, Bush, Vener &amp; Young (2007), <em>Dissipative descent: rocking and rolling down an incline</em></a><span>Journal of Fluid Mechanics 590, 295–318 · DOI: 10.1017/S0022112007008051.</span><p>Sections 2.1–2.2 motivate the distinction between buoyancy and relative inertia and the importance of lubrication. The paper studies cylinders; it does not verify this app’s fixed-orbit sphere closure.</p></li>
<li><a href="https://ocw.mit.edu/courses/16-07-dynamics-fall-2009/resources/mit16_07f09_lec20/" target="_blank" rel="noopener">MIT OpenCourseWare, Dynamics, Lecture 20: Energy Methods and Lagrange’s Equations</a><p>Supports the analytical-mechanics framework. The specific mass matrix and dissipative sphere equations below are derived for this app.</p></li>
<li><a href="https://www.dgp.toronto.edu/people/stam/reality/Research/pdf/ns.pdf" target="_blank" rel="noopener">Stam (1999), <em>Stable Fluids</em></a><span>SIGGRAPH ’99 · DOI: 10.1145/311535.311548.</span><p>Section 2.2 describes semi-Lagrangian advection, implicit viscosity and pressure projection. Moving raster walls and the one-way coupling here are implementation approximations.</p></li>
<li><a href="https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101567" target="_blank" rel="noopener">NIST steel material-property table</a><p>Supports the nominal default density 7850 kg/m³. Each alternative material preset links to its own property source; density alone does not model elasticity, porosity or a nonuniform ball.</p></li>
</ol><p class="source-note">Primary publications were checked for the stated claims. The spherical geometry, energy identity, contact-force balances and terminal solution are direct derivations; the gap resistance is an explicitly approximate closure. Numerical tests verify implementation, not experimental agreement.</p></section>`;}
