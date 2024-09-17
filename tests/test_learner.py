from ltl_learner.traces import Trace

from tests.fixtures.learner import (
    default_learner,
    learner_with_ops,
    operators_ux_or_not
)


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


def test_learner_with_specified_operators(learner_with_ops, operators_ux_or_not):
    assert learner_with_ops.cutoff == 10
    assert learner_with_ops.variables == ["noncrit1", "wait1", "crit1", "noncrit2", "wait2", "crit2"]
    assert learner_with_ops.positive[0] == Trace({
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["crit1", "noncrit2"]
        ],
        "repeat": 0
    })
    assert learner_with_ops.negative[0] == Trace({
        "traces": [
            ["noncrit1", "noncrit2"],
            ["wait1", "noncrit2"],
            ["wait1", "wait2"],
            ["crit1", "wait2"],
            ["crit1", "crit2"]
        ],
        "repeat": 1
    })
    for e in learner_with_ops.builder.operators:
        assert e in operators_ux_or_not
    for e in operators_ux_or_not:
        assert e in learner_with_ops.builder.operators

# def test_learner_should_return_formula(default_learner):
#     result = default_learner.main()
