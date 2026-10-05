"""Verify a running local server: python3 tests/check_http.py [port]."""
import json
import sys
import urllib.request
base='http://127.0.0.1:'+str(int(sys.argv[1]) if len(sys.argv)>1 else 8000)
def call(path,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    request=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if data else {})
    with urllib.request.urlopen(request,timeout=30) as response:
        assert response.status==200
        if '/api/' not in path:
            assert response.headers.get('Cache-Control')=='no-cache'
        if path.endswith('.js'):
            assert response.headers.get_content_type() in ('text/javascript','application/javascript')
        content=response.read()
        return json.loads(content) if '/api/' in path else content
assert call('/api/health')['version']==2
for path in ('/','/app.js','/measurements.js','/physics.js','/liquids.js','/materials.js','/equations.js','/model-page.js','/scene3d.js','/fluid.js','/fluid-worker.js','/fluid-view.js','/styles.css','/PHYSICS.md'):
    assert len(call(path))>100
sample=call('/api/simulate',{'parameters':{'duration':1},'timestamps':[0,.25,1]})
assert [z['t'] for z in sample['samples']]==[0,.25,1]
assert sample['k']['coreDensity']==7850
assert abs(sample['parameters']['core']-400.07533180984267)<1e-8
assert 'mu_required' in sample['samples'][-1]
assert sample['statistics']['residual']<1e-7
custom=call('/api/simulate',{'parameters':{'core_density':8940,'duration':.1}})
assert custom['k']['coreDensity']==8940
assert abs(custom['parameters']['core']-8940*4*3.141592653589793/3*.023**3*1000)<1e-8
payload={'rows':[{'t':'0:00','x':0},{'t':'15f','x':20},{'t':'0:01','x':40}],
         'fps':30,'distance_unit':'mm','sigma_x':1,'sigma_t':.01}
analysis=call('/api/analyze',payload)
assert abs(analysis['summary']['mean_velocity']-.04)<1e-12
interval=call('/api/measure',{**payload,'mode':'distance','x_start':10,'x_end':30})
assert abs(interval['duration']-.5)<1e-12
assert abs(interval['mean_velocity']-.04)<1e-12
flow=call('/api/flow',{'eta':2,'gap_mm':.5,'u1':.02})
assert abs(flow['profile'][-1]['u']-.02)<1e-12
assert flow['dissipation_per_area']>0
print('PASS: Stokes gap flow; live HTTP assets, health, Python simulation, measurement analysis, and distance interval.')
