def test_trace(trace, expected):
    for i, t in enumerate(expected):
        assert trace[i] == t