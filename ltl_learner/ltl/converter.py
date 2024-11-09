from z3 import And, Solver, is_true


class LTLConverter:
    def __init__(self, solver: Solver):
        self.solver = solver

    def build(self):
        psi = self.solver.model()
        true_vars = {x.name(): x for x in psi.decls() if is_true(psi[x])}
        dag = [x for x in true_vars.keys() if x.startswith('x_') or x.startswith('l_') or x.startswith('r_')]
        ys = [y for y in true_vars.keys() if y.startswith('y_')]
        print(dag)
        print(ys)
