import json
from copy import deepcopy
from pathlib import Path

from ltl_learner.dag.builder import DAGBuilder
from ltl_learner.ltl.converter import LTLConverter
from ltl_learner.traces import Sample


class Learner:
    def __init__(self, k: int = 10, sample: Path = None, max_words: int = 10):
        self.cutoff = k
        self.variables, self.positive, self.negative = self.read_sample(sample)
        self.builder = DAGBuilder(deepcopy(self.variables))
        self.converter = LTLConverter()

    def read_sample(self, sample):
        with open(sample, 'r') as f:
            spec = json.load(f)
        return (
            spec['variables'],
            Sample(spec['positives']),
            Sample(spec['negatives'])
        )

    def main(self):
        n = 0
        satisfied = False
        while not satisfied:
            n += 1
            phi = self.builder.build(n)
            return phi
            if phi.sat or n > self.cutoff:
                break
        if phi.sat:
            return self.converter.build(phi.model)
        else:
            return "Unable to determine a formula within the given constraint."