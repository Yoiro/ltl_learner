from pathlib import Path

import pytest

from ltl_learner.learner import Learner

@pytest.fixture
def operators_ux_or_not():
    return ('U', 'X', 'v', '!')

@pytest.fixture
def default_learner():
    return Learner(sample=Path(Path(__file__) / '..' / 'mutex.json').resolve())


@pytest.fixture
def learner_with_ops(operators_ux_or_not):
    return Learner(
        sample=Path(Path(__file__) / '..' / 'mutex.json').resolve(),
        syntax=operators_ux_or_not
    )