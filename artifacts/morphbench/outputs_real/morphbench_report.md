# MorphBench — local suite report

Budget per task: **24** units  |  E2E tasks: **5**  |  Systems: **3**

## Mean leaderboard percentile (Tier B)

| System | Mean LB percentile | Completion rate | Mean redundant rate |
|---|---|---|---|
| SingleAgent | 87.12 | 1.0 | 0.4833 |
| CentralScheduler | 87.29 | 1.0 | 0.425 |
| MorphSwarm | 87.29 | 1.0 | 0.425 |

## Swarm mechanism metrics (Tier A)

| Metric | Value |
|---|---|
| SB-01_swarm_survival | 1.0 |
| SB-01_central_survival | 0.0 |
| SB-01_swarm_units_used | 20 |
| SB-01_central_units_used | 10 |
| SB-02_reuse_gain | 0.0 |
| SB-02_cold_units_to_target | 9 |
| SB-02_warm_units_to_target | 9 |
| SB-03_overhead_ratio | 2.8632 |
| SB-03_base_wall_seconds | 4.8838 |
| SB-03_swarm_wall_seconds | 18.8669 |
| SB-04_redundant_rate | 0.425 |