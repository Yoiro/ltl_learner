from itertools import zip_longest

from z3 import Bool, And, Or, Not

from ltl_learner.constants import operators

# We encode a syntax DAG with 3 types of variables:
#   * x_i_label (i in [1, ..., n] and label in {AP U C}) : if variable x_i_label is true, then node i is labeled with label
#   * l_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if l_i_j is set to true, j is the identifier to the left of node i.
#   * r_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if r_i_j is set to true, j is the identifier to the right of node i.

class DAGBuilder:
    def __init__(self, variables, ops = None) -> None:
        self.variables = variables
        self.labels = None
        self.node_1 = None
        self.left_children = None
        self.right_children = None
        self.vars = {}
        if not ops:
            ops = []
        self.operators = [o for o in operators if o not in ops]
        self.symbols = set(self.variables).union(set(self.operators))

    def generate_vars(self, length):
        vars = {}
        for i in range(length):
            var_i = {f'{i}.{symb}': Bool(f'{i}.{symb}') for symb in self.symbols}
            vars.update(var_i)
        return vars

    def build(self, length: int) -> None:
        '''
        Constructs the full formula that encodes a DAG with the given number of nodes.
        :@param length: The length of the DAG to compute. 
                        This corresponds to the number of node within the DAG.
        :return: The conjunction of all formulas that encode a different constraint
                 modeling the DAG of an LTL formula.
        :@type return: z3.And()
        '''
        self.vars = self.generate_vars(length)
        self.labels = self._get_labels(length)
        self.node_1 = self._get_node_1()
        if length == 1:
            return And(self.labels, self.node_1)
        self.left_children = self._get_left(length)
        self.right_children = self._get_right(length)
        return And(self.labels, self.left_children, self.right_children, self.node_1)

    def _get_left(self, length):
        return self._gen_structure(length, 'L')
    
    def _get_right(self, length):
        return self._gen_structure(length, 'R')

    def _gen_structure(self, length, side: str):
        left_vars = []
        left_unique = []
        for i in range(1, length):
            l_i = []
            uniq_i = []
            for j in range(0, i):
                name = f'{side}.{i}.{j}'
                l_i_j = Bool(name)
                self.vars[name] = l_i_j
                l_i.append(l_i_j)
                uniq_i.append(And(*[
                    Or(Not(l_i_j), Not(self.vars[f'{side}.{i}.{k}'])) 
                    for k in range(0, j)
                ]))
            left_vars.append(Or(*l_i))
            left_unique.append(And(*uniq_i))
        return And(And(*left_vars), And(*left_unique))

    def _get_labels(self, length):
        '''
        Computes the formulas to force nodes to have one (and only one) label.
        Label is contained in the union between the sets representing the variables
        given and the allowed operators for the considered LTL.

        :return: an object with two children constraints: 
                 one that encodes the fact that node i must have a label assigned, 
                 and the other that ensures that node i only has a single label assigned.
        :@type return: z3.And(z3.And(z3.Or(z3.Not, z3.Not)), z3.And(z3.Or))
        '''
        names = []
        for i in range(length):
            node_i = Or(*[self.vars[f'{i}.{symb}'] for symb in self.symbols])
            names.append(node_i)

        node_with_label = And(*names)

        nodes = []
        for i in range(length):
            node_i = []
            for label in self.symbols:
                not_label_i = Not(self.vars[f'{i}.{label}'])
                not_other_labels_i = [Not(self.vars[f'{i}.{symb}']) for symb in set(self.symbols) - set([label])]
                node_i.append(And(*[Or(not_label_i, other_label) for other_label in not_other_labels_i]))
            nodes.append(And(*node_i))
        only_one_label_per_node = And(*nodes)
        return And(node_with_label, only_one_label_per_node)

    def _get_node_1(self):
        '''
        Returns the formula encoding the node at index 1 of the DAG.
        That node needs to be labeled with an atomic proposition, 
        i.e. one of the variables given in the .json file containing the traces

        :return: the formula encoding the constraint that node 1 must be an atomic proposition.
        :@type return: z3.Or
        '''
        return Or(*[self.vars[f'0.{var}'] for var in self.variables])
