"""Generate gui_cmg_pes_mujoco_subsystems.py from the validated GUI file.

Only the neural-branch block is restructured: the flat list of nodes becomes
four labeled nested nengo.Network groups so each subsystem is separately
expandable/collapsible in Nengo GUI. Nested networks are an organizational
construct only -- objects, connections, transforms, synapses and the PES
rule are byte-identical, so the simulation is unchanged. Verified by
comparing built-model object counts against the original.
"""
from __future__ import annotations

import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "gui_cmg_pes_mujoco.py"
DST = HERE / "gui_cmg_pes_mujoco_subsystems.py"

OLD = '''    with nengo.Network(label="PD + paired CMG + online PES twin") as neural_branch:
        neural_plant = nengo.Node(
            neural_plant_object,
            size_in=3,
            size_out=14,
            label=f"MuJoCo {PLATFORM} neural",
        )
        neural_error = nengo.Node(
            _quaternion_error, size_in=8, size_out=4, label="neural shortest-path q error"
        )
        neural_pd = nengo.Node(_pd, size_in=6, size_out=3, label="same quaternion PD torque")
        pes_target = nengo.Node(_target, size_in=6, size_out=3, label="signed PES target")
        paired_currents = nengo.Node(
            _currents, size_in=3, size_out=6, label="paired currents [+x,+y,+z,-x,-y,-z]"
        )
        nengo.Connection(reference[:4], neural_error[:4], synapse=None)
        nengo.Connection(neural_plant[:4], neural_error[4:8], synapse=None)
        nengo.Connection(neural_error[:3], neural_pd[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], neural_pd[3:6], synapse=None)
        nengo.Connection(neural_error[:3], pes_target[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], pes_target[3:6], synapse=None)
        nengo.Connection(neural_pd, paired_currents, synapse=None)

        cmg_population = nengo.Ensemble(
            N_UNITS,
            1,
            neuron_type=CoupledMembraneGate(adaptive=True),
            gain=np.ones(N_UNITS),
            bias=np.zeros(N_UNITS),
            encoders=np.ones((N_UNITS, 1)),
            label="six coupled membrane-gate units",
        )
        nengo.Connection(paired_currents, cmg_population.neurons, synapse=None)

        decoded_residual = nengo.Node(
            size_in=3, label="learned normalized residual y = W a"
        )
        decoded_clipped = nengo.Node(
            lambda t, x: np.clip(x, -1.0, 1.0),
            size_in=3,
            size_out=3,
            label="clipped decoder used by PES and residual",
        )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="This learning rate is very high.*")
            adaptive_decoder = nengo.Connection(
                cmg_population.neurons,
                decoded_residual,
                transform=W0,
                synapse=None,
                learning_rule_type=nengo.PES(
                    learning_rate=NENGO_LEARNING_RATE, pre_synapse=None
                ),
            )
        nengo.Connection(decoded_residual, decoded_clipped, synapse=None)
        learning_enable = nengo.Node([1.0], label="PES learning enable [0,1]")
        pes_error = nengo.Node(
            _pes_error, size_in=7, size_out=3, label="PES error = enable(y-y*)"
        )
        nengo.Connection(decoded_clipped, pes_error[:3], synapse=None)
        nengo.Connection(pes_target, pes_error[3:6], synapse=None)
        nengo.Connection(learning_enable, pes_error[6], synapse=None)
        nengo.Connection(pes_error, adaptive_decoder.learning_rule, synapse=None)

        beta_control = nengo.Node([0.5], label="residual authority beta [0,0.75]")
        augmented_torque = nengo.Node(
            _residual_command,
            size_in=7,
            size_out=6,
            label="bounded tau=tau0+delta_tau [tau, residual]",
        )
        nengo.Connection(neural_pd, augmented_torque[:3], synapse=None)
        nengo.Connection(decoded_clipped, augmented_torque[3:6], synapse=None)
        nengo.Connection(beta_control, augmented_torque[6], synapse=None)
        nengo.Connection(augmented_torque[:3], neural_plant, synapse=nengo.Lowpass(1e-6))
'''

NEW = '''    with nengo.Network(label="PD + paired CMG + online PES twin") as neural_branch:

        # -- Subsystem 1: plant and the (unmodified) baseline PD law --------
        with nengo.Network(label="S1 plant + quaternion PD") as sub_plant_pd:
            neural_plant = nengo.Node(
                neural_plant_object,
                size_in=3,
                size_out=14,
                label=f"MuJoCo {PLATFORM} neural",
            )
            neural_error = nengo.Node(
                _quaternion_error, size_in=8, size_out=4, label="neural shortest-path q error"
            )
            neural_pd = nengo.Node(_pd, size_in=6, size_out=3, label="same quaternion PD torque")

        # -- Subsystem 2: the CMG neuron population -------------------------
        # cmg_population is the only nengo.Ensemble in the model: a real
        # neural population whose neuron_type is the custom CMG unit.
        with nengo.Network(label="S2 CMG neuron population") as sub_cmg:
            paired_currents = nengo.Node(
                _currents, size_in=3, size_out=6, label="paired currents [+x,+y,+z,-x,-y,-z]"
            )
            cmg_population = nengo.Ensemble(
                N_UNITS,
                1,
                neuron_type=CoupledMembraneGate(adaptive=True),
                gain=np.ones(N_UNITS),
                bias=np.zeros(N_UNITS),
                encoders=np.ones((N_UNITS, 1)),
                label="six coupled membrane-gate units",
            )
            nengo.Connection(paired_currents, cmg_population.neurons, synapse=None)

        # -- Subsystem 3: decoder and the online PES rule -------------------
        with nengo.Network(label="S3 decoder + online PES") as sub_pes:
            pes_target = nengo.Node(_target, size_in=6, size_out=3, label="signed PES target")
            decoded_residual = nengo.Node(
                size_in=3, label="learned normalized residual y = W a"
            )
            decoded_clipped = nengo.Node(
                lambda t, x: np.clip(x, -1.0, 1.0),
                size_in=3,
                size_out=3,
                label="clipped decoder used by PES and residual",
            )
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="This learning rate is very high.*")
                adaptive_decoder = nengo.Connection(
                    cmg_population.neurons,
                    decoded_residual,
                    transform=W0,
                    synapse=None,
                    learning_rule_type=nengo.PES(
                        learning_rate=NENGO_LEARNING_RATE, pre_synapse=None
                    ),
                )
            nengo.Connection(decoded_residual, decoded_clipped, synapse=None)
            learning_enable = nengo.Node([1.0], label="PES learning enable [0,1]")
            pes_error = nengo.Node(
                _pes_error, size_in=7, size_out=3, label="PES error = enable(y-y*)"
            )
            nengo.Connection(decoded_clipped, pes_error[:3], synapse=None)
            nengo.Connection(pes_target, pes_error[3:6], synapse=None)
            nengo.Connection(learning_enable, pes_error[6], synapse=None)
            nengo.Connection(pes_error, adaptive_decoder.learning_rule, synapse=None)

        # -- Subsystem 4: bounded additive residual injection ---------------
        with nengo.Network(label="S4 bounded residual injection") as sub_residual:
            beta_control = nengo.Node([0.5], label="residual authority beta [0,0.75]")
            augmented_torque = nengo.Node(
                _residual_command,
                size_in=7,
                size_out=6,
                label="bounded tau=tau0+delta_tau [tau, residual]",
            )

        # -- Inter-subsystem wiring (kept at branch level so the arrows
        #    between subsystems stay visible when groups are collapsed) ----
        nengo.Connection(reference[:4], neural_error[:4], synapse=None)
        nengo.Connection(neural_plant[:4], neural_error[4:8], synapse=None)
        nengo.Connection(neural_error[:3], neural_pd[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], neural_pd[3:6], synapse=None)
        nengo.Connection(neural_error[:3], pes_target[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], pes_target[3:6], synapse=None)
        nengo.Connection(neural_pd, paired_currents, synapse=None)
        nengo.Connection(neural_pd, augmented_torque[:3], synapse=None)
        nengo.Connection(decoded_clipped, augmented_torque[3:6], synapse=None)
        nengo.Connection(beta_control, augmented_torque[6], synapse=None)
        nengo.Connection(augmented_torque[:3], neural_plant, synapse=nengo.Lowpass(1e-6))
'''

if __name__ == "__main__":
    src = io.open(SRC, encoding="utf-8").read()
    if OLD not in src:
        raise SystemExit("source block not found -- gui_cmg_pes_mujoco.py changed; "
                          "re-sync OLD before regenerating.")
    dst = src.replace(OLD, NEW, 1)
    dst = dst.replace(
        '"""Interactive twin-plant GUI for quaternion PD versus Nengo CMG + PES.',
        '"""Interactive twin-plant GUI (SUBSYSTEM VIEW) for quaternion PD vs Nengo CMG + PES.\n\n'
        'Generated by make_subsystem_variant.py from gui_cmg_pes_mujoco.py. The neural\n'
        'branch is split into four labeled nested networks (S1 plant+PD, S2 CMG neuron\n'
        'population, S3 decoder+PES, S4 residual injection) so each is separately\n'
        'expandable in Nengo GUI. Nesting is organizational only: identical objects,\n'
        'connections and learning rule, hence identical simulation.',
        1)
    io.open(DST, "w", encoding="utf-8").write(dst)
    print(f"wrote {DST}")
