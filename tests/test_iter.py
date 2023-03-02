from ts_utils.iter import iternodes
from ts_utils.cursor_utils import tuple_cursor, Cursor


def test_iternodes_follows_preorder():
    tree = (1, (4, (2, 3), (5, 6)), (7, 8))

    cursor = tuple_cursor(tree)

    nodes = list(iternodes(cursor))
    assert nodes == [1, 4, 2, 3, 5, 6, 7, 8]


def test_iternodes_traversal_filter():
    tree = (1, (4, (2, 3), (5, 6)), (7, 8))

    cursor = tuple_cursor(tree)

    nodes = list(iternodes(cursor, lambda n: n not in (2, 7)))
    assert nodes == [1, 4, 5, 6]