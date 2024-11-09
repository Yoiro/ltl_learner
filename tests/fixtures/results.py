import pytest
from z3 import Solver

from ltl_learner.ltl.converter import LTLConverter


@pytest.fixture
def converter():
    return LTLConverter(Solver())


@pytest.fixture
def result_length_7():
    return [
        'x_6_U',
        'l_6_4',
        'x_4_!',
        'l_4_3',
        'x_3_F',
        'l_3_2',
        'x_2_&',
        'l_2_1',
        'x_1_crit2',
        'r_2_0',
        'x_0_crit1',
        'r_6_5',
        'x_5_|',
        'l_5_1',
        'r_5_0',
    ]