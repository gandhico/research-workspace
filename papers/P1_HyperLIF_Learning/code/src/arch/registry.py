"""Model registry: build any (architecture x neuron x readout) — the swappable layer the three-tier
plan needs. `ff` reuses project 07's parity-validated SNNTorchNet; `conv`/`rsnn` are the new Tier-2
topologies. Same signature as train_hpc expects: model(X) -> (logits, aux)."""
from __future__ import annotations

from .common import KNOWN_SENSOR  # noqa: F401  (also triggers the 07 path bootstrap)
from .conv_snn import ConvSNNNet
from .conv_resnet import ConvResSNN
from .delay_snn import DelaySNNNet
from .recurrent_snn import RSNNNet

from adhyperlif_triage.models.snntorch_net import SNNTorchNet  # 07, via common's bootstrap

ARCHITECTURES = ["ff", "rsnn", "conv", "delay", "convres"]
CONV_FAMILY = ("conv", "convres")   # vision-only (need a 2-D sensor)

# Dense conv-residual defaults = ResNet-18-class (~14M params) for the at-scale / SOTA runs (report
# these in the paper). Denser tiers for full-data caches: (128,(2,2,2,2))≈57M, (128,(3,4,6,3))≈97M.
CONVRES_BASE_CH = 128
CONVRES_STAGE_BLOCKS = (2, 2, 2)


def infer_sensor(meta):
    if meta.get("sensor"):
        return tuple(meta["sensor"])
    return KNOWN_SENSOR.get(meta["n_in"])


def build_model(arch, meta, neuron="hyperlif", readout="hybrid_vr_conductance", hidden=256, dt=1e-3, cfg=None):
    """cfg = HyperLIF variant params (event_threshold, v_reset, delta_reset, min_voltage); applies to
    conv/rsnn. (ff reuses 07's SNNTorchNet which uses base params — variant support there is a small
    07 extension for Phase B.)"""
    n_in, n_classes = meta["n_in"], meta["n_classes"]
    if arch == "ff":
        return SNNTorchNet(n_in, hidden, n_classes, neuron=neuron, readout=readout, dt=dt)
    if arch == "rsnn":
        return RSNNNet(n_in, n_classes, neuron=neuron, readout=readout, n_hidden=hidden, dt=dt, cfg=cfg)
    if arch == "conv":
        sensor = infer_sensor(meta)
        if sensor is None:
            raise ValueError(f"conv needs a vision sensor; F={n_in} not in KNOWN_SENSOR (audio? use rsnn/ff)")
        return ConvSNNNet(sensor, n_classes, neuron=neuron, readout=readout,
                          n_hidden=min(hidden, 128), dt=dt, cfg=cfg)
    if arch == "delay":
        return DelaySNNNet(n_in, n_classes, neuron=neuron, readout=readout, n_hidden=hidden, dt=dt, cfg=cfg)
    if arch == "convres":
        sensor = infer_sensor(meta)
        if sensor is None:
            raise ValueError(f"convres needs a vision sensor; F={n_in} not in KNOWN_SENSOR")
        return ConvResSNN(sensor, n_classes, neuron=neuron, readout=readout, n_hidden=hidden, dt=dt,
                          cfg=cfg, base_ch=CONVRES_BASE_CH, stage_blocks=CONVRES_STAGE_BLOCKS)
    raise ValueError(f"unknown architecture: {arch} (choose from {ARCHITECTURES})")
