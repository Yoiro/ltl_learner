import json
import os
import uuid
from multiprocessing.pool import ThreadPool
from pathlib import Path


def generate_word(trace_in: str, variables: list):
    trace, repeat = trace_in.split('::')
    json_traces = []
    for word in trace.split(';'):
        w = []
        for i, symbol in enumerate(word.split(',')):
            if symbol == '1':
                w.append(variables[i])
        json_traces.append(w)
    return {
        "traces": json_traces,
        "repeat": int(repeat),
    }


def convert_trace(raw_trace):
    trace = raw_trace.read_text()
    positives, negatives, operators, num_variables, expected_result = trace.split('---')
    positives = positives.strip()
    negatives = negatives.strip()
    operators = operators.strip()
    num_variables = num_variables.strip()
    expected_result = expected_result.strip()
    num_variables = int(num_variables)
    json_trace = {
        "variables": [f'x{i}' for i in range(num_variables)],
        "positives": [],
        "negatives": [],
        "expected": expected_result
    }
    json_trace['positives'] = [
        generate_word(positive, json_trace['variables'])
        for positive in positives.split('\n')
    ]
    json_trace['negatives'] = [
        generate_word(negative, json_trace['variables'])
        for negative in negatives.split('\n')
    ]
    with open(Path(Path(__file__) / '..' / 'json' / f'{uuid.uuid4().hex}.json').resolve(), 'w') as f:
        json.dump(json_trace, f, indent = 2)
    return json_trace


def main():
    workers = os.cpu_count() * 2 + 1
    root = Path(Path(__file__) / '..').resolve()
    with ThreadPool(processes = workers) as pool:
        pool.map(convert_trace, root.glob('raw/**/*.trace'))


if __name__ == '__main__':
    main()
