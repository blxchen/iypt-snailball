import io
import json
import math
import unittest
from backend.model import simulate, parameters, constants, DEFAULTS, steel_mass, derivative
from backend.measurements import analyze, interval, timestamp
from serve import Handler
from backend.flow import gap_flow

class ModelTests(unittest.TestCase):
    def test_energy_and_viscosity(self):
        baseline=simulate()
        self.assertLess(baseline['statistics']['residual'],1e-7)
        self.assertTrue(all(z['power']>=0 for z in baseline['data']))
        slower=simulate({'eta':150})
        self.assertLess(slower['statistics']['mean'],baseline['statistics']['mean'])

    def test_custom_samples(self):
        result=simulate({'duration':1},[0,.123,1,.123])
        self.assertEqual([z['t'] for z in result['samples']],[0,.123,1,.123])
        self.assertEqual(result['samples'][0]['x'],0)
        with self.assertRaises(ValueError):
            simulate({'duration':1},[2])

    def test_invalid_configuration_and_step_budget(self):
        for p in ({'eta':-1},{'duration':float('nan')},{'R':25,'r':30},{'drag':0},{'unknown':4}):
            with self.subTest(p=p),self.assertRaises(ValueError):
                constants(parameters(p))
        with self.assertRaisesRegex(ValueError,'million'):
            simulate({'duration':300,'eta':200,'gap':.05})

    def test_undamped_energy(self):
        result=simulate({'eta':0,'duration':2})
        self.assertLess(result['statistics']['residual'],1e-7)
        self.assertFalse(result['reynolds_defined'])

    def test_recoil_is_not_clamped(self):
        result=simulate({'q0':30,'duration':2})
        data=result['data']
        self.assertTrue(any(z['v'] < -0.001 for z in data))
        self.assertTrue(any(b['x'] < a['x'] for a,b in zip(data,data[1:])))
        self.assertLess(result['statistics']['residual'],1e-7)

    def test_gap_resistance_and_liquids(self):
        default=constants(parameters())
        smaller_gap=constants(parameters({'gap':.1}))
        self.assertGreater(smaller_gap['c'],default['c'])
        self.assertGreater(default['c'],6*math.pi*97*default['r']*default['l']**2)
        water=simulate({'eta':.001002,'rho':998.2,'duration':2})
        oil=simulate({'duration':2})
        self.assertNotEqual(water['k']['mf'],oil['k']['mf'])
        self.assertGreater(water['statistics']['mean'],oil['statistics']['mean'])

    def test_solid_steel_mass_and_radius(self):
        for radius in (10,20,23):
            p=parameters({'r':radius,'core':1})
            expected=7850*4*math.pi/3*(radius/1000)**3
            k=constants(p)
            self.assertAlmostEqual(k['mc'],expected)
            self.assertAlmostEqual(p['core']/1000,expected)
            self.assertAlmostEqual(k['Icore'],.4*expected*(radius/1000)**2)
        self.assertAlmostEqual(steel_mass(20)/steel_mass(10),8)

    def test_material_density_updates_mass_and_dynamics(self):
        baseline=constants(parameters())
        for density in (2700,8940,19250,5300):
            config=parameters({'core_density':density,'core':1,'duration':.2})
            k=constants(config)
            expected=density*4*math.pi/3*(config['r']/1000)**3
            self.assertAlmostEqual(k['mc'],expected)
            self.assertAlmostEqual(config['core']/1000,expected)
            self.assertAlmostEqual(k['Icore'],.4*expected*k['r']**2)
            self.assertEqual(k['md'],baseline['md'])
            self.assertEqual(k['c'],baseline['c'])
            result=simulate(config)
            self.assertLess(result['statistics']['residual'],1e-7)
            self.assertTrue(all(math.isfinite(z['a']) for z in result['data']))
        for density in (0,-1,float('nan'),30001,900):
            with self.subTest(density=density),self.assertRaises(ValueError):
                simulate({'core_density':density,'duration':.1})
        self.assertNotEqual(simulate({'core_density':2700,'duration':.2})['data'][-1]['v'],
                            simulate({'core_density':19250,'duration':.2})['data'][-1]['v'])

    def test_mean_fluid_inertia_from_kinetic_energy(self):
        p=parameters();k=constants(p);q=.43;v=.03;w=.6
        ex=k['l']*math.cos(q)*w;ey=k['l']*math.sin(q)*w
        ratio=k['md']/k['mf']
        direct=.5*p['shell']/1000*v*v+.5*k['I']*(v/k['R'])**2
        direct+=.5*k['mc']*((v+ex)**2+ey*ey)
        direct+=.5*k['mf']*((v-ratio*ex)**2+(ratio*ey)**2)
        reduced=.5*k['A']*v*v+k['b']*math.cos(q)*v*w+.5*k['D']*w*w
        self.assertAlmostEqual(direct,reduced,places=14)
        self.assertGreater(k['mi'],k['mc'])
        self.assertLess(k['m'],k['mc'])
        for angle in range(-180,181,15):
            self.assertGreater(k['A']*k['D']-(k['b']*math.cos(math.radians(angle)))**2,0)

    def test_instantaneous_energy_and_damping_sign(self):
        k=constants(parameters())
        for q,v,w in ((.3,.03,.6),(-.7,-.02,.1),(1.2,.04,-1.1)):
            _,a,_,wdot=derivative((0,v,q,w),k)
            B=k['b']*math.cos(q);rel=w+v/k['R']
            dEdt=(k['A']*v+B*w)*a+(B*v+k['D']*w)*wdot
            dEdt+=(-k['b']*math.sin(q)*v*w+k['m']*k['g']*k['l']*math.sin(q-k['alpha']))*w
            dEdt-=k['M']*k['g']*math.sin(k['alpha'])*v
            self.assertAlmostEqual(dEdt,-k['c']*rel*rel,places=13)
            qx=k['A']*a+B*wdot-k['M']*k['g']*math.sin(k['alpha'])-k['b']*math.sin(q)*w*w
            qq=B*a+k['D']*wdot+k['m']*k['g']*k['l']*math.sin(q-k['alpha'])
            self.assertAlmostEqual(qx,-k['c']*rel/k['R'],places=13)
            self.assertAlmostEqual(qq,-k['c']*rel,places=13)
        # Counterclockwise orbit and clockwise shell share a rotation at w=-v/R.
        state=(0,.03,.4,-.03/k['R'])
        self.assertEqual(derivative(state,k),derivative(state,{**k,'c':0}))

    def test_ground_forces_from_body_accelerations(self):
        run=simulate({'q0':30,'duration':1});k=run['k']
        for z in run['data']:
            eddot=(k['l']*(math.cos(z['q'])*z['core_angular_acceleration']-math.sin(z['q'])*z['w']**2),
                    k['l']*(math.sin(z['q'])*z['core_angular_acceleration']+math.cos(z['q'])*z['w']**2))
            core_acc=(z['a']+eddot[0],eddot[1])
            fluid_acc=(z['a']-k['md']/k['mf']*eddot[0],-k['md']/k['mf']*eddot[1])
            px=run['parameters']['shell']/1000*z['a']+k['mc']*core_acc[0]+k['mf']*fluid_acc[0]
            py=k['mc']*core_acc[1]+k['mf']*fluid_acc[1]
            self.assertAlmostEqual(z['friction']+k['M']*k['g']*math.sin(k['alpha']),px,places=12)
            self.assertAlmostEqual(z['normal']-k['M']*k['g']*math.cos(k['alpha']),py,places=12)
            self.assertAlmostEqual(z['torque']*z['w']+z['shell_torque']*z['omega'],-z['power'],places=13)
        undamped=simulate({'eta':0,'duration':.1})
        self.assertIsNone(undamped['statistics']['Re'])
        self.assertTrue(all(z['Re'] is None for z in undamped['data']))

    def test_step_resolves_coupled_damping(self):
        run=simulate({'duration':.1});k=run['k']
        for degrees in range(-180,181,15):
            B=k['b']*math.cos(math.radians(degrees))
            exact=k['c']*(k['A']+k['D']/k['R']**2-2*B/k['R'])/(k['A']*k['D']-B*B)
            self.assertLessEqual(exact,k['dampingRateBound']*(1+1e-12))
        self.assertLessEqual(run['dt']*k['dampingRateBound'],.08*(1+1e-12))
        self.assertLessEqual(run['dt']*k['frequencyBound'],.08*(1+1e-12))

    def test_horizontal_rest_and_repeatability(self):
        first=simulate({'angle':0,'duration':1})
        self.assertTrue(all(z['x']==0 and z['v']==0 and z['w']==0 for z in first['data']))
        cfg={'q0':30,'duration':1}
        self.assertEqual(simulate(cfg)['data'],simulate(cfg)['data'])

class FlowTests(unittest.TestCase):
    def test_couette_boundary_conditions(self):
        f=gap_flow({'eta':2,'gap_mm':.5,'u0':.01,'u1':.03})
        self.assertEqual(f['profile'][0]['u'],.01)
        self.assertAlmostEqual(f['profile'][-1]['u'],.03)
        self.assertAlmostEqual(f['profile'][32]['u'],.02)
        self.assertAlmostEqual(f['profile'][0]['shear'],80)
        self.assertAlmostEqual(f['dissipation_per_area'],1.6)
    def test_poiseuille_pressure_balance(self):
        f=gap_flow({'eta':2,'gap_mm':1,'u0':0,'u1':0,'pressure_gradient':-1000})
        self.assertAlmostEqual(f['profile'][32]['u'],.0000625)
        self.assertGreater(f['volume_flux_per_width'],0)
        for i in range(1,64):
            a,b,c=f['profile'][i-1:i+2]
            dy=b['y']-a['y']
            self.assertAlmostEqual(2*(c['u']-2*b['u']+a['u'])/dy**2,-1000,places=6)
    def test_invalid_viscosity(self):
        with self.assertRaises(ValueError):
            gap_flow({'eta':0})

class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.payload={'rows':[{'t':0,'x':0},{'t':.3,'x':.09},{'t':1,'x':1},{'t':2,'x':4}],
                      'distance_unit':'m','sigma_x':.001,'sigma_t':.01}

    def test_irregular_quadratic_derivatives(self):
        result=analyze(self.payload)
        self.assertAlmostEqual(result['data'][1]['v'],.6)
        self.assertAlmostEqual(result['data'][2]['v'],2)
        for z in result['data']:
            self.assertAlmostEqual(z['a'],2)
            self.assertGreater(z['sigma_a'],0)
        self.assertAlmostEqual(result['summary']['mean_velocity'],2)

    def test_units_clock_frames_and_origins(self):
        result=analyze({'rows':[{'t':'1:00','x':10},{'t':'1830f','x':20},{'t':'1:02','x':30}],
                        'fps':30,'distance_unit':'cm','time_offset':'1:00','position_offset':10})
        self.assertEqual([z['t'] for z in result['data']],[0,1,2])
        self.assertAlmostEqual(result['summary']['displacement'],.2)
        self.assertAlmostEqual(result['summary']['mean_velocity'],.1)
        self.assertAlmostEqual(timestamp('1:02:03.5'),3723.5)
        self.assertAlmostEqual(timestamp('120f',60),2)

    def test_bad_measurements(self):
        for rows in ([{'t':0,'x':0}]*3,[{'t':-1,'x':0},{'t':1,'x':2},{'t':2,'x':3}],
                     [{'t':0,'x':''},{'t':1,'x':2},{'t':2,'x':3}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                analyze({'rows':rows})
        for value in ('1:60','1.2:03','-1','NaN','3.5f','f',''):
            with self.subTest(value=value),self.assertRaises(ValueError):
                timestamp(value)

    def test_supplied_velocity_preserved(self):
        for row in self.payload['rows']:
            row['v']=7
        data=analyze(self.payload)['data']
        self.assertTrue(all(z['v']==7 and z['sigma_v'] is None for z in data))

    def test_time_interval_interpolation(self):
        result=interval({**self.payload,'t_start':.3,'t_end':1.5})
        self.assertAlmostEqual(result['duration'],1.2)
        self.assertAlmostEqual(result['displacement'],2.41)
        self.assertGreater(result['sigma_velocity'],0)
        with self.assertRaises(ValueError):
            interval({**self.payload,'t_start':0,'t_end':3})

    def test_distance_interval_and_backward_motion(self):
        payload={'rows':[{'t':0,'x':0},{'t':1,'x':10},{'t':2,'x':5},{'t':3,'x':15}],
                 'distance_unit':'cm','mode':'distance','x_start':8,'x_end':6}
        result=interval(payload)
        self.assertAlmostEqual(result['t_start'],.8)
        self.assertAlmostEqual(result['t_end'],1.8)
        self.assertAlmostEqual(result['mean_velocity'],-.02)
        summary=analyze(payload)['summary']
        self.assertAlmostEqual(summary['path_length'],.25)
        self.assertAlmostEqual(summary['displacement'],.15)

class APIHarness(Handler):
    def __init__(self,path,payload):
        raw=payload if isinstance(payload,bytes) else json.dumps(payload).encode()
        self.path=path
        self.headers={'Content-Length':str(len(raw))}
        self.rfile=io.BytesIO(raw)
        self.wfile=io.BytesIO()
        self.status=None
        self.response_headers={}
    def send_response(self,status):
        self.status=status
    def send_header(self,key,value):
        self.response_headers[key]=value
    def end_headers(self):
        pass
    def result(self):
        return json.loads(self.wfile.getvalue())

class APITests(unittest.TestCase):
    def request(self,path,payload):
        h=APIHarness(path,payload)
        h.do_POST()
        return h
    def test_routes_and_health(self):
        h=APIHarness('/api/health',{})
        h.do_GET()
        self.assertEqual(h.status,200)
        self.assertEqual(h.result()['version'],2)
        self.assertEqual(self.request('/api/nope',{}).status,404)
    def test_invalid_json_and_shape(self):
        for body in (b'{bad',[],{'rows':[]}):
            h=self.request('/api/analyze',body)
            self.assertEqual(h.status,400)
            self.assertIn('error',h.result())
    def test_simulation_and_comparison(self):
        h=self.request('/api/simulate',{'parameters':{'duration':1},'timestamps':[0,.5,1]})
        self.assertEqual(h.status,200)
        self.assertEqual(len(h.result()['samples']),3)
        rows=h.result()['samples']
        compare=self.request('/api/analyze',{'rows':rows,'compare_model':True,'parameters':{'duration':1}})
        self.assertEqual(compare.status,200)
        self.assertEqual(compare.result()['comparison']['samples'],3)
        self.assertLess(compare.result()['comparison']['velocity_rmse'],1e-12)
    def test_flow_endpoint(self):
        h=self.request('/api/flow',{'eta':2,'u1':.01,'gap_mm':.5})
        self.assertEqual(h.status,200)
        self.assertEqual(len(h.result()['profile']),65)

    def test_measure_endpoint(self):
        h=self.request('/api/measure',{'rows':[{'t':0,'x':0},{'t':1,'x':1},{'t':2,'x':2}],
                                       't_start':.5,'t_end':1.5})
        self.assertEqual(h.status,200)
        self.assertAlmostEqual(h.result()['mean_velocity'],1)

if __name__=='__main__':
    unittest.main()
