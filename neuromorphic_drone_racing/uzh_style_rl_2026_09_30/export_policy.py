"""Export a trained policy.pt to a NumPy .npz for the MuJoCo evaluator (PyTorch process)."""
import sys
from pathlib import Path

import numpy as np
import torch

run = Path(sys.argv[1])
ck = torch.load(run / "policy.pt", weights_only=False)
sd = ck["model"]
np.savez(run / "policy_numpy.npz", arm=ck["arm"], seed=ck["seed"],
         norm_mean=ck["norm_mean"].numpy(), norm_var=ck["norm_var"].numpy(),
         enc=ck["enc"].numpy(), off=ck["off"].numpy(),
         **{k.replace(".", "_"): v.numpy() for k, v in sd.items() if k.startswith("pi.") or k == "log_std"})
print("exported", run / "policy_numpy.npz")
