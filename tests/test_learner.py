from ltl_learner.traces import Trace

from tests.fixtures.learner import default_learner


def test_learner_should_correctly_load(default_learner):
    assert default_learner.cutoff == 10
    assert default_learner.variables == ["noncrit1", "wait1", "crit1", "noncrit2", "wait2", "crit2"]
    assert default_learner.positive[0] == Trace({
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["crit1", "noncrit2"]
        ],
        "repeat": 0
    })
    assert default_learner.negative[0] == Trace({
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["wait1", "wait2"],
            ["crit1", "wait2"],
            ["crit1", "crit2"]
        ],
        "repeat": 1
    })


def test_learner_should_return_formula(default_learner):
    result = default_learner.main()
