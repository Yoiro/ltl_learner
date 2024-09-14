from tests.fixtures.traces import *
from tests import helpers


def test_indexing_trace_should_return_word(trace_len5_repeat2):
    helpers.test_trace(trace_len5_repeat2, [
        ["noncrit1", "noncrit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"]
    ])


def test_indexing_outside_trace_should_cycle_infinitely(trace_len5_repeat2, trace_len5_repeat1):
    helpers.test_trace(trace_len5_repeat2, [
        ["noncrit1", "noncrit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["noncrit1", "wait2"]
    ])

    helpers.test_trace(trace_len5_repeat1, [
        ["noncrit1", "noncrit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["crit1", "crit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["crit1", "crit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["crit1", "crit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["crit1", "crit2"],
        ["wait1", "noncrit2"],
        ["wait1", "wait2"],
        ["crit1", "wait2"],
        ["crit1", "crit2"],
    ])