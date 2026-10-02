# Portable Julia HyperLIF architectures

This dependency-light Julia 1.12 package reproduces the forward mathematics of
the PyTorch HyperLIF architecture harness without requiring CUDA or Flux. It
implements the useful non-convolutional families used across audio and control:

- dense/feedforward;
- recurrent SNN (RSNN), with previous hard events fed through `W_rec`;
- temporal-delay SNN, in both PyTorch-parity centered mode and online causal mode;
- all six state readouts: spike count, membrane, gate, `[gate, conductance]`,
  `[voltage, gate]`, and `[voltage, gate, conductance]`.

Event semantics are explicit. `event_mode=:occupancy` is the default because
it reproduces the published snnTorch/APEX-v2 architecture harness: it counts
sampled time bins for which voltage is above threshold. Use
`event_mode=:upcrossing` to count discrete upward threshold crossings, as in
the standalone/Nengo reference. These quantities must not be compared as if
they were the same physical spike count.

Run the tests:

```powershell
julia --project=. -e 'using Pkg; Pkg.test()'
```

The older `../apex_v2` implementation remains the CUDA performance path and has
shared-weight PyTorch parity evidence. This package is the portable reference
path for debugging, teaching, and control-system integration.

## Scope boundary

This package validates forward dynamics and architecture semantics. It does not
yet claim end-to-end gradient or optimizer parity. The published PyTorch delay
model uses symmetric `Conv1d` padding and therefore reads future samples. That is
valid for offline classification but not for real-time control; select
`delay_mode=:causal` online and treat it as a distinct architecture.
