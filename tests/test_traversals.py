from ts_utils.cursor_utils import tuple_cursor
from ts_utils.traversals import NO_CONTEXT, Moves, NoContext, broadcastl, traverse

import collections


def test_walk_tree():
    tree = (1, (2, 3), (4, (5, )))

    cursor = tuple_cursor(tree)

    items = [(cursor.node, last_move)
             for cursor, last_move in traverse(cursor)]

    assert items == [
        (1, Moves.DOWN),
        (2, Moves.DOWN),
        (3, Moves.DOWN),
        (3, Moves.UP),
        (2, Moves.UP),
        (4, Moves.RIGHT),
        (5, Moves.DOWN),
        (5, Moves.UP),
        (4, Moves.UP),
        (1, Moves.UP),
    ]


def test_walk_tree_filter_skipped_node_last_sibling():
    tree = (1, (2, 3), (4, (5, )))
    cursor = tuple_cursor(tree)
    items = [(cursor.node, last_move) for cursor, last_move in traverse(
        cursor, should_traverse=lambda c: c.node != 4)]
    assert items == [
        (1, Moves.DOWN),
        (2, Moves.DOWN),
        (3, Moves.DOWN),
        (3, Moves.UP),
        (2, Moves.UP),
        (1, Moves.UP),
    ]


def test_walk_tree_filter_skipped_node_before_last_sibling():
    tree = (1, (2, 3), (4, (5, )))
    cursor = tuple_cursor(tree)
    items = [(cursor.node, last_move) for cursor, last_move in traverse(
        cursor, should_traverse=lambda c: c.node != 2)]
    assert items == [
        (1, Moves.DOWN),
        (4, Moves.DOWN),
        (5, Moves.DOWN),
        (5, Moves.UP),
        (4, Moves.UP),
        (1, Moves.UP),
    ]


def test_broadcastl():

    tree = (1, (4, (5, (6, 7))))

    context = ({1: "root", 5: "child", 6: "grandchild"})

    stream = traverse(tuple_cursor(tree))
    stream = broadcastl(lambda _, cursor: context.get(cursor.node, NO_CONTEXT)).bind(
        stream)
    results = collections.defaultdict(set)

    for context_value, (cursor, _) in stream:
        if context_value != NO_CONTEXT:
            results[cursor.node].add(context_value)

    assert results == {
        # 1 should not have any context
        4: {"root"},
        5: {"root"},
        6: {"child"},
        7: {"grandchild"}
    }


def get_context(prev_context: int | NoContext, cursor ) -> int | NoContext:
        match (prev_context, cursor.node):
            case (NoContext(), _):
                return cursor.node
            case (int(n), _):
                return n * 10 + cursor.node
            case _:
                return NO_CONTEXT
            

def test_broadcastl_with_reducer():
    tree = (1, (4, (5, (6, 7))))

    stream = traverse(tuple_cursor(tree))
    stream = broadcastl(get_context).bind(stream)
    results = collections.defaultdict(set)

    for context_value, (cursor, _) in stream:
        if context_value != NO_CONTEXT:
            results[cursor.node].add(context_value)

    assert results == {
        # 1 should not have any context
        
        4: {1},
        5: {14},
        6: {145},
        7: {1456}
        
    }

# def test_broadcastr():
#     tree = (1, (4, (5, (6, 7))))

#     stream = traverse(tuple_cursor(tree))
#     stream = broadcastl(get_context).bind(stream)
#     results = collections.defaultdict(set)

#     for context_value, (cursor, _) in stream:
#         if context_value != NO_CONTEXT:
#             results[cursor.node].add(context_value)

#     assert results == {
#         # 1 should not have any context
        
#         4: {1},
#         5: {14},
#         6: {145},
#         7: {1456}
        
#     }