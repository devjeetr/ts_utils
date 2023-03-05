import dataclasses
import enum
import functools
from typing import Callable, Generic, Iterator, NewType, Optional, Sequence, Type, TypeVar, cast
from tree_sitter import TreeCursor
from ts_utils.cursor_utils import Cursor
from typing import dataclass_transform, Any, ParamSpec

import abc

CursorLike = TypeVar("CursorLike", bound=Cursor)
"""Any object that implements the [Cursor][ts_utils.cursor_utils.Cursor] protocol."""


class Moves(enum.Enum):
    """Enum representing the possible moves that can be made by a TreeCursor."""
    RIGHT = enum.auto()
    """corresponds to `cursor.goto_next_sibling()`"""
    UP = enum.auto()
    """corresponds to `cursor.goto_parent()`"""
    DOWN = enum.auto()
    """corresponds to `cursor.goto_first_child()`"""


def traverse(
    cursor: CursorLike,
    should_traverse: Optional[Callable[[Cursor], bool]] = None
) -> Iterator[tuple[CursorLike, Moves]]:
    """Iteratively walk tree-sitter trees using the TreeCursor API.

    The recommended way to traverse a `tree-sitter` tree is to use the
    `TreeCursor` API. However, the api is stateful and requires some bookkeeping
    for iterative traversals. This function abstracts away the bookkeeping
    and walks the tree using the cursor using the minimum number of moves possible.
    This is a low-level primitive that can be used to build tree traversals such
    as preorder, postorder etc. 
    
    Warning:
        Do not modify the cursor once you start walking the tree. If you want to use
        the cursor during iterations, make a copy using `TreeCursor.copy()`.
    Args:
        cursor: stateful cursor like object. This cursor will be mutated.
        should_traverse: a function that decides whether or not to traverse the subtree
                        rooted at a given node. Defaults to None.
 

    Yields:
        A tuple of the cursor and the move that was made
    """
    reached_root = False
    results = []

    last_move: Moves = Moves.DOWN
    while not reached_root:
        skip_current_node = not should_traverse(
            cursor) if should_traverse else False

        if not skip_current_node:
            yield cursor, last_move

        # Here, we filter if we want to go down this
        # subtree or not
        if not skip_current_node:
            if cursor.goto_first_child():
                last_move = Moves.DOWN
                continue

            # Leaf: No child nodes, but we pretend like
            # we went to the subtree at this node and
            # came back up
            yield cursor, Moves.UP

        if cursor.goto_next_sibling():
            last_move = Moves.RIGHT if not skip_current_node else Moves.DOWN
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                reached_root = True
                break

            yield cursor, Moves.UP

            if cursor.goto_next_sibling():
                last_move = Moves.RIGHT
                break
    return results


CursorStep = tuple[CursorLike, Moves]


def filter_moves(
    *moves: Moves
) -> Callable[[Iterator[tuple[CursorLike, Moves]]], Iterator[tuple[CursorLike,
                                                                   Moves]]]:
    return lambda iterator: filter(lambda x: x[1] in moves, iterator)


def with_height(iterator: Iterator[CursorStep[CursorLike]]):
    height = 0
    for cursor, move in iterator:
        if move in (Moves.RIGHT, Moves.DOWN):
            height += 1
            yield height, (cursor, move)
        else:
            yield height, (cursor, move)
            height -= 1


class NoContext(object):

    def __repr__(self):
        return "NoContext"


NO_CONTEXT = NoContext()
ContextValue = TypeVar("ContextValue")

T = TypeVar("T")
CursorStream = Iterator[CursorStep[CursorLike]]
StreamTransform = Callable[[CursorStream[CursorLike]],
                           CursorStream[CursorLike]]
WithCursorStream = Callable[[CursorStream[CursorLike]],
                            Iterator[tuple[T, CursorStep[CursorLike]]]]

# def broadcastr(
#     fn: Callable[[CursorLike, Sequence[ContextValue | NoContext]],
#                  ContextValue | NoContext]
# ) -> WithCursorStream[CursorLike, ContextValue | NoContext]:
#     context_stack = [
#         [],
#     ]
#     forward = (Moves.RIGHT, Moves.DOWN)
#     retracing = (Moves.UP, )

#     def _stream_transform(iterator: CursorStream[CursorLike], ):
#         for height, (cursor, move) in with_height(iterator):
#             if move in retracing:
#                 if context_stack:
#                     context_height, _ = context_stack[-1]
#                     if context_height == height:
#                         child_contexts = context_stack.pop()
#                         parent_context = fn(cursor, child_contexts)

#             if not context_stack:
#                 yield NO_CONTEXT, (cursor, move)
#             else:
#                 yield context_stack[-1][1], (cursor, move)

#             if move in forward:
#                 prev_context: tuple[
#                     NoContext | ContextValue,
#                     ...] = context_stack[-1][1] if context_stack else (
#                         NO_CONTEXT, )

#                 context_value = fn(prev_context)
#                 if not isinstance(context_value, NoContext):
#                     pass
#                     # context_stack.append((Height(height), context_value))

#     return _stream_transform

T = TypeVar("T")
S = TypeVar("S")


class TraversalHook(abc.ABC, Generic[CursorLike, T]):
    """A traversal hook is a mechanism for user code to hook into the lifecycle of a tree traversal.
    Traversal hooks are composeable via the `merge` method or the `|` operator.
    """

    @abc.abstractmethod
    def snapshot(self) -> T:
        """Returns a snapshot of the value of the hook at the current node."""
        ...

    def enter(self, step: CursorStep[CursorLike]):
        """Called when the cursor performs performs step into a new node."""
        del step

    def exit(self, step: CursorStep[CursorLike]):
        """Called when the cursor is about to leav the current node and onto the next step."""
        del step

    def bind(
        self, stream: CursorStream[CursorLike]
    ) -> Iterator[tuple[T, CursorStep[CursorLike]]]:
        """Binds this hook to a tree traversal.

        Args:
            stream: The traversal stream to bind to. 

        Returns:
            the original stream unchanged 
        """
        for step in stream:
            self.enter(step)
            yield self.snapshot(), step
            self.exit(step)

    def __or__(
        self, other: "TraversalHook[CursorLike, S]"
    ) -> "TraversalHook[CursorLike, tuple[T, S]]":
        return self.merge(other)

    def merge(
        self, other: "TraversalHook[CursorLike, S]"
    ) -> "TraversalHook[CursorLike, tuple[T, S]]":
        """Merges "other" with this hook.

        Args:
            other: the hook to merge with 

        Returns:
            a new hook that merges the results of this hook and "other" 
        """
        return MergedHooks((self, other))


class MergedHooks(TraversalHook[CursorLike, tuple[T, S]]):
    """Represents a higher order hook that merges the results of two child hooks.

    """

    def __init__(self, hooks: tuple[TraversalHook[CursorLike, T],
                                    TraversalHook[CursorLike, S]]):
        self.hooks = hooks

    def snapshot(self) -> tuple[T, S]:
        return tuple(hook.snapshot() for hook in self.hooks)

    def enter(self, step: CursorStep[CursorLike]):
        for hook in self.hooks:
            hook.enter(step)

    def exit(self, step: CursorStep[CursorLike]):
        for hook in self.hooks:
            hook.exit(step)


P = ParamSpec("P")


def field(
    value: Callable[P, Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> Any:
    if not issubclass(value, TraversalHook):  # type: ignore
        raise ValueError(f"Field value must be a subclass of TraversalHook")

    return functools.partial(value, *args, **kwargs)


T = TypeVar("T")


@dataclass_transform(field_specifiers=(field, ))
def attribute_collection(cls: Type[T]) -> Type[T]:
    return cls


class HookCollection(TraversalHook):
    """A collection of traversal hooks.

    Example:

    ```python
    
    @attribute_collection
    class MyHooks:
        foo: field(FooHook)
        bar: field(BarHook)
    
    hooks = MyHooks()

    stream = traverse(tree.walk())

    for snapshot, step in hooks.bind(stream):
        snapshot.foo # OK
        snapshot.bar # OK
        snapshot.baz # Type Error!!
    ```

    """

    def __init__(self):
        self._traversal_hooks = {}
        fields = {}
        for field_name in self.__annotations__:
            field_value = getattr(self, field_name)
            fields[field_name] = field_value()
        self._traversal_hooks: dict[str, TraversalHook] = fields
        self._result_dataclass = dataclasses.dataclass(frozen=True)(type(self))

    def enter(self, step: CursorStep[CursorLike]):
        for hook in self._traversal_hooks.values():
            hook.enter(step)

    def exit(self, step: CursorStep[CursorLike]):
        for hook in self._traversal_hooks.values():
            hook.exit(step)

    def snapshot(self):
        return self._result_dataclass(
            **{
                field_name: hook.snapshot()
                for field_name, hook in self._traversal_hooks.items()
            })


class Height(TraversalHook[CursorLike, int]):

    def __init__(self) -> None:
        self.height = 0

    def enter(self, step: CursorStep[CursorLike]):
        _, move = step
        if move == Moves.DOWN:
            self.height += 1

    def exit(self, step: CursorStep[CursorLike]):
        _, move = step
        if move == Moves.UP:
            self.height -= 1

    def snapshot(self):
        return self.height


NodeHeight = NewType("NodeHeight", int)
Initial = TypeVar("Initial")


class BroadcastL(Generic[ContextValue, CursorLike],
                 TraversalHook[CursorLike, ContextValue | NoContext]):

    def __init__(
        self,
        fn: Callable[[ContextValue | NoContext, CursorLike], ContextValue],
    ):
        self.fn = fn
        self.context_stack: list[tuple[NodeHeight, ContextValue]] = []
        self.height_hook = Height()

    def snapshot(self):
        return NO_CONTEXT if not self.context_stack else self.context_stack[
            -1][1]

    def enter(self, step):
        self.height_hook.enter(step)

        height = self.height_hook.snapshot()
        _, move = step
        if move == Moves.UP:
            if self.context_stack:
                context_height, _ = self.context_stack[-1]
                if context_height == height:
                    self.context_stack.pop()

    def exit(self, step: CursorStep[CursorLike]):
        cursor, move = step
        self.height_hook.exit(step)
        height = self.height_hook.snapshot()
        if move in (Moves.RIGHT, Moves.DOWN):
            prev_context = self.context_stack[-1][
                1] if self.context_stack else NO_CONTEXT

            context_value = self.fn(prev_context, cursor)
            if not isinstance(context_value, NoContext):
                self.context_stack.append((NodeHeight(height), context_value))


def broadcastl(fn: Callable[[ContextValue | NoContext, CursorLike],
                            ContextValue | NoContext] = lambda x, _: x,
               ):
    return BroadcastL(fn)
