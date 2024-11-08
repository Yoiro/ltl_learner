from typing import Any, Union

from z3 import Bool, And, Or, Not, Implies

from ltl_learner.constants import operators
from ltl_learner.traces import Sample, Trace

# We encode a syntax DAG with 3 types of variables:
#   * x_i_label (i in [1, ..., n] and label in {AP U O}) : if variable x_i_label is true, then node i is labeled with label
#   * l_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if l_i_j is set to true, j is the identifier to the left of node i.
#   * r_i_j (i in [2, ..., n] and j in [1, ..., i - 1]): if r_i_j is set to true, j is the identifier to the right of node i.

class DAGBuilder:
    def __init__(self, solver=None, variables: list[Any]=None, ops: Union[None, list, set, tuple] = None) -> None:
        self.solver = solver
        self.variables = variables
        self.labels = None
        self.node_1 = None
        self.left_children = None
        self.right_children = None
        self.vars = {}
        self.x = {}
        self.y = {}
        self.l = {}
        self.r = {}
        self.current_length = 0
        if not ops:
            ops = operators['all']
        self.operators = [o for o in ops if o in operators['all']]
        self.symbols = set(self.variables).union(set(self.operators))
    
    def _reset(self):
        self.labels = None
        self.node_1 = None
        self.left_children = None
        self.right_children = None
        self.vars = {}
        self.current_length = 0

    def generate_vars(self, length: int) -> dict[str, Bool]:
        '''
        Generates all basic variables to declare for the model.
        It will generate a combination of all operators for all 
        integers in the range of the given length.
        :return: a dict with keys being all DAG variables identifiers, 
                and values being the z3.Bool() matching the identifier.
        '''
        vars = {}
        for i in range(length):
            # for symb in self.symbols:
            #     self.x[(i, symb)] = Bool(f'x_{i}_{symb}')
            var_i = {f'x_{i}_{symb}': Bool(f'x_{i}_{symb}') for symb in self.symbols}
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
        self._reset()
        self.current_length = length
        self.vars = self.generate_vars(length)
        self.labels = self._get_labels(length)
        self.node_1 = self._get_node_1()
        if length == 1:
            # self.solver.assert_and_track()
            return self.solver
        # And(self.labels, self.node_1)

        self.l = self._get_left(length)
        # We don't need to compute right_children formula if there are only 2 nodes in the DAG.
        if length == 2:
            return self.solver
            # return And(self.labels, self.node_1, self.left_children)

        self.r = self._get_right(length)
        # return And(self.labels, self.left_children, self.right_children, self.node_1)
        return self.solver

    def _get_left(self, length: int) -> And:
        '''
        Builds the "left children" constraints for the given length.
        '''
        return self._gen_structure(length, 'L')

    def _get_right(self, length: int) -> And:
        '''
        Builds the "right children" constraints for the given length.
        '''
        return self._gen_structure(length, 'R')

    def _gen_structure(self, length: int, side: str) -> And:
        '''
        Generates the variables encoding the DAG structure.
        Variables will range from 0 to length - 1, and will be 
        prefixed with the given lowercased side (e.g. 'l_i_j', 'r_i_j').
        :return: The constraint for the given side in the form of a z3.And object.
        '''
        ops = self.operators
        if side == 'R':
            ops = [o for o in self.operators if o in operators['binary']]
        vars = []
        unique = []
        # for i in range(1, length):
        #     for j in range(0, i):
        #         self.l[(i, j)] = Bool('l_{i}_{j}')
        #         if i > 1:
        #             self.r[(i, j)] = Bool('r_{i}_{j}')
        for op in ops:
            labelled_vars = []
            for i in range(1, length):
                l_i = []
                uniq_i = []
                for j in range(0, i):
                    name = f'{side.lower()}_{i}_{j}'
                    l_i_j = Bool(name)
                    self.vars[name] = l_i_j
                    l_i.append(l_i_j)
                    uniq_i.append(And(*[
                        Or(Not(l_i_j), Not(self.vars[f'{side.lower()}_{i}_{k}'])) 
                        for k in range(0, j)
                    ]))
                children = Or(*l_i)
                vars.append(children)
                unique.append(And(*uniq_i))
                labelled_vars.append(Implies(self.vars[f'x_{i}_{op}'], children))
        self.solver.assert_and_track(And(And(*vars), And(*unique)), f"nodes on {side}")
        return And(And(*vars), And(*unique))

    def _create_consistence_variables(self, i: int, word: Trace) -> None:
        for t in range(len(word)):
            var_name = f'y_{word.u}_{word.v}_{i}_{t}'
            self.y[(word.u, word.v, i, t)] = Bool(var_name)
        return self.y

    # def add_consistency_with(self, base_formula: And, sample: Sample, positive = True) -> And:
    def add_consistency_with(self, sample: Sample, positive = True) -> None:
        '''
        Computes the formulas in order to add consistency for the given sample.
        If positive is set to False, then makes sure the given formula does not satisfy the sample
        by AND-ing it with the negation of y^{u,v}_{n,1}, as stated in the article.
        '''
        for i in range(self.current_length):
            for word in sample:
                self._create_consistence_variables(i, word)
                # self.solver.assert_and_track(self.add_ap_constraints(i, word), f"atoms for node {i} of word {word.u} {word.v}")
                self.add_ap_constraints(i, word)
                if i > 0:
                    # self.solver.assert_and_track(self.add_or_constraints(i, word), f"or semantics for node {i} of word {word.u} {word.v}")
                    # self.solver.assert_and_track(self.add_not_constraints(i, word), f"and semantics for node {i} of word {word.u} {word.v}")
                    # self.solver.assert_and_track(self.add_u_constraints(i, word), f"until semantics for node {i} of word {word.u} {word.v}")
                    # self.solver.assert_and_track(self.add_x_constraints(i, word), f"next semantics for node {i} of word {word.u} {word.v}")
                    self.add_not_constraints(i, word)
                    self.add_x_constraints(i, word)
                if i > 1:
                    self.add_or_constraints(i, word)
                    self.add_u_constraints(i, word)
                    # self.solver.assert_and_track(self.add_u_constraints(i, word), f"until semantics for node {i} of word {word.u} {word.v}")
                    # self.solver.assert_and_track(self.add_or_constraints(i, word), f"or semantics for node {i} of word {word.u} {word.v}")
        if positive:
            self.solver.assert_and_track(self.y[(word.u, word.v, i, 0)], f"ensure models models positive samples")
        else:
            self.solver.assert_and_track(Not(self.y[(word.u, word.v, i, 0)]), f"ensure models does not model positive samples")
        # return And(base_formula, *formulas)
    
    def add_ap_constraints(self, i: int, word: Trace) -> And:
        # x_i_a -> A_{1 <= t <= |uv|} y^{uv}_{it} if a in uv[t]
        # x_i_a -> A_{1 <= t <= |uv|} ~y^{uv}_{it} if a not in uv[t]
        # self.solver.assert_and_track([Implies(
        #     And(
        #         self.x[(i, a)],
        #         And(self.y[word.u, word.v, i, t] if a in word)
        #     )]
        # ) for a in self.variables])
        # sub_formulas = []
        # for a in self.variables:
        #     x = self.vars[f'x_{i}_{a}']
        self.solver.assert_and_track(
            And(
                *[Implies(
                    self.vars[f'x_{i}_{a}'],
                    And(*[
                        self.y[(word.u, word.v, i, t)] if a in word
                        else Not(self.y[(word.u, word.v, i, t)]) 
                        for t in range(len(word))
                    ])
                ) for a in self.variables]
            ), f"atoms semantics for node {i} on word {word.u} {word.v}"
        )
        # return And(*sub_formulas)
    
    def _get_children_of(self, i: int):
        return (
            [(k, v) for k, v in self.vars.items() if k.startswith(f'l_{i}_')],
            [(k, v) for k, v in self.vars.items() if k.startswith(f'r_{i}_')]
        )

    def add_or_constraints(self, i: int, word: Trace) -> And:
        self.solver.assert_and_track(
            And(*[
                Implies(
                    And(self.vars[f'x_{i}_v'], self.vars[f'l_{i}_{j}'], self.vars[f'r_{i}_{jp}']),
                    And(*[
                        self.y[(word.u, word.v, i, t)] == Or(
                            self.y[(word.u, word.v, j, t)],
                            self.y[(word.u, word.v, jp, t)]
                        )
                    for t in range(len(word))])
                )
                for j in range(i) for jp in range(i)
            ]),
            f"or semantics for node {i} on word {word.u} {word.v}"
        )
        # sub_formulas = []
        # left_children, right_children = self._get_children_of(i)
        # x = self.vars[f'x_{i}_v']
        # for lid, l_child in left_children:
        #     j = lid.split('_')[-1]
        #     for rid, r_child in right_children:
        #         jp = rid.split('_')[-1]
        #         left = And(x, l_child, r_child)
        #         right = []
        #         for t, y in enumerate(ys):
        #             right.append(
        #                 y == Or(
        #                     self.vars[f'y_{word.u}_{word.v}_{j}_{t}'],
        #                     self.vars[f'y_{word.u}_{word.v}_{jp}_{t}']
        #                 )
        #             )
        #         sub_formulas.append(Implies(left, And(*right)))
        # return And(*sub_formulas)

    def add_not_constraints(self, i: int, word: Trace) -> And:
        # sub_formulas = []
        # left_children, _ = self._get_children_of(i)
        # x = self.vars[f'x_{i}_!']
        # for j in range(i):
        # for l, child in left_children:
        #     j = l.split("_")[-1]
        #     left = And(x, child)
        #     right = []
        self.solver.assert_and_track(
            And(*[
                Implies(
                    And(self.vars[f'x_{i}_!'], self.vars[f'l_{i}_{j}']),
                    And(*[
                        self.y[(word.u, word.v, i, t)] == Not(self.y[(word.u, word.v, j, t)])
                    for t in range(len(word))])
                )
            for j in range(i)]), f"not semantics for node {i} on word {word.u} {word.v}")
        #     for t, y in enumerate(ys):
        #         right.append(y == Not(self.vars[f'y_{word.u}_{word.v}_{j}_{t}']))
        #     sub_formulas.append(Implies(left, And(*right)))
        # return And(*sub_formulas)

    def add_x_constraints(self, i: int, word: Trace) -> And:
        self.solver.assert_and_track(
            And(*[
                Implies(
                    And(self.vars[f'x_{i}_X'], self.vars[f'l_{i}_{j}']),
                    And(
                        And(*[
                            self.y[(word.u, word.v, i, t)] == self.y[(word.u, word.v, j, t + 1)]
                            for t in range(len(word) - 1)
                        ]),
                        self.y[(word.u, word.v, i, len(word) - 1)] == self.y[(word.u, word.v, j, word._repeat)]
                    )
                )
            for j in range(i)])
        , f"next semantics for node {i} on word {word.u} {word.v}")
        # sub_formulas = []
        # left_children, _ = self._get_children_of(i)
        # x = self.vars[f'x_{i}_X']
        # for lid, child in left_children:
        #     j = lid.split('_')[-1]
        #     left = And(x, child)
        #     right = []
        #     for t in range(len(ys) - 1):
        #         right.append(ys[t] == self.vars[f'y_{word.u}_{word.v}_{j}_{t + 1}'])
        #     right.append(ys[-1] == self.vars[f'y_{word.u}_{word.v}_{j}_{word._repeat}'])
        #     sub_formulas.append(Implies(left, And(*right)))
        # return And(*sub_formulas)

    def add_u_constraints(self, i: int, word: Trace) -> And:
        self.solver.assert_and_track(
            And(*[
                Implies(
                    And(self.vars[f'x_{i}_U'], self.vars[f'l_{i}_{j}'], self.vars[f'r_{i}_{jp}']),
                    And(
                        And(*[
                            self.y[(word.u, word.v, i, t)] == Or(*[
                                And(
                                    self.y[(word.u, word.v, jp, tp)],
                                    And(*[
                                        self.y[(word.u, word.v, j, tpp)]
                                        for tpp in range(t, tp)
                                    ])
                                )
                                for tp in range(t, len(word))
                            ])
                            for t in range(word._repeat)
                        ]),
                        And(*[
                            self.y[(word.u, word.v, i, t)] == Or(*[
                                And(
                                    self.y[(word.u, word.v, jp, tp)],
                                    And(*[
                                        self.y[(word.u, word.v, j, tpp)]
                                        for tpp in self._generate_aux_set(word, t, tp)
                                    ])
                                )
                                for tp in range(word._repeat, len(word))
                            ])
                            for t in range(word._repeat, len(word))
                        ])
                    )
                )
                for j in range(i) for jp in range(i) if j != jp
            ]),
            f"until semantics for node {i} on word {word.u} {word.v}"
        )
        # sub_formulas = []
        # left_children, right_children = self._get_children_of(i)
        # x = self.vars[f'x_{i}_U']
        # for lid, lchild in left_children:
        #     j = lid.split('_')[-1]
        #     for rid, rchild in right_children:
        #         left = And(x, lchild, rchild)
        #         jp = rid.split('_')[-1]
        #         right_1 = []
        #         right_2 = []
        #         for t in range(word._repeat):
        #             y = self.vars[f'y_{word.u}_{word.v}_{i}_{t}']
        #             r = []
        #             for tt in range(word._repeat, len(word)):
        #                 r.append(
        #                     And(
        #                         self.vars[f'y_{word.u}_{word.v}_{jp}_{tt}'],
        #                         And(*[
        #                             v for k, v in self.vars.items()
        #                             if k in [
        #                                 f'y_{word.u}_{word.v}_{j}_{ttt}'
        #                                 for ttt in range(t, tt)
        #                             ]
        #                         ])
        #                     )
        #                 )
        #             right_1.append(y == Or(*r))
        #         for t in range(word._repeat, len(word)):
        #             y = self.vars[f'y_{word.u}_{word.v}_{i}_{t}']
        #             r = []
        #             for tt in range(word._repeat, len(word)):
        #                 r.append(
        #                     And(
        #                         self.vars[f'y_{word.u}_{word.v}_{jp}_{tt}'],
        #                         And(*[
        #                             v for k, v in self.vars.items()
        #                             if k in [
        #                                 f'y_{word.u}_{word.v}_{j}_{ttt}'
        #                                 for ttt in self._generate_aux_set(word, t, tt)
        #                             ]
        #                         ])
        #                     )
        #                 )
        #             right_2.append(y == Or(*r))
        #         sub_formulas.append(Implies(left, And(*right_1, *right_2)))
        # return And(*sub_formulas)

    def _generate_aux_set(self, word: Trace, start: int, end: int):
        if start < end:
            return range(start, end)
        if end <= word._repeat:
            return []
        l = [i for i in range(word._repeat, end - 1)]
        r = [i for i in range(start, len(word))]
        return l + r

    def _get_labels(self, length: int) -> And:
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
            node_i = Or(*[self.vars[f'x_{i}_{symb}'] for symb in self.symbols])
            names.append(node_i)

        # node_with_label = And(*names)
        # node_with_label = self.solver.assert_and_track(And(*names), "each node has a label")

        nodes = []
        for i in range(length):
            node_i = []
            for label in self.symbols:
                not_label_i = Not(self.vars[f'x_{i}_{label}'])
                not_other_labels_i = [Not(self.vars[f'x_{i}_{symb}']) for symb in set(self.symbols) - set([label])]
                node_i.append(And(*[Or(not_label_i, other_label) for other_label in not_other_labels_i]))
            nodes.append(And(*node_i))
        self.solver.assert_and_track(And(And(*names), And(*nodes)), "each node has only one label")
        # only_one_label_per_node = And(*nodes)
        # return And(node_with_label, only_one_label_per_node)

    def _get_node_1(self) -> Or:
        '''
        Returns the formula encoding the node at index 1 of the DAG.
        That node needs to be labeled with an atomic proposition, 
        i.e. one of the variables given in the .json file containing the traces

        :return: the formula encoding the constraint that node 1 must be an atomic proposition.
        :@type return: z3.Or
        '''
        self.solver.assert_and_track(Or(*[self.vars[f'x_0_{var}'] for var in self.variables]), "node 1 must be an atom")
