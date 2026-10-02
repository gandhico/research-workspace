# Friday presentation outline

1. **Problem and thesis** — preserve a trusted baseline while adding a bounded,
   online-adaptive neuromorphic residual.
2. **Why the old project needed reconstruction** — blending versus residual,
   external wrench versus rotor actuators, and CF2 authority mismatch.
3. **Architecture** — quaternion PD, pair encoding, coupled membrane–gate (CMG) units, learned
   decoder, additive residual, rotor allocation.
4. **X2 headline result** — 53.07% lower mean quaternion error, zero saturation.
5. **What adaptation matters** — online decoder matters; conductance adaptation
   is null under gate saturation.
6. **Stock CF2 feasibility failure** — 99.88% saturation under the virtual
   moment model.
7. **CF2 actuator co-design** — explicit four-rotor model, authority sweep, and
   1.5× design result with 53.65% improvement.
8. **Pendulum evidence** — bounded QLabs virtual-twin transfer with nominal
   performance equivalent to LQR; no physical-hardware claim.
9. **QCar and 3DOF Hover** — safe bridges, MuJoCo integration models, QCar
   spiking shadow perception, and planned hardware protocol.
10. **Neuron-family hypothesis** — archived LIF/Izhikevich pipelines were worse,
    but output representations were unmatched; CMG superiority is not yet claimed.
11. **Work to submission** — robustness, frozen-weight hold-out, matched
    LIF/ALIF/Izhikevich ablation, hardware runs, and September 25 deadline.
