class Trace(list):
    def __init__(self, spec) -> None:
        self._path = [t for t in spec['traces']]
        self._repeat = spec['repeat']
        self._repeated_path = self._path[self._repeat::]

    def __getitem__(self, key):
        if key < len(self._path):
            return self._path[key]
        else:
            return self._repeated_path[(key - self._repeat) % len(self._repeated_path)]

    def __eq__(self, value: object) -> bool:
        if self._repeat != value._repeat:
            return False
        for i, e in enumerate(value._path):
            if self._path[i] != e:
                return False
        return True


class Sample(list):
    def __init__(self, specs) -> None:
        self._raw_traces = specs
        self._traces = []
        for spec in specs:
            self._traces.append(Trace(spec))
    
    def __getitem__(self, key):
        return self._traces[key]

    def satisfies(self, phi):
        for trace in self._traces:
            if not trace.satisfies(phi):
                return False
        return True
