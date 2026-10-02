import json,tempfile,unittest
from pathlib import Path
import numpy as np
from deepc.src.r3_roll_runtime import R3RollDeePCRuntime,DEFAULT_CONFIG

class TestR3RollRuntime(unittest.TestCase):
 def test_zero_history_zero_command(self):
  runtime=R3RollDeePCRuntime();result=runtime.update(0.);self.assertFalse(result['fallback_required']);self.assertAlmostEqual(result['command'],0.,places=15)
 def test_finite_sequence_is_deterministic_and_bounded(self):
  sequence=np.sin(np.arange(100)*.2)*.01;a=R3RollDeePCRuntime();b=R3RollDeePCRuntime()
  for value in sequence:
   x=a.update(value);y=b.update(value);self.assertEqual(x,y);self.assertFalse(x['fallback_required']);self.assertLessEqual(abs(x['command']),.0002+1e-15)
 def test_nonfinite_latches_permanently(self):
  runtime=R3RollDeePCRuntime();first=runtime.update(float('nan'));second=runtime.update(0.);self.assertTrue(first['fallback_required']);self.assertTrue(second['fallback_required']);self.assertEqual(first['reason'],second['reason'])
 def test_nonconvergence_requests_fallback(self):
  config=json.loads(DEFAULT_CONFIG.read_text());config['solver_max_iterations']=0
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'config.json';path.write_text(json.dumps(config));result=R3RollDeePCRuntime(path).update(.01)
  self.assertTrue(result['fallback_required']);self.assertIn('converge',result['reason'])
 def test_optimizer_constants_are_precomputed(self):
  runtime=R3RollDeePCRuntime();hessian_id=id(runtime._hessian);step=runtime._step
  for value in np.sin(np.arange(20)*.2)*.01:runtime.update(value)
  self.assertEqual(id(runtime._hessian),hessian_id);self.assertEqual(runtime._step,step)

if __name__=='__main__':unittest.main()
