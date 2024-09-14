import pytest

from ltl_learner.traces import Trace

@pytest.fixture
def trace_len5_repeat2():
    return Trace(spec = {
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["wait1", "wait2"],
            ["crit1", "wait2"],
            ["noncrit1", "wait2"]
        ],
        "repeat": 2
    })


@pytest.fixture
def trace_len5_repeat1():
    return Trace(spec = {
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["wait1", "wait2"],
            ["crit1", "wait2"],
            ["crit1", "crit2"]
        ],
        "repeat": 1
    })