from ts_utils.cursor_utils import tuple_cursor
from ts_utils.traversals import Moves, walk_tree


def test_walk_tree():
    tree = (1, (2, 3), (4, (5, )))

    cursor = tuple_cursor(tree)

    items = [(cursor.node, last_move)
             for cursor, last_move in walk_tree(cursor)]

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
    items = [(cursor.node, last_move) for cursor, last_move in walk_tree(
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
    items = [(cursor.node, last_move) for cursor, last_move in walk_tree(
        cursor, should_traverse=lambda c: c.node != 2)]
    assert items == [
        (1, Moves.DOWN),
        (4, Moves.DOWN),
        (5, Moves.DOWN),
        (5, Moves.UP),
        (4, Moves.UP),
        (1, Moves.UP),
    ]
