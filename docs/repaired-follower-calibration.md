# Repaired follower calibration (2026-10-19)

`robots/so101/calibration/mnri_arms_1_follower.json` now matches the saved
calibration used for the repaired cube-to-cup follower on USB serial
`5AAF263600`. These are raw servo encoder values, not degrees or normalized
gripper percentages.

| Joint | Field | Previous value | Repaired follower |
| --- | --- | ---: | ---: |
| shoulder_lift (ID 2) | homing_offset | -1983 | 1088 |
| shoulder_lift (ID 2) | range_min | 756 | 790 |
| shoulder_lift (ID 2) | range_max | 3097 | 3296 |
| gripper (ID 6) | range_min | 2005 | 1031 |
| gripper (ID 6) | range_max | 3541 | 2496 |

All other follower entries, including the gripper homing offset (860), are
unchanged. This update changes the saved configuration only; it does not run
calibration, write motor registers, or move hardware.

The source is the cube-to-cup project's
`calibration/robots/so101_follower/repaired-shoulder-1792448625156379989/cup_follower_repaired.json`.
That calibration was used during recording and attended inference on the repaired
arm. The PR preparation checks the JSON against that saved source; the recording
launcher in this repository has not been exercised on hardware with this change.

## Leader pairing

The cube-to-cup setup also used a replacement leader, USB serial `5AAF264132`.
This repository's `scripts/so101_env.sh` still selects leader serial `5AAF263743`
and its existing leader calibration. This follower-only update does not make
those two leader setups interchangeable. Before recording, select the calibration
matching the actual leader and verify alignment with the existing pose checks.
Do not use the follower's calibration for the leader or copy these values to a
different arm just because it uses the same SO-101 model.
