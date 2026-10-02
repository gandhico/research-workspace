# 6-DOF feedforward study — compiled tables

## X2

Selected baseline: `a20_20_17.5_p2_2_2.4` (score 0.0492); runner-up `a16_16_14_p2_2_2.4` (0.0508).
Selected CMG β = 0.05 (score 0.0469); β=0.02: 0.0477, β=0.008: 0.0487, β=0.1: 0.0495

| mission | canonical PD | canonical CMG | tuned PD + pos-ff | CMG on tuned |
|---|---|---|---|---|
| hover3d | 0.0000 m / 0.00° | 0.0770 m / 1.62° | 0.0013 m / 0.12° | 0.0039 m / 0.63° |
| waypoint_step | 0.1680 m / 3.01° | 0.1487 m / 2.61° | 0.0293 m / 0.55° | 0.0314 m / 0.90° |
| circle_xy | 0.8783 m / 13.92° | 0.3061 m / 4.44° | 0.0086 m / 0.33° | 0.0070 m / 0.39° |
| full6_stress | 0.9891 m / 14.65° | 0.2368 m / 5.00° | 0.0113 m / 0.36° | 0.0085 m / 0.44° |

## CF2

Selected baseline: `a24_24_20.4_p2.25_2.25_2.7` (score 0.0387); runner-up `a20_20_17_p2.5_2.5_3` (0.0395).
Selected CMG β = 0.008 (score 0.0374); β=0.002: 0.0382, β=0.02: 0.0385, β=0.05: 0.0465

| mission | canonical PD | canonical CMG | tuned PD + pos-ff | CMG on tuned |
|---|---|---|---|---|
| hover3d | 0.0000 m / 0.00° | 0.0009 m / 0.00° | 0.0000 m / 0.00° | 0.0007 m / 0.00° |
| waypoint_step | 0.0401 m / 1.81° | 0.0422 m / 1.84° | 0.0257 m / 0.67° | 0.0266 m / 0.68° |
| circle_xy | 0.2248 m / 0.50° | 0.2174 m / 0.61° | 0.0053 m / 0.24° | 0.0046 m / 0.25° |
| full6_stress | 0.1587 m / 0.55° | 0.1511 m / 0.65° | 0.0077 m / 0.28° | 0.0061 m / 0.29° |
