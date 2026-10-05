"""Check terminal speed without imposing zero acceleration or clamping velocity."""
import math
import unittest
from backend.model import simulate, derivative


def rk4(state, h, k):
    def add(y, d, factor):
        return tuple(a + factor*b for a, b in zip(y, d))
    d1 = derivative(state, k)
    d2 = derivative(add(state, d1, h/2), k)
    d3 = derivative(add(state, d2, h/2), k)
    d4 = derivative(add(state, d3, h), k)
    return tuple(y+h/6*(a+2*b+2*c+d) for y,a,b,c,d in zip(state,d1,d2,d3,d4))


class TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trajectory = simulate()
        cls.k = cls.trajectory['k']

    def test_analytical_equilibrium_and_force_balance(self):
        k = self.k
        ratio = k['M']*k['R']*math.sin(k['alpha'])/(k['m']*k['l'])
        self.assertLess(ratio, 1)
        vt = k['M']*k['g']*k['R']**2*math.sin(k['alpha'])/k['c']
        qt = k['alpha']-math.asin(ratio)
        equilibrium = derivative((0, vt, qt, 0), k)
        self.assertLess(abs(equilibrium[1]), 1e-12)
        self.assertLess(abs(equilibrium[3]), 1e-12)
        end = self.trajectory['data'][-1]
        self.assertLess(abs(end['v']-vt), 1e-10)
        self.assertLess(abs(end['a']), 1e-9)
        self.assertGreater(abs(end['a']), 0)  # No exact-zero threshold in the solver.
        self.assertGreater(end['power'], 0)  # Steady speed still dissipates energy.
        self.assertAlmostEqual(end['power'], k['M']*k['g']*end['v']*math.sin(k['alpha']), places=9)

    def test_acceleration_matches_independent_velocity_differences(self):
        for time in (0, 2, 4, 6, 8, 10, 12):
            z = min(self.trajectory['data'], key=lambda z: abs(z['t']-time))
            state = (z['x'], z['v'], z['q'], z['w'])
            delta = 1e-5
            # Use local RK4 steps on either side, not rounded chart samples.
            forward = rk4(state, delta, self.k)
            backward = rk4(state, -delta, self.k)
            finite_difference = (forward[1]-backward[1])/(2*delta)
            self.assertLess(abs(finite_difference-z['a']), 1e-11+abs(z['a'])*1e-5)
        near_six = min(self.trajectory['data'], key=lambda z: abs(z['t']-6))
        self.assertGreater(abs(near_six['a']), 1e-6)  # Visually flat is not exact zero.

    def test_half_step_convergence(self):
        duration = self.trajectory['parameters']['duration']
        steps = self.trajectory['steps']*2
        h = duration/steps
        state = (0., 0., 0., 0.)
        for _ in range(steps):
            state = rk4(state, h, self.k)
        coarse = self.trajectory['data'][-1]
        self.assertLess(abs(state[1]-coarse['v']), 1e-10)
        fine_acceleration = derivative(state, self.k)[1]
        self.assertLess(abs(fine_acceleration-coarse['a']), 1e-11)
