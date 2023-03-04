import enum
from typing import Callable, Generic, Iterator, NewType, Optional, Sequence, TypeVar
from tree_sitter import TreeCursor
from ts_utils.cursor_utils import Cursor

CursorLike = TypeVar("CursorLike", Cursor, TreeCursor)
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


Height = NewType("Height", int)


class NoContext(object):

    def __repr__(self):
        return "NoContext"


NO_CONTEXT = NoContext()
ContextValue = TypeVar("ContextValue")


class Context(Generic[CursorLike, ContextValue]):
    __slots__ = ("fn", "context_stack")

    def __init__(
        self,
        fn: Callable[[CursorLike], ContextValue | NoContext],
    ) -> None:
        self.fn = fn
        self.context_stack: list[tuple[Height, ContextValue]] = []

    @property
    def value(self):
        if not self.context_stack:
            return NO_CONTEXT

        return self.context_stack[-1][1]

    def __call__(
        self, iterator: Iterator[CursorStep[CursorLike]]
    ) -> Iterator[CursorStep[CursorLike]]:
        forward = (Moves.RIGHT, Moves.DOWN)
        for height, (cursor, move) in with_height(iterator):
            if move in forward:
                yield cursor, move

                context_value = self.fn(cursor)
                if not isinstance(context_value, NoContext):
                    self.context_stack.append((Height(height), context_value))
            else:
                if self.context_stack:
                    context_height, value = self.context_stack[-1]
                    if context_height == height:
                        self.context_stack.pop()
                yield cursor, move


T = TypeVar("T")
CursorStream = Iterator[CursorStep[CursorLike]]
StreamTransform = Callable[[CursorStream[CursorLike]],
                           CursorStream[CursorLike]]
WithCursorStream = Callable[[CursorStream[CursorLike]],
                            Iterator[tuple[T, CursorStep[CursorLike]]]]


def broadcastl(
    fn: Callable[[ContextValue | NoContext, CursorLike],
                 ContextValue | NoContext] = lambda x, _: x
) -> WithCursorStream[CursorLike, ContextValue | NoContext]:
    context_stack = []
    forward = (Moves.RIGHT, Moves.DOWN)
    retracing = (Moves.UP, )

    def _stream_transform(iterator: CursorStream[CursorLike], ):
        for height, (cursor, move) in with_height(iterator):
            if move in retracing:
                if context_stack:
                    context_height, _ = context_stack[-1]
                    if context_height == height:
                        context_stack.pop()
            if not context_stack:
                yield NO_CONTEXT, (cursor, move)
            else:
                yield context_stack[-1][1], (cursor, move)
            if move in forward:
                prev_context = context_stack[-1][
                    1] if context_stack else NO_CONTEXT

                context_value = fn(prev_context, cursor)
                if not isinstance(context_value, NoContext):
                    context_stack.append((Height(height), context_value))

    return _stream_transform


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
