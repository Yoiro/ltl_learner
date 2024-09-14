import argparse
from pathlib import Path

from ltl_learner.learner import Learner


def positive_integer(n: int):
    return max([n, 0])

def strictly_positive_integer(n: int):
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
    The cutoff value for the computed DAG encoding the LTL formula.
    If any value below or equal to 0 is given, defaults to 1.
    ''',
    type=strictly_positive_integer
)
parser.add_argument('-n', '--num_words',
    action='store',
    default=10,
    help='''
    The maximum number of words to take into account (since traces are infinite over AP).
    If any value below or equal to 0 is given, defaults to 1.
    ''',
    type=strictly_positive_integer
)
args = parser.parse_args()
result = Learner(k = args.cutoff, sample = args.input_file, max_words = args.num_words).main()
print(result)