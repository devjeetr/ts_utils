from functools import reduce
from typing import Callable, Optional, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


def all_true(*fns: Optional[Callable[P, bool]]) -> Callable[P, bool]:
    valid_fns = [fn for fn in fns if fn is not None]

    def _inner(*args: P.args, **kwargs: P.kwargs) -> bool:
        def reducer(prev: bool, fn: Callable):
            return fn(*args, **kwargs) and prev

        return reduce(reducer, valid_fns, True)

    return _inner
