from tests.fixtures.learner import default_learner

from ltl_learner.constants import operators


def test_dag_length_1_should_return_only_labels_and_node_1(default_learner):
    dag_length_1 = default_learner.builder.build(1)
    parts = dag_length_1.children()
    assert len(parts) == 2

    assert len(parts[0].children()) == len(set(operators)) + len(set(default_learner.builder.variables))
    for variable in parts[0].children():
        assert any([o not in str(variable) for o in operators]) # Size one formula can only contain a variable
    for variable in parts[1].children():
        assert any([str(v) in str(variable) for v in default_learner.builder.variables])
    assert len(parts[1].children()) == len(set(default_learner.builder.variables))
