from tests.fixtures.learner import default_learner

from ltl_learner.constants import operators


def test_dag_length_1_should_return_only_labels_and_node_1(default_learner):
    dag_length_1 = default_learner.builder.build(1)
    parts = dag_length_1.children()
    assert len(parts) == 2
    # Test becomes really complex -- will write it later
