from typing import Any, Union

from z3 import Bool, And, Or, Not, Implies, AtMost, AtLeast, Solver

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
        self.solver.set(unsat_core = True)

    def generate_vars(self, length: int, positives: Sample, negatives: Sample) -> tuple:
        '''
        Generates all variables to declare for the model and store them on this builder instance.
        :return: a 4-length tuple corresponding to the variables (x_il, l_ij, r_ij, yuv_it).
        '''
        for i in range(length):
            for symb in self.symbols:
                name = f'x_{i}_{symb}'
                self.x[(i, symb)] = Bool(name)
        for i in range(1, length):
            for j in range(i):
                self.l[(i, j)] = Bool(f'l_{i}_{j}')
                self.r[(i, j)] = Bool(f'r_{i}_{j}')
        for i in range(length):
            for j, trace in enumerate(positives):
                for t in range(len(trace)):
                    self.y[(i, 'p', j, t)] = Bool(f'y_{i}_p_{j}_{t}')
            for j, trace in enumerate(negatives):
                for t in range(len(trace)):
                    self.y[(i, 'n', j, t)] = Bool(f'y_{i}_n_{j}_{t}')
        return self.x, self.l, self.r, self.y

    def build(self, length: int, positives: Sample, negatives: Sample) -> Solver:
        '''
        Constructs the full formula that encodes a DAG with the given number of nodes.
        :@param length: The length of the DAG to compute. 
                        This corresponds to the number of node within the DAG.
        :@param positives: The positive words to learn from
        :@param negatives: The negative words to learn from
        :return: This builder's instance solver.
        '''
        self._reset()
        self.current_length = length
        self.generate_vars(length, positives, negatives)
        self.add_node_1_constraints()
        self.add_general_constraints(length)
        if self.current_length > 1:
            self._get_left(length)
            self._get_right(length)
        self.add_consistency_with(positives)
        self.add_consistency_with(negatives, positive = False)

        self.solver.assert_and_track(
            And(*[
                self.y[(self.current_length - 1, 'p', word_idx, 0)]
                for word_idx in range(len(positives))
            ]),
            f"ensure model models positive samples"
        )
        self.solver.assert_and_track(
            And(*[
                Not(self.y[(self.current_length - 1, 'n', word_idx, 0)])
                for word_idx in range(len(negatives))
            ]),
            f"ensure model does not model negative samples"
        )
        return self.solver
    
    def add_general_constraints(self, length: int):
        self.solver.assert_and_track(And(*[
            AtMost(*[self.x[t] for t in self.x if t[0] == i] + [1])
            for i in range(length)
        ]), 'at most one label per node')
        self.solver.assert_and_track(And(*[
            AtLeast(*[self.x[t] for t in self.x if t[0] == i] + [1])
            for i in range(length)
        ]), 'at least one label per node')
        if self.current_length > 1:
            self.solver.assert_and_track(
                And(*[
                    And(*[
                        Or(
                            Not(self.l[(i, j)]),
                            Not(self.r[(i, j)])
                        )
                        for j in range(i)
                    ])
                    for i in range(length)
                ]),
                f'nodes cannot have the same child on left and on right'
            )
            self.solver.assert_and_track(
                And(*[
                    Implies(
                        Or(*[self.x[(i, a)] for a in self.variables]),
                        Not(
                            Or(
                                Or(*[self.r[t] for t in self.r if t[0] == i]),
                                Or(*[self.l[t] for t in self.l if t[0] == i])
                            )
                        )
                    )
                    for i in range(1, length)
                ]),
                'variables cannot have children'
            )
            self.solver.assert_and_track(
                And(*[
                    Or(
                        AtLeast(*[self.l[(parent, i)] for parent in range(i + 1, length)] + [1]),
                        AtLeast(*[self.r[(parent, i)] for parent in range(i + 1, length)] + [1])
                    )
                    for i in range(length - 1)
                ]),
                "ensure that lower variables have at least one parent"
            )

    def _get_left(self, length: int) -> And:
        '''
        Builds the "left children" constraints for the given length.
        '''
        self.solver.assert_and_track(
            And(*[
                Implies(
                    Or(*[self.x[(i, op)] for op in self.operators]),
                    AtMost(*[self.l[t] for t in self.l if t[0] == i] + [1])
                )
                for i in range(1, length)
            ]), "at most one left operand per operator"
        )

        self.solver.assert_and_track(
            And(*[
                Implies(
                    Or(*[self.x[(i, op)] for op in self.operators]),
                    AtLeast(*[self.l[t] for t in self.l if t[0] == i] + [1])
                )
                for i in range(1, length)
            ]), "at least one left operand per operator"
        )

    def _get_right(self, length: int) -> And:
        '''
        Builds the "right children" constraints for the given length.
        '''
        unaries = [o for o in self.operators if o in operators['unary']]
        binaries = [o for o in self.operators if o in operators['binary']]
        self.solver.assert_and_track(
            And(*[
                Implies(
                    Or(*[self.x[(i, op)] for op in binaries]),
                    AtMost(*[self.r[t] for t in self.r if t[0] == i] + [1])
                )
                for i in range(1, length)
            ]), "at most one right operand per binary operator"
        )
        self.solver.assert_and_track(
            And(*[
                Implies(
                    Or(*[self.x[(i, op)] for op in binaries]),
                    AtLeast(*[self.r[t] for t in self.r if t[0] == i] + [1])
                )
                for i in range(1, length)
            ]), "at least one right operand per binary operator"
        )
        self.solver.assert_and_track(
            And(*[
                Implies(
                    Or(*[self.x[(i, op)] for op in unaries]),
                    Not(
                        Or(*[self.r[t] for t in self.r if t[0] == i])
                    )
                )
                for i in range(1, length)
            ]), 'unary operators cannot have a right operand'
        )

    def add_consistency_with(self, sample: Sample, positive = True) -> None:
        '''
        Computes the formulas in order to add consistency for the given sample.
        If positive is set to False, then makes sure the given formula does not satisfy the sample
        by AND-ing it with the negation of y^{u,v}_{n,1}, as stated in the article.
        '''
        symbol = 'p' if positive else 'n'
        for i in range(self.current_length):
            for j, word in enumerate(sample):
                self.add_ap_constraints(i, word, j, symbol)
                if '!' in self.operators:
                    self.add_not_constraints(i, word, j, symbol)
                if 'X' in self.operators:
                    self.add_x_constraints(i, word, j, symbol)
                if 'G' in self.operators:
                    self.add_g_constraints(i, word, j, symbol)
                if 'F' in self.operators:
                    self.add_f_constraints(i, word, j, symbol)
                if '|' in self.operators:
                    self.add_or_constraints(i, word, j, symbol)
                if '&' in self.operators:
                    self.add_and_constraints(i, word, j, symbol)
                if 'U' in self.operators:
                    self.add_u_constraints(i, word, j, symbol)
                if '>' in self.operators:
                    self.add_implication_constraints(i, word, j, symbol)
    
    def add_ap_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        for a in self.variables:
            self.solver.assert_and_track(
                    Implies(
                        self.x[(i, a)],
                        And(*[
                            self.y[(i, symbol, word_idx, t)] if a in word[t] else Not(self.y[(i, symbol, word_idx, t)])
                            for t in range(len(word))
                        ])
                    ),
                f"atom {a} semantics for node {i} on {symbol} word number {word_idx}"
            )

    def add_not_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, '!')],
                And(*[
                    Implies(
                        And(self.x[(i, '!')], self.l[(i, j)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == Not(
                                self.y[(j, symbol, word_idx, t)]
                            )
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i)
                ])
            ),
            f"not semantics for node {i} on {symbol} word number {word_idx}"
        )

    def add_x_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, 'X')],
                And(*[
                    Implies(
                        And(self.x[(i, 'X')], self.l[(i, j)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == self.y[(j, symbol, word_idx, word.next_index(t))]
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i)
                ])
            ),
            f"next semantics for node {i} on {symbol} word number {word_idx}"
        )
    
    def add_g_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, 'G')],
                And(*[
                    Implies(
                        And(self.x[(i, 'G')], self.l[(i, j)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == And(*[
                                self.y[(j, symbol, word_idx, tp)]
                                for tp in word.generate_aux_set(t)
                            ])
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i)
                ])
            ),
            f'semantics of the globally operator on {symbol} word {word_idx} for node {i}'
        )

    def add_f_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, 'F')],
                And(*[
                    Implies(
                        And(self.x[(i, 'F')], self.l[(i, j)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == Or(*[
                                self.y[(j, symbol, word_idx, tp)]
                                for tp in word.generate_aux_set(t)
                            ])
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i)
                ])
            ),
            f'semantics of the finally operator on {symbol} word {word_idx} for node {i}'
        )
    
    def add_or_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, '|')],
                And(*[
                    Implies(
                        And(self.x[(i, '|')], self.l[(i, j)], self.r[(i, jp)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == Or(*[
                                self.y[(j, symbol, word_idx, t)],
                                self.y[(jp, symbol, word_idx, t)]
                            ])
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i) for jp in range(i)
                ])
            ),
            f"or semantics for node {i} on {symbol} word number {word_idx}"
        )
    
    def add_and_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, '&')],
                And(*[
                    Implies(
                        And(self.x[(i, '&')], self.l[(i, j)], self.r[(i, jp)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == And(*[
                                self.y[(j, symbol, word_idx, t)],
                                self.y[(jp, symbol, word_idx, t)]
                            ])
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i) for jp in range(i)
                ])
            ),
            f"and semantics for node {i} on {symbol} word number {word_idx}"
        )
    
    def add_implication_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, '>')],
                And([
                    Implies(
                        And(self.x[(i, '>')], self.l[(i, j)], self.r[(i, jp)]),
                        And([
                            self.y[(i, symbol, word_idx, t)] == Implies(
                                self.y[(j, symbol, word_idx, t)],
                                self.y[(jp, symbol, word_idx, t)]
                            )
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i) for jp in range(i)
                ])
            ),
            f'implies semantics for node {i} on {symbol} word {word_idx}'
        )

    def add_u_constraints(self, i: int, word: Trace, word_idx: int, symbol: str) -> None:
        self.solver.assert_and_track(
            Implies(
                self.x[(i, 'U')],
                And(*[
                    Implies(
                        And(self.x[(i, 'U')], self.l[(i, j)], self.r[(i, jp)]),
                        And(*[
                            self.y[(i, symbol, word_idx, t)] == Or(*[
                                And(
                                    [self.y[(j, symbol, word_idx, tp)] for tp in word.generate_aux_set(t)[0:tpp]] +
                                    [self.y[(jp, symbol, word_idx, word.generate_aux_set(t)[tpp])]]
                                )
                                for tpp in range(len(word.generate_aux_set(t)))
                            ])
                            for t in range(len(word))
                        ])
                    )
                    for j in range(i) for jp in range(i)
                ])
            ),
            f"until semantics for node {i} on {symbol} word number {word_idx}"
        )

    def add_node_1_constraints(self) -> None:
        '''
        Adds the formula encoding the node at index 1 of the DAG.
        That node needs to be labeled with an atomic proposition, 
        i.e. one of the variables given in the .json file containing the traces
        '''
        self.solver.assert_and_track(
            Or([self.x[(0, a)] for a in self.variables]),
            "node 1 must be an atom"
        )
