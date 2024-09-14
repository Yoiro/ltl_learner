from z3 import Bool, And, Or, Not

from ltl_learner.constants import operators

# We encode a syntax DAG with 3 types of variables:
#   * x_i_label (i in [1, ..., n] and label in {AP U C}) : if variable x_i_label is true, then node i is labeled with label
#   * l_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if l_i_j is set to true, j is the identifier to the left of node i.
#   * r_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if r_i_j is set to true, j is the identifier to the right of node i.

class DAGBuilder:
    def __init__(self, variables) -> None:
        self.variables = [Bool(v) for v in variables]
        self.symbols = set(self.variables).union(set(operators))

    def build(self, length: int) -> None:
        self.labels = self._get_labels(length)
        self.node_1 = self._get_node_1()
        if length == 1:
            return And(self.labels, self.node_1)
        self.left_children = self._get_left(length)
        self.right_children = self._get_right(length)

        return And(self.labels, self.left_children, self.right_children, self.node_1)
    
    def _get_labels(self, length):
        node_with_label = Or(*[Bool(f'{i}.{symb}') for i in range(length) for symb in self.symbols])
        only_one_label_per_node = And(
            And(
                Or(
                    Not(),
                    Not()
                )
            )
        )
        return And(node_with_label, only_one_label_per_node)

    def _get_node_1(self):
        return Or(self.variables)            
