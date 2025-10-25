from typing import NamedTuple

params_dict = {"a": 1, "b": 2.0}


class Params(NamedTuple):
    a: int
    b: float


def create_params(params_dict: dict) -> Params:
    return Params(**params_dict)


params = create_params(params_dict)

print(params)
