# v3 allocation screen (CF2, seen step missions)

| variant | mission | controller | mean q-error [rad] | z_min [m] | alpha_min | torque scaled frac |
|---|---|---|---|---|---|---|
| tpa | hardstep | pid | 0.4355 | 0.725 | 0.272 | 0.0039 |
| tpa | hardstep | st_pid | 2.3944 | 0.016 | 0.000 | 0.9354 |
| tpa | hardstep | dual | 2.4612 | 0.018 | 0.000 | 0.9618 |
| tpa | hardstep_b | pid | 0.3738 | 0.659 | 0.633 | 0.0051 |
| tpa | hardstep_b | st_pid | 0.3173 | 0.607 | 0.534 | 0.0063 |
| tpa | hardstep_b | dual | 2.4782 | 0.012 | 0.000 | 0.9081 |
| tpa_r | hardstep | pid | 0.4319 | 0.174 | 1.000 | 0.0000 |
| tpa_r | hardstep | st_pid | 2.4567 | 0.017 | 1.000 | 0.0000 |
| tpa_r | hardstep | dual | 2.4212 | 0.018 | 1.000 | 0.0000 |
| tpa_r | hardstep_b | pid | 0.3728 | 0.130 | 1.000 | 0.0000 |
| tpa_r | hardstep_b | st_pid | 2.4061 | 0.016 | 1.000 | 0.0000 |
| tpa_r | hardstep_b | dual | 2.5119 | 0.015 | 1.000 | 0.0000 |
| apa | hardstep | pid | 0.4319 | 0.740 | 1.000 | 0.0000 |
| apa | hardstep | st_pid | 0.3624 | 0.642 | 1.000 | 0.0000 |
| apa | hardstep | dual | 2.1067 | 0.017 | 1.000 | 0.0000 |
| apa | hardstep_b | pid | 0.3728 | 0.659 | 1.000 | 0.0000 |
| apa | hardstep_b | st_pid | 0.3155 | 0.607 | 1.000 | 0.0000 |
| apa | hardstep_b | dual | 0.3474 | 0.600 | 1.000 | 0.0000 |

**Selected: `apa`** (tie on worst-case z_min (0.015 vs 0.017); lower geo-mean error (1.3400 vs 0.4878)).
Worst-case z_min / geo-mean error: tpa_r 0.015 m / 1.3400 rad; apa 0.017 m / 0.4878 rad.
