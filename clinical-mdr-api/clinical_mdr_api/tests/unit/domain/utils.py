import random
import uuid
from typing import Optional, Sequence


def random_str() -> str:
    return str(uuid.uuid4())


def random_int(int_min: int = 0, int_max: int = 1000) -> int:
    return random.randint(int_min, int_max)


def random_opt_str(null_probability: float = 0.5) -> Optional[str]:
    return None if random.random() < null_probability else random_str()


def random_opt_c_code(
    c_code_list: Sequence[str], null_probability: float = 0.5
) -> Optional[str]:
    return None if random.random() < null_probability else random.choice(c_code_list)[0]


def random_c_code_sequence(
    c_code_list: Sequence[str], null_probability: float = 0.5
) -> Sequence[str]:
    result = []
    while random.random() >= null_probability:
        result.append(random.choice(c_code_list)[0])
    return result


def random_str_sequence() -> Sequence[str]:
    probability = 0.3
    result = []
    while random.random() >= probability:
        result.append(random_str())
    return result
