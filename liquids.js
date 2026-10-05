// Representative Newtonian properties at the stated temperature, not temperature curves.
export const liquids=[
 {id:'silicone100k',name:'Silicone oil · 100,000 cSt',eta:97,rho:970,temp:25,color:'#e3a238',source:'https://api.pennwhite.co.uk/pdf/TDS%20Silicone%20Oil.pdf'},
 {id:'silicone10k',name:'Silicone oil · 10,000 cSt',eta:9.7,rho:970,temp:25,color:'#d8ad4c',source:'https://api.pennwhite.co.uk/pdf/TDS%20Silicone%20Oil.pdf'},
 {id:'silicone1k',name:'Silicone oil · 1,000 cSt',eta:.97,rho:970,temp:25,color:'#65b7c5',source:'https://api.pennwhite.co.uk/pdf/TDS%20Silicone%20Oil.pdf'},
 {id:'glycerol',name:'Glycerol · nominal pure',eta:1.5,rho:1260,temp:20,color:'#d4ba45',source:'https://physicsme.ir/en/iypt/2027/snail-ball-en/'},
 {id:'water',name:'Water',eta:.001002,rho:998.2,temp:20,color:'#48a9df',source:'https://www.iapws.org/relguide/LiquidWater.pdf'}
];
export function matchingLiquid(p){return liquids.find(l=>Math.abs(l.eta-p.eta)<1e-10&&Math.abs(l.rho-p.rho)<1e-6);}
