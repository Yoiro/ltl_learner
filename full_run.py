import csv
import json
import time
import threading
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from ltl_learner.learner import Learner
from ltl_learner.traces import Sample

TIMEOUT = 300


def read_sample(sample: Path):
    with open(sample, 'r') as f:
        spec = json.load(f)
    return (
        spec['variables'],
        Sample(spec['positives']),
        Sample(spec['negatives']),
        spec.get('expected', '')
    )


def worker(filepath: Path, queue: mp.Queue):
    start = time.time_ns()
    l = Learner(k = 10, sample = filepath)
    ltl_formula, expected_formula = l.main()
    end = time.time_ns()
    total = (end - start) / 10**9
    queue.put_nowait([ltl_formula, total])


def main():
    dataset_folder = Path(Path(__file__) / '..' / 'dataset' / 'json').resolve()
    files = dataset_folder.glob('*.json')

    outfile_name = datetime.now().strftime('%Y%m%d%H%M%S')
    output = Path(Path(__file__) / '..' / 'results' / f'{outfile_name}_experiment.csv').resolve()

    csv_headers = [
        'experiment_time',
        'specs_file',
        'learned_formula',
        'expected_formula',
        'elapsed_time',
        'number_of_variables',
        'positive_length',
        'negative_length',
        'cutoff',
        'comment'
    ]

    with open(output, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

    i = 0
    total = len(list(files))
    files = dataset_folder.glob('*.json')
    for f in tqdm(files, total = total):
        i += 1
        queue = mp.Queue(5)
        experiment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        variables, positives, negatives, expected = read_sample(f)
        ltl_formula, elapsed_time, comment = '', '', ''
        p = mp.Process(target = worker, args = (f,queue,), )
        p.start()
        p.join(timeout = TIMEOUT)
        if p.is_alive:
            p.terminate()
        while p.exitcode is None:
            time.sleep(1)
        if p.exitcode == 0:
            ltl_formula, elapsed_time = queue.get()
        else:
            comment = f'timeout: {TIMEOUT}s'
        results = [
            experiment_time,
            f.name,
            ltl_formula,
            expected,
            elapsed_time,
            len(variables),
            len(positives), 
            len(negatives), 
            comment
        ]
        with open(output, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(results)

if __name__ == '__main__':
    main()