"""Generate architectures.drawio (multi-page) from a compact node/edge spec.

Open the output at https://app.diagrams.net or in the VS Code / desktop
draw.io editor. Each architecture is one page, matching the TikZ sources
archA1..archG1 one-for-one so the two stay in sync.

Run:  python make_drawio.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "architectures.drawio"

# --- shared styles ---------------------------------------------------------
F = "fontFamily=Helvetica;fontSize=12;whiteSpace=wrap;html=1;rounded=1;"
PLAIN = F + "fillColor=#FFFFFF;strokeColor=#333333;"
CLAS = F + "fillColor=#F2F2F2;strokeColor=#333333;"
NEURO = F + "fillColor=#DDDDDD;strokeColor=#000000;strokeWidth=2;"
PLANT = F + "fillColor=#C9C9C9;strokeColor=#333333;"
MEAS = F + "fillColor=#FFFFFF;strokeColor=#777777;dashed=1;"
GROUP = (F + "fillColor=none;strokeColor=#999999;dashed=1;verticalAlign=top;"
         "fontSize=11;fontStyle=2;align=left;spacingLeft=6;spacingTop=2;")
NOTE = ("text;html=1;align=left;verticalAlign=top;fontFamily=Helvetica;"
        "fontSize=11;fontStyle=2;")
E = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;"
     "endFill=1;strokeColor=#000000;fontFamily=Helvetica;fontSize=11;"
     "labelBackgroundColor=#FFFFFF;")
ED = E + "dashed=1;"

STYLES = {"p": PLAIN, "c": CLAS, "n": NEURO, "P": PLANT, "m": MEAS,
          "g": GROUP, "t": NOTE}


TAG = "&lt;%s&gt;%s&lt;/%s&gt;"


def xml_escape(text: str) -> str:
    """Escape the five characters that may not appear literally in an XML
    attribute value."""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;")
                .replace("'", "&apos;"))


_SUB = re.compile(r"_\{([^}]*)\}")
_SUP = re.compile(r"\^\{([^}]*)\}")


def fmt(label: str) -> str:
    """Mini-markup -> a drawio label attribute value.

    ``x_{k}`` and ``x^{2}`` become <sub>/<sup>, newlines become <br>, and
    the whole thing is XML-escaped the way draw.io stores HTML labels
    (drawio un-escapes and renders it because every style sets html=1).
    Plain underscores in code identifiers such as ``neuron_type`` are left
    alone because only the braced form is treated as markup.
    """
    out = xml_escape(label)
    out = _SUB.sub(lambda m: TAG % ("sub", m.group(1), "sub"), out)
    out = _SUP.sub(lambda m: TAG % ("sup", m.group(1), "sup"), out)
    return out.replace(chr(10), "&lt;br&gt;")


class Page:
    """One drawio page. Coordinates are absolute pixels, origin top-left."""

    def __init__(self, pid: str, name: str):
        self.pid, self.name, self.cells, self._n = pid, name, [], 0

    def box(self, key, kind, x, y, w, h, label):
        self.cells.append(
            f'<mxCell id="{self.pid}_{key}" value="{fmt(label)}" '
            f'style="{STYLES[kind]}" vertex="1" parent="{self.pid}_1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
            f'as="geometry"/></mxCell>')

    def edge(self, src, dst, label="", dashed=False, exit=None, entry=None,
             waypoints=()):
        self._n += 1
        st = ED if dashed else E
        if exit:
            st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        pts = ""
        if waypoints:
            inner = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in waypoints)
            pts = f'<Array as="points">{inner}</Array>'
        self.cells.append(
            f'<mxCell id="{self.pid}_e{self._n}" value="{fmt(label)}" '
            f'style="{st}" edge="1" parent="{self.pid}_1" '
            f'source="{self.pid}_{src}" target="{self.pid}_{dst}">'
            f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry>'
            f'</mxCell>')

    def xml(self):
        body = "".join(self.cells)
        return (f'<diagram id="{self.pid}" name="{xml_escape(self.name)}">'
                f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" '
                f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
                f'page="1" pageScale="1" pageWidth="1600" pageHeight="900" '
                f'math="0" shadow="0"><root>'
                f'<mxCell id="{self.pid}_0"/>'
                f'<mxCell id="{self.pid}_1" parent="{self.pid}_0"/>'
                f'{body}</root></mxGraphModel></diagram>')


pages: list[Page] = []


# ===========================================================================
# A1 -- main loop, compact
# ===========================================================================
p = Page("A1", "A1 main loop (compact)")
p.box("grp", "g", 240, 250, 700, 230,
      "neuromorphic residual path (only W adapts)")
p.box("ref", "p", 40, 60, 110, 50, "reference\nq_{d}(t)")
p.box("err", "c", 200, 60, 140, 50, "quaternion error\n(eq. 6)")
p.box("pd", "c", 390, 60, 140, 50, "quaternion PD\n(eq. 11)")
p.box("res", "c", 590, 60, 170, 50, "bounded additive\nresidual  (eq. 22)")
p.box("plt", "P", 820, 60, 150, 50, "mixer B⁻¹\n+ plant")
p.box("enc", "n", 280, 290, 140, 60, "paired encoding\n(eq. 15)")
p.box("cmg", "n", 480, 290, 150, 60, "2m CMG units\n(eq. 16)")
p.box("dec", "n", 700, 290, 150, 60, "decoder Wₖ\n(eq. 19)")
p.box("pes", "n", 480, 400, 150, 60, "PES update\n(eq. 21)")
p.edge("ref", "err")
p.edge("err", "pd", "e_{q}")
p.edge("pd", "res", "u₀")
p.edge("res", "plt", "uₖ")
p.edge("pd", "enc", "u₀", exit=(0.5, 1), entry=(0.5, 0))
p.edge("enc", "cmg", "I±")
p.edge("cmg", "dec", "aₖ")
p.edge("dec", "res", "βℓ⊙sₖ", exit=(0.5, 0), entry=(0.5, 1),
       waypoints=[(775, 220), (675, 220)])
p.edge("cmg", "pes", exit=(0.5, 1), entry=(0.5, 0))
p.edge("pes", "dec", "ΔW", exit=(1, 0.5), entry=(0.5, 1),
       waypoints=[(775, 430)])
p.edge("plt", "err", "q, ω", exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(895, 540), (270, 540)])
p.edge("plt", "pes", "εₖ", dashed=True, exit=(0.5, 1),
       entry=(0.5, 1), waypoints=[(895, 540), (555, 540)])
p.box("note", "t", 40, 570, 900, 60,
      "u = sat_{ℓ}(u₀ + βℓ⊙s):  the residual is ADDED to a "
      "saturated baseline, never blended with it, so β=0 recovers the "
      "baseline exactly.")
pages.append(p)


# ===========================================================================
# A2 -- main loop, detailed
# ===========================================================================
p = Page("A2", "A2 main loop (detailed)")
p.box("grp", "g", 250, 260, 940, 260, "CMG-PES residual path")
p.box("ref", "p", 30, 70, 110, 60, "mission\nreference q_{d}(t)")
p.box("err", "c", 190, 70, 190, 60,
      "shortest-path error\nq_{e} = q_{d} ⊗ q⁻¹\ne_{q} = sgn₊(q_{e,0}) vec(q_{e})")
p.box("pd", "c", 430, 70, 210, 60,
      "quaternion PD\nτ₀ = sat(−K_{q} e_{q} − K_{ω} ω)")
p.box("res", "c", 700, 70, 220, 60,
      "bounded additive residual\nuₖ = sat_{ℓ}(u₀ₖ + βℓ⊙sₖ)")
p.box("alc", "c", 970, 70, 150, 60, "allocation\nf = B⁻¹[T, τᵀ]ᵀ")
p.box("plt", "P", 1170, 70, 150, 60, "MuJoCo rigid body\nX2 / CF2")
p.box("enc", "n", 280, 300, 200, 80,
      "paired encoding\nū = u₀ ⊘ ℓ\nI± = I_{b} + I_{g} max(±ū, 0)")
p.box("cmg", "n", 540, 300, 210, 80,
      "2m CMG units\ngate r_{j}, membrane v_{j}\nc_{j} = (g₀ + χ g₁|I_{j}|) r_{j}²\n"
      "aₖ = clip(G rₖ)")
p.box("dec", "n", 820, 300, 200, 80,
      "linear decoder\nsₖ = clip(Wₖ aₖ)\nW₀ = [I_{m}, −I_{m}]")
p.box("pes", "n", 540, 430, 300, 70,
      "projected PES\nWₖ₊₁ = Π[Wₖ + η εₖ aₖᵀ − λ_{W} Wₖ]")
p.box("tgt", "m", 280, 430, 220, 70,
      "PES target\ny*ₖ = clip(−k_{e} e_{q} − k*_{ω} ω)")
p.edge("ref", "err")
p.edge("err", "pd", "e_{q}")
p.edge("pd", "res", "u₀ = τ₀")
p.edge("res", "alc", "uₖ")
p.edge("alc", "plt", "f")
p.edge("pd", "enc", "u₀", exit=(0.5, 1), entry=(0.5, 0))
p.edge("enc", "cmg", "I")
p.edge("cmg", "dec", "aₖ")
p.edge("dec", "res", "βℓ⊙sₖ", exit=(0.5, 0), entry=(0.5, 1),
       waypoints=[(920, 230), (810, 230)])
p.edge("cmg", "pes", "aₖ", exit=(0.5, 1), entry=(0.5, 0))
p.edge("tgt", "pes", "y*ₖ")
p.edge("dec", "pes", "sₖ", exit=(0.25, 1), entry=(1, 0.25),
       waypoints=[(870, 400), (880, 400)])
p.edge("pes", "dec", "Wₖ₊₁", exit=(1, 0.5), entry=(1, 0.75),
       waypoints=[(1070, 465), (1070, 360)])
p.edge("plt", "err", "q, ω", exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(1245, 570), (285, 570)])
p.edge("plt", "tgt", dashed=True, exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(1245, 570), (390, 570)])
pages.append(p)


# ===========================================================================
# A3 -- layered mechanism view
# ===========================================================================
p = Page("A3", "A3 three separable mechanisms")
p.box("b0", "g", 40, 40, 900, 110, "L0  fixed classical control")
p.box("b1", "g", 40, 230, 900, 110, "L1  neural substrate")
p.box("b2", "g", 40, 420, 900, 110, "L2  online learning")
p.box("l0a", "c", 70, 80, 150, 50, "reference q_{d}")
p.box("l0b", "c", 270, 80, 180, 50, "shortest-path error")
p.box("l0c", "c", 500, 80, 160, 50, "quaternion PD")
p.box("l0d", "c", 720, 80, 180, 50, "allocation B⁻¹ + plant")
p.box("l1a", "n", 70, 270, 150, 50, "paired encoding")
p.box("l1b", "n", 270, 270, 180, 50, "membrane v_{j}")
p.box("l1c", "n", 500, 270, 160, 50, "gate r_{j}")
p.box("l1d", "n", 720, 270, 180, 50, "activities aₖ")
p.box("l2a", "n", 70, 460, 150, 50, "PES error εₖ")
p.box("l2b", "n", 270, 460, 180, 50, "gradient η εₖ aₖᵀ")
p.box("l2c", "n", 500, 460, 160, 50, "decay λ_{W} Wₖ")
p.box("l2d", "n", 720, 460, 180, 50, "projection Π")
for a, b in [("l0a", "l0b"), ("l0b", "l0c"), ("l0c", "l0d"),
             ("l1a", "l1b"), ("l1b", "l1c"), ("l1c", "l1d"),
             ("l2a", "l2b"), ("l2b", "l2c"), ("l2c", "l2d")]:
    p.edge(a, b)
p.edge("l1c", "l1b", "γ, c_{j}", dashed=True, exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(580, 360), (360, 360)])
p.edge("l0a", "l1a", "u₀", exit=(0.5, 1), entry=(0.5, 0))
p.edge("l1a", "l2a", "aₖ", exit=(0.5, 1), entry=(0.5, 0))
p.edge("l2d", "l1d", "Wₖ₊₁", exit=(0.5, 0), entry=(0.5, 1))
p.edge("l1d", "l0d", "βℓ⊙sₖ", exit=(0.5, 0), entry=(0.5, 1))
p.box("k0", "t", 960, 80, 260, 60,
      "L0 fixed. Gains never adapt; the residual is added, not blended.")
p.box("k1", "t", 960, 270, 260, 60,
      "L1 substrate. Ablation knob χ ∈ {0,1} (conductance modulation).")
p.box("k2", "t", 960, 460, 260, 60,
      "L2 learning. Ablation knobs η, λ_{W} (online decoder adaptation).")
p.box("note", "t", 40, 560, 1000, 60,
      "Interface knob β ∈ [0,1] scales L1→L0 authority. β=0 recovers the "
      "baseline exactly; η=0 freezes W = W₀; χ=0 removes input-dependent "
      "conductance. The three can be ablated independently.")
pages.append(p)


# ===========================================================================
# B1 -- CMG unit internals
# ===========================================================================
p = Page("B1", "B1 CMG unit internals")
p.box("I", "p", 220, 60, 90, 45, "I_{j}")
p.box("v", "n", 400, 45, 330, 80,
      "membrane  v_{j}\ndv/dt = −(v − v_{rest})/τ + I_{j}/τ − c_{j} (v − v_{reset})\n"
      "exact exponential step (eq. 18)")
p.box("r", "n", 400, 250, 330, 80,
      "gate  r_{j}\ndr/dt = [σ(α_{h} (v − v_{th} + γ r)) − r] / τ_{r}\n"
      "clipped Euler step (eq. 17)")
p.box("c", "c", 80, 260, 250, 60,
      "conductance\nc_{j} = (g₀ + χ g₁ |I_{j}|) r_{j}²")
p.box("a", "p", 810, 250, 190, 60, "activity\na_{j} = clip(G r_{j})")
p.edge("I", "v")
p.edge("v", "r", "v_{j} sets the gate target", exit=(0.5, 1), entry=(0.5, 0))
p.edge("r", "c", "r_{j}²")
p.edge("c", "v", "c_{j} shunts", exit=(0.5, 0), entry=(0.1, 1))
p.edge("r", "a", "r_{j}")
p.edge("I", "c", "χ g₁ |I_{j}|", exit=(0, 0.5), entry=(0.5, 0),
       waypoints=[(40, 82), (40, 220), (205, 220)])
p.edge("r", "r", "γ r_{j} shifts its own threshold", dashed=True,
       exit=(0.75, 1), entry=(0.25, 1),
       waypoints=[(650, 390), (480, 390)])
p.box("note", "t", 60, 420, 950, 60,
      "Two coupling paths make the unit coupled rather than a cascade: the "
      "gate shifts its own activation threshold (γ) and shunts the membrane "
      "through c_{j} ∝ r_{j}². Continuous dynamics — no spike, no reset event "
      "— and only a_{j} leaves the unit. χ = 0 gives the ablated variant.")
pages.append(p)


# ===========================================================================
# B2 -- antagonistic pair
# ===========================================================================
p = Page("B2", "B2 antagonistic +/- pair")
p.box("u", "p", 40, 180, 190, 60,
      "channel i\nū_{i} = u_{0,i} / ℓ_{i} ∈ [−1, 1]")
p.box("ip", "c", 300, 60, 220, 50, "Iᵢ⁺ = I_{b} + I_{g} max(ū_{i}, 0)")
p.box("im", "c", 300, 320, 220, 50, "Iᵢ⁻ = I_{b} + I_{g} max(−ū_{i}, 0)")
p.box("cp", "n", 580, 55, 160, 60, "CMG unit i⁺\n(v, r)")
p.box("cm", "n", 580, 315, 160, 60, "CMG unit i⁻\n(v, r)")
p.box("ap", "p", 800, 60, 130, 50, "aᵢ⁺ ∈ [0,1]")
p.box("am", "p", 800, 320, 130, 50, "aᵢ⁻ ∈ [0,1]")
p.box("w", "n", 1000, 175, 230, 80,
      "decoder row i of Wₖ\ns_{i} = clip(W_{k,i} · aₖ)\nat k=0:  s_{i} = aᵢ⁺ − aᵢ⁻")
p.box("out", "p", 1300, 185, 160, 55, "signed residual s_{i}")
p.edge("u", "ip")
p.edge("u", "im")
p.edge("ip", "cp")
p.edge("im", "cm")
p.edge("cp", "ap")
p.edge("cm", "am")
p.edge("ap", "w", "+1")
p.edge("am", "w", "−1")
p.edge("w", "out")
p.box("note", "t", 40, 430, 1100, 60,
      "Each of the m command channels drives an antagonistic pair, so the "
      "population has 2m units. Activities are non-negative by construction; "
      "the sign is carried by the decoder. Initialising W₀ = [I_{m}, −I_{m}] "
      "makes the untrained residual exactly the pair difference, so learning "
      "starts from a meaningful readout rather than a random one.")
pages.append(p)


# ===========================================================================
# C1 -- twin-plant harness
# ===========================================================================
p = Page("C1", "C1 matched twin-plant harness")
p.box("ref", "p", 40, 200, 170, 60, "shared mission\ngenerator q_{d}(t)")
p.box("pd1", "c", 300, 60, 160, 60, "quaternion PD\nK_{q}, K_{ω}")
p.box("pl1", "P", 530, 60, 160, 60, "MuJoCo twin A")
p.box("m1", "m", 760, 60, 190, 60,
      "θ̄_{q}(PD),  τ̄,  f_{sat}")
p.box("pd2", "c", 300, 340, 160, 60, "identical PD\nsame K_{q}, K_{ω}")
p.box("rsd", "n", 530, 340, 180, 60, "CMG + PES residual\nβ, η, χ")
p.box("pl2", "P", 780, 340, 160, 60, "MuJoCo twin B")
p.box("m2", "m", 1010, 340, 190, 60,
      "θ̄_{q}(CMG),  τ̄,  f_{sat}")
p.box("cmp", "p", 1010, 60, 230, 70,
      "matched comparison\nΔ = 1 − θ̄_{q}(CMG)/θ̄_{q}(PD)")
p.edge("ref", "pd1")
p.edge("ref", "pd2")
p.edge("pd1", "pl1")
p.edge("pl1", "m1")
p.edge("m1", "cmp")
p.edge("pd2", "rsd")
p.edge("rsd", "pl2")
p.edge("pl2", "m2")
p.edge("m2", "cmp", exit=(1, 0.5), entry=(0.5, 1),
       waypoints=[(1270, 370), (1270, 200), (1125, 200)])
p.edge("pl1", "pd1", dashed=True, exit=(0.5, 0), entry=(0.5, 0),
       waypoints=[(610, 20), (380, 20)])
p.edge("pl2", "pd2", dashed=True, exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(860, 440), (380, 440)])
p.box("note", "t", 40, 480, 1150, 60,
      "Both twins share reference, duration, integration step, actuator "
      "scale, allocator, initial condition, safety limits and logging. The "
      "residual path is the only difference, so the reported improvement is "
      "attributable to it rather than to re-tuning.")
pages.append(p)


# ===========================================================================
# D1 -- Nengo realization
# ===========================================================================
p = Page("D1", "D1 Nengo realization")
p.box("grp", "g", 40, 60, 1180, 300,
      "built model: 1 Ensemble, 25 Nodes, 35 Connections, 1 PES rule")
p.box("s1", "c", 80, 110, 250, 90,
      "S1  plant + quaternion PD\nnengo.Node × 3\nMuJoCo twin, error, PD law")
p.box("s2", "n", 430, 100, 300, 110,
      "S2  CMG population\nnengo.Ensemble(n_neurons = 2m)\n"
      "neuron_type = CoupledMembraneGate\ngain = 1, bias = 0")
p.box("s3", "c", 840, 105, 300, 100,
      "S3  decoder + PES\nnengo.Connection(... .neurons)\n"
      "learning_rule_type = nengo.PES\ntransform = W₀")
p.box("s4", "c", 460, 270, 300, 70,
      "S4  bounded residual injection\nnengo.Node (β, sat_{ℓ})")
p.edge("s1", "s2", "I  into .neurons")
p.edge("s2", "s3", "aₖ")
p.edge("s3", "s4", "sₖ", exit=(0.5, 1), entry=(1, 0.5),
       waypoints=[(990, 305)])
p.edge("s4", "s1", "uₖ", exit=(0, 0.5), entry=(0.5, 1),
       waypoints=[(205, 305)])
p.box("note", "t", 40, 390, 1150, 80,
      "The CMG population is the model's only Ensemble: in Nengo a custom "
      "NeuronType can exist only inside one. Everything else is a Node, i.e. "
      "non-neural scaffolding. Current is injected at .neurons, bypassing "
      "the NEF encoders (gain = 1, bias = 0), and the PES learning rate is "
      "converted as η_{nengo} = η (2m) / h so the direct and Nengo "
      "realizations coincide.")
pages.append(p)


# ===========================================================================
# E1 -- hardware loop
# ===========================================================================
p = Page("E1", "E1 3DOF Hover hardware loop")
p.box("rig", "P", 60, 60, 210, 80,
      "Quanser 3DOF Hover\n3 encoders, 4 motors\nvia Q8 DAQ")
p.box("enc", "m", 350, 65, 190, 70, "tare, unwrap, filter\n→ q, ω")
p.box("pd", "c", 620, 65, 210, 70,
      "quaternion PD\n200 Hz  (5 ms budget)")
p.box("nn", "n", 620, 250, 210, 80,
      "CMG + PES\n10× substeps at\nh = 0.5 ms  (2 kHz)")
p.box("cap", "c", 370, 255, 170, 70, "residual cap\n+ slew limit")
p.box("alc", "c", 100, 255, 190, 70,
      "torque → F/B/L/R\n0–24 V, gain 3")
p.box("grd", "m", 300, 400, 400, 70,
      "safety layer: encoder-step check · attitude limit\n"
      "· deadline-miss abort · zero-output cleanup")
p.edge("rig", "enc")
p.edge("enc", "pd")
p.edge("pd", "nn", "u₀", exit=(0.5, 1), entry=(0.5, 0))
p.edge("nn", "cap", "sₖ")
p.edge("cap", "alc", "uₖ")
p.edge("alc", "rig", "f", exit=(0.5, 0), entry=(0.5, 1))
p.edge("grd", "cap", dashed=True, exit=(0.5, 0), entry=(0.5, 1))
p.edge("grd", "nn", dashed=True, exit=(1, 0.5), entry=(0.5, 1),
       waypoints=[(725, 435)])
p.box("note", "t", 60, 500, 1000, 60,
      "Hard real time: each 200 Hz hardware step contains ten 0.5 ms neural "
      "substeps, so the neural state advances at the same rate as in "
      "simulation. The controller is driven directly from Nengo; the same "
      "model under the Nengo GUI produces interpreter-lock contention and "
      "deadline-miss aborts.")
pages.append(p)


# ===========================================================================
# F1 -- 6-DOF cascade
# ===========================================================================
p = Page("F1", "F1 6-DOF cascade")
p.box("pref", "p", 40, 60, 150, 55, "p_{d}(t), ψ_{d}")
p.box("perr", "c", 250, 60, 150, 55, "position error")
p.box("pos", "c", 460, 60, 150, 55, "outer PD\nω_{n,pos}")
p.box("dcp", "c", 670, 50, 190, 75,
      "thrust-vector\ndecomposition → (q_{d}, T)")
p.box("aerr", "c", 250, 250, 180, 55, "quaternion error")
p.box("att", "c", 490, 250, 150, 55, "inner PD\nω_{n,att}")
p.box("res", "c", 700, 250, 160, 55, "residual (eq. 22)")
p.box("cmg", "n", 490, 380, 150, 55, "CMG + PES")
p.box("alc", "c", 930, 250, 160, 55, "allocation B⁻¹")
p.box("plt", "P", 930, 380, 160, 55, "6-DOF rigid body")
p.edge("pref", "perr")
p.edge("perr", "pos")
p.edge("pos", "dcp", "F_{cmd}")
p.edge("dcp", "aerr", "q_{d}", exit=(0.5, 1), entry=(0.5, 0),
       waypoints=[(765, 180), (340, 180)])
p.edge("dcp", "alc", "T", exit=(1, 0.5), entry=(0.5, 0),
       waypoints=[(1010, 88)])
p.edge("aerr", "att")
p.edge("att", "res", "τ₀")
p.edge("res", "alc", "τ")
p.edge("att", "cmg", exit=(0.5, 1), entry=(0.5, 0))
p.edge("cmg", "res", "βℓ⊙sₖ", exit=(1, 0.5), entry=(0.5, 1),
       waypoints=[(780, 408)])
p.edge("alc", "plt", "f")
p.edge("plt", "aerr", "q, ω", exit=(0.5, 1), entry=(0.5, 1),
       waypoints=[(1010, 500), (340, 500)])
p.edge("plt", "perr", "p, ṗ", exit=(0.5, 1), entry=(0, 0.5),
       waypoints=[(1010, 530), (200, 530), (200, 88)])
p.box("note", "t", 40, 560, 1050, 60,
      "Time-scale separation is required, not optional: the validated "
      "ceiling is ω_{n,pos} = [1.0, 1.0, 1.2] against ω_{n,att} = [4, 4, 3.5] "
      "rad/s. Both q_{d} and the measured q must be expressed in the same "
      "quaternion convention before the error is formed.")
pages.append(p)


# ===========================================================================
# G1 -- learning-rule comparison
# ===========================================================================
p = Page("G1", "G1 PES vs annealed trace")
p.box("a", "p", 60, 60, 170, 50, "activities aₖ")
p.box("e", "p", 330, 60, 220, 50, "error εₖ = y*ₖ − sₖ")
p.box("s", "p", 700, 60, 200, 50, "mission progress\ns = t/T ∈ [0,1]")
p.box("g1", "g", 60, 200, 380, 130, "R1  instantaneous PES (this paper)")
p.box("r1", "n", 90, 240, 320, 70,
      "ΔWₖ = η εₖ aₖᵀ − λ_{W} Wₖ\nfixed rate, no memory of past activity")
p.box("g2", "g", 560, 200, 420, 220, "R2  annealed trace (precursor only)")
p.box("r2a", "n", 590, 240, 360, 70,
      "zₖ = ρ(s) zₖ₋₁ + (1 − ρ(s)) aₖ\nρ(s) = 0.98 − 0.48 s  (trace shortens)")
p.box("r2b", "n", 590, 335, 360, 70,
      "ΔWₖ = η(s) εₖ zₖᵀ\nη(s) = η₀ (1 − 0.8 s)  (rate decays)")
p.box("W", "p", 380, 490, 300, 55, "decoder update  Wₖ₊₁ = Wₖ + ΔWₖ")
p.edge("a", "r1", exit=(0.5, 1), entry=(0.25, 0))
p.edge("e", "r1", exit=(0.5, 1), entry=(0.75, 0))
p.edge("a", "r2a", "aₖ", exit=(0.5, 0), entry=(0.15, 0),
       waypoints=[(145, 20), (644, 20)])
p.edge("s", "r2a", exit=(0.5, 1), entry=(0.85, 0))
p.edge("s", "r2b", "η(s)", exit=(1, 0.5), entry=(1, 0.5),
       waypoints=[(1010, 85), (1010, 370)])
p.edge("e", "r2b", "εₖ", exit=(0.5, 1), entry=(0, 0.5),
       waypoints=[(440, 370)])
p.edge("r2a", "r2b", "zₖ", exit=(0.5, 1), entry=(0.5, 0))
p.edge("r1", "W", exit=(0.5, 1), entry=(0, 0.5))
p.edge("r2b", "W", exit=(0.5, 1), entry=(1, 0.5))
p.box("note", "t", 60, 570, 1000, 70,
      "Both rules share the same activities, the same error signal and the "
      "same projected decoder; they differ only in what multiplies the error "
      "and how fast it is applied. R2 explores early and consolidates late. "
      "Its outcome is mission dependent — beneficial in some missions, "
      "adverse in others — so it is reported separately rather than folded "
      "into the main results.")
pages.append(p)


# ---------------------------------------------------------------------------
xml = ('<mxfile host="app.diagrams.net" agent="make_drawio.py" version="24.7.17">'
       + "".join(pg.xml() for pg in pages) + "</mxfile>")
io.open(OUT, "w", encoding="utf-8").write(xml)
print(f"wrote {OUT}  ({len(pages)} pages, {len(xml)} bytes)")
for pg in pages:
    print(f"  {pg.pid:4s} {pg.name}")
