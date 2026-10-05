// Nominal solid-material densities. Alloy, porosity and temperature can change them.
export const materials=[
 {id:'steel',name:'Steel',density:7850,source:'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101567',palette:['#f7fbff','#d8e0e8','#9ca9b5','#65717c','#303942','#84929f']},
 {id:'aluminium',name:'Aluminium',density:2700,source:'https://www.plansee.com/100/content/Plansee_100Jahre-Festschrift_EN.pdf',palette:['#ffffff','#eff2f5','#c5ccd3','#969ea6','#626970','#b4bdc6']},
 {id:'copper',name:'Copper',density:8940,source:'https://archive.copper.org/resources/properties/129_6/characteristics_properties.php',palette:['#fff1dc','#f1c5a0','#c68757','#8b502f','#4f291b','#b37549']},
 {id:'tungsten',name:'Tungsten',density:19250,source:'https://plansee-group.com/en/company/tungsten',palette:['#edf1f5','#bdc6ce','#818d97','#505c66','#242d35','#73808b']}
];
export function matchingMaterial(p){return materials.find(material=>Math.abs(material.density-p.core_density)<1e-6)||null;}
