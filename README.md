# space-teleoperation

Research program and runnable testbed for ground teleoperation of robot arms inside a LEO
spacecraft to collect physical-AI demonstrations.

Start with the [second-wave report](docs/REPORT.md), [results page](docs/arms_in_orbit.html),
[current decision record](docs/research/SYNTHESIS.md), and [testbed specification](docs/TESTBED_SPEC.md).
The [first-wave report](docs/REPORT_WAVE1.md) and experiment artifacts remain available as historical evidence.

```sh
uv sync --frozen
uv run pytest -q
uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 3
```

The testbed uses synthetic operators and simplified MuJoCo tasks over localhost UDP. It is not
flight-qualified, and its NPZ recordings are not a loadable LeRobot dataset. See the report for
corrected experiments, evidence limits and the reproduction protocol.
