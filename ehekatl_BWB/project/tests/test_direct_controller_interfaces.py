import unittest
from lqr.LQRController import LQRController
from lqr.discrete_cascade_roll_lqr import DiscreteCascadeRollLQR
from deepc.DeePC import DeePC
from deepc.src.r3_roll_runtime import R3RollDeePCRuntime

class TestDirectControllerInterfaces(unittest.TestCase):
    def test_lqr_facade_matches_runtime(self):
        facade=LQRController();reference=DiscreteCascadeRollLQR();facade.SetPoint=.01
        for p,total,yoke in ((.02,.001,.002),(.03,.002,.001),(-.01,0.,0.)):
            self.assertEqual(facade.update(p,total,yoke),reference.update(p-.01,total,yoke)['command'])
    def test_deepc_facade_matches_runtime(self):
        facade=DeePC();reference=R3RollDeePCRuntime();facade.SetPoint=.01
        for p in (.02,.03,-.01,0.):self.assertEqual(facade.update(p),reference.update(p-.01)['command'])
    def test_common_shape(self):
        for controller in (LQRController(),DeePC()):
            self.assertTrue(hasattr(controller,'SetPoint'));self.assertTrue(hasattr(controller,'output'));self.assertTrue(callable(controller.clear));self.assertTrue(callable(controller.update))
