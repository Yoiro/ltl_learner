from tests.fixtures.results import result_length_7, converter

def test_tree_str(result_length_7, converter):
    tree = converter.build(length = 7, true_nodes = result_length_7)
    assert tree == 'U(!(F(&(crit2,crit1))),|(crit2,crit1))'