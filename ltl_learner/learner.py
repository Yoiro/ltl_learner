import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from z3 import Solver

from ltl_learner.constants import operators
from ltl_learner.dag.builder import DAGBuilder
from ltl_learner.ltl.converter import LTLConverter
from ltl_learner.traces import Sample


class Learner:
    def __init__(self, k: int = 10, sample: Path = None, max_words: int = 10, operators_file = None):
        self.root_folder = Path(Path(__file__) / '..').resolve()
        self.file_name = f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.smtlib2'
        self.cutoff = k
        self.variables, self.positive, self.negative = self.read_sample(sample)
        ops = {"operators": []}
        if operators_file:
            with open(operators, 'r') as f:
                ops = json.load(f)
        self.builder = DAGBuilder(deepcopy(self.variables), ops=ops["operators"])
        self.converter = LTLConverter()
        self.output_file = str(Path(self.root_folder / 'results' / self.file_name))
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w') as f:
                f.write(f';; Run {self.file_name}\n')
                f.write(f';; Parameters\n')
                f.write(f';;    cutoff: {self.cutoff}\n')
                f.write(f';;    variables: {", ".join(self.variables)}\n')
                f.write(f';;    operators: {", ".join(operators)}\n')
        self.solver = Solver()
        self.sat = None

    def read_sample(self, sample):
        with open(sample, 'r') as f:
            spec = json.load(f)
        return (
            spec['variables'],
            Sample(spec['positives']),
            Sample(spec['negatives'])
        )

    def is_sat(self, phi, push = True):
        if push:
            self.solver.push()
            self.solver.add(phi)
            self.sat = self.solver.check()
        return self.sat

    def write_model(self):
        with open(self.output_file, 'a') as f:
            f.write(self.solver.sexpr())

    def main(self):
        n = 0
        satisfied = False
        while not satisfied:
            n += 1
            phi = self.builder.build(n)
            if self.is_sat(phi) or n > self.cutoff:
                break
        if self.is_sat(phi, push = False):
            print("Found a valid truth assignation. Registering it in results.")
            self.write_model()
            return self.converter.build(phi.model)
        else:
            print("Unable to determine a formula within the given constraint.")
            return phi
