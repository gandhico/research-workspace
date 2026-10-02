# Controller structure

The canonical project root is:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

Each controller has one top-level folder:

```text
backstepping/   preserved recovery-capable dissertation controller
pid/            preserved dissertation PID controller
lqr/            unvalidated LQR retained pending identification
```

Shared project material is under `configs/`, `logs/`, `scripts/`, `docs/`, and
`tests/`. Historical material is under `archive/`. The existing virtual
environment remains at
`backstepping/ehekatl_xplane12_backstepping_bridge/.venv` to preserve its
embedded paths; the directory contains no active controller source.

XPlaneConnect's third-party source is outside the project at
`../shared/third_party/XPlaneConnect-master`. Local `xpc.py` clients remain next
to runners to preserve their tested import and transport behavior.
