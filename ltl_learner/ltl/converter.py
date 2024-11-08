from z3 import And, Solver, is_true


class LTLConverter:
    def __init__(self, solver: Solver):
        self.solver = solver

    def build(self):
        psi = self.solver.model()
        true_vars = [x for x in psi.decls() if is_true(psi[x])]
        print(self.solver.check())
