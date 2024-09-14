from pathlib import Path

import pytest

from ltl_learner.learner import Learner

@pytest.fixture
def default_learner():
    return Learner(sample=Path(Path(__file__) / '..' / 'mutex.json').resolve())
