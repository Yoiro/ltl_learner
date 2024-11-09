import argparse
import logging
import sys
import time
from pathlib import Path

from ltl_learner.learner import Learner

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
root.addHandler(handler)


def positive_integer(n: int):
    n = int(n)
    return max([n, 0])

def strictly_positive_integer(n: int):
    n = int(n)
    return max([n, 1])


parser = argparse.ArgumentParser(
    prog = 'ltl_learner',
    description = '''
    This program will try to determine if a separating LTL formula for a given sample exists.
    The learned formula must be of maximum size k (which must be given). Even though k is not
    used in the original paper which this algorithm comes from, it is used here as a cutoff to ensure
    the program exits.
    '''
)
parser.add_argument('-f', '--input_file',
    action='store',
    help='The path to the file containing the samples for which we want to learn the LTL formula',
    type=Path,
    default=Path(Path(__file__) / '..' / 'mutex.json').resolve()
)
parser.add_argument('-k', '--cutoff',
    action='store',
    default=10,
    help='''
    The cutoff value for the number of variables of the computed DAG encoding the LTL formula.
    If any value below or equal to 0 is given, defaults to 1. If not specified, defaults to 10.
    ''',
    type=strictly_positive_integer
)
parser.add_argument('-o', '--operators',
    action='store',
    help='''
    A path to a (JSON) file specifying the operators to use. 
    This allows one to use only subsets of LTL should you desire it.
    ''',
    type=list,
    nargs='+',
    required=False
)
args = parser.parse_args()
start = time.time()
result = Learner(
    k=args.cutoff,
    sample=args.input_file,
    syntax=args.operators
).main()
end = time.time()

print(f"It took {end - start} seconds to give this answer.")
