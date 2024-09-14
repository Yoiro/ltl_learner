import json
import os

from dag.builder import DAGBuilder
from ltl.converter import LTLConverter
from traces import Traces


class Learner:
    def __init__(self, k: int = 10, sample: os.Pathlike = None, max_words: int = 10):
        # k = args.cutoff, sample = args.input_file, max_words = args.num_words
        self.cutoff = k
        self.builder = DAGBuilder()
        self.converter = LTLConverter()
        self.variables, self.positive, self.negative = self.read_sample(sample)

    def read_sample(self, sample):
        with open(sample, 'r') as f:
            spec = json.load(f)
        return (
            spec['variables'],
            Traces(spec['positives']),
            Traces(spec['negatives'])
        )

    def main(self):
        n = 0
        satisfied = False
        while not satisfied:
            n += 1
            phi = self.builder.build(n)
            if phi.sat or n > self.cutoff:
                break
        if phi.sat:
            return self.converter.build(phi.model)
        else:
            return "Unable to determine a formula within the given constraint."