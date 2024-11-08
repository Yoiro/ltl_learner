from collections import UserList

class Trace(UserList):
    '''
    This class implements ultimately periodic words.
    '''
    def __init__(self, spec = None) -> None:
        if not spec:
            spec = []
        self.data = spec['traces']
        self._path = [t for t in spec['traces']]
        self._repeat = spec['repeat']
        self._repeated_path = self._path[self._repeat::]
        self.u = '-'.join([''.join(p) for p in self._path[:self._repeat]])
        self.v = '-'.join([''.join(p) for p in self._repeated_path])

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


class Sample(UserList):
    '''
    This is a container class for Traces (being ultimately periodic words).
    '''
    def __init__(self, specs = None) -> None:
        if not specs:
            specs = []
        self.data = []
        self._raw_traces = specs
        self._traces = []
        for spec in specs:
            t = Trace(spec)
            self._traces.append(t)
            self.data.append(t)
    
    def __getitem__(self, key):
        return self._traces[key]

    def satisfies(self, phi):
        '''
        Checks whether this sample instance satisfies the given formula.
        '''
        for trace in self._traces:
            if not trace.satisfies(phi):
                return False
        return True
