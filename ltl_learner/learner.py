import json
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from z3 import Solver

from ltl_learner.constants import operators
from ltl_learner.dag.builder import DAGBuilder
from ltl_learner.ltl.converter import LTLConverter
from ltl_learner.traces import Sample

logger = logging.getLogger(__name__)


class Learner:
    def __init__(self, k: int = 10, sample: Path = None, syntax = None):
        self.root_folder = Path(Path(__file__) / '..').resolve()
        self.file_name = f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.smtlib2'
        self.cutoff = k
        self.variables, self.positive, self.negative = self.read_sample(sample)
        ops = {}
        if syntax:
            ops = syntax
        self.solver = Solver()
        self.builder = DAGBuilder(solver=self.solver, variables=deepcopy(self.variables), ops=ops)
        self.converter = LTLConverter(self.solver)
        self.output_file = str(Path(self.root_folder / 'results' / self.file_name))
        self.sat = None

    def read_sample(self, sample):
        with open(sample, 'r') as f:
            spec = json.load(f)
        return (
            spec['variables'],
            Sample(spec['positives']),
            Sample(spec['negatives'])
        )
    
    def is_sat(self):
        self.solver.check()
        return self.solver.model()

    def write_model(self):
        logger.info('Writing z3 model expression tree.')
        logger.info(f'  Using file {self.output_file}')
        with open(self.output_file, 'w') as f:
            f.write(f';; Run {self.file_name}\n')
            f.write(f';; Parameters\n')
            f.write(f';;    cutoff: {self.cutoff}\n')
            f.write(f';;    variables: {", ".join(self.variables)}\n')
            f.write(f';;    operators: {", ".join(operators["all"])}\n')
            f.write(self.solver.sexpr())

    def main(self):
        logger.info('Starting to compute an LTL formula.')
        n = 1
        logger.info(f'Computing DAG of length {n}')
        self.builder.build(n, self.positive, self.negative)
        while True:
            if self.is_sat() or n > self.cutoff:
                break
            self.solver.reset()
            n += 1
            logger.info(f"Computing DAG of length {n}")
            self.builder.build(n, self.positive, self.negative)
        if n <= self.cutoff:
            logger.info("Found a valid truth assignation.")
            self.write_model()
            logger.info('Now computing the matching LTL formula.')
            return self.converter.build(length = n)
        else:
            logger.info("Unable to determine a formula within the given constraint.")
            return self.solver
