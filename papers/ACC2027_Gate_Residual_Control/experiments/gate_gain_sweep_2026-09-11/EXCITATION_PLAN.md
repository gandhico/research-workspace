# Follow-up excitation and simpler-control tests

Adaptive development stage, motivated by the completed gamma=.5, G=1 Full3 pair: changing gamma alone gives very little conductance excitation during nominal tracking and only about 0.8% improvement over PD. The triangular-ramp neuron test did excite a conductance-sensitive regime, but ordinary baseline currents rarely remain in that range.

Test the single input-bias change Ib=.75 -> 1.0, keeping gamma=.5, G in {1,3}, chi in {0,1}, on X2 Full3 and Hardstep (8 cases). This intentionally changes the operating point to the nominal membrane threshold. It is new tuning, not the frozen encoding. All other control and learning parameters remain fixed. Save all outcomes; do not describe a post-selected configuration as independently validated.

Also test a constant six-feature basis a=ones(6) with exactly the same W0, PES update, leak, bounds, authority and plant on X2 Roll/Full3 and CF2 Hardstep (3 cases). This has no neurons or intrinsic states and is equivalent to the reduced target-filter recursion while its projections/clipping are inactive. Artificial gate/voltage archive slots are placeholders only. It directly checks whether saturated CMG activity is necessary, rather than merely comparing different neural families.

Two fresh X2 Hardstep anchors (PD and canonical CMG) provide the missing paired nominal comparison for the development cases. Total extension: 13 runs. Canonical sources are unchanged; sweep_extensions.py is an explicitly separate wrapper. Full-rate currents and CSV current fields use the actual new bias.
