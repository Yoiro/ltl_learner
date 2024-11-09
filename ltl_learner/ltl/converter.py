import logging

from z3 import And, Solver, is_true

from ltl_learner.constants import operators

logger = logging.getLogger(__name__)


class Node:
    def __init__(self, id, label, left = None, right = None):
        self.label = label
        self.left = left
        self.right = right
        self.id = id

    def __str__(self):
        acc = f'{self.label}'
        if self.label in operators['all']:
            acc += '('
            if self.left:
                acc += f'{self.left}'
            if self.right:
                acc += f',{self.right}'
            acc += ')'
        return acc

class Tree:
    def __init__(self):
        self.root = None
    
    def add_node(self, node):
        self.nodes.append(node)

    def get_formula(self):
        return str(self.root)


class LTLConverter:
    def __init__(self, solver: Solver):
        self.solver = solver

    def build(self, length: int, true_nodes = None):
        if not true_nodes:
            psi = self.solver.model()
            true_vars = {x.name(): x for x in psi.decls() if is_true(psi[x])}
            dag = [x for x in true_vars.keys() if x.startswith('x_') or x.startswith('l_') or x.startswith('r_')]
            logger.info(f"Variables set to true:  {dag}")
            true_nodes = list(sorted(dag, key = lambda n: n.split('_')[1]))
        tree = Tree()
        nodes = {}
        for i in range(length):
            label = [n for n in true_nodes if n.startswith(f'x_{i}_')][0].split('_')[-1]
            nodes[i] = Node(i, label)
        for i in range(length):
            left = [n for n in true_nodes if n.startswith(f'l_{i}_')]
            if left:
                left = int(left[0].split('_')[-1])
                nodes[i].left = nodes[left]
            right = [n for n in true_nodes if n.startswith(f'r_{i}_')]
            if right:
                right = int(right[0].split('_')[-1])
                nodes[i].right = nodes[right]
        tree.root = nodes[length - 1]
        logger.info('Computed tree from SAT assignation.')
        logger.info(f'  {tree}')
        logger.info('LTL Formula:')
        logger.info(f'  {tree.get_formula()}')
        return tree.get_formula()
