from ts_utils.cursor_utils import tuple_cursor


def test_tuple_cursor_moves():
    tree = (1, (2, 3), (4, (5, )))

    cursor = tuple_cursor(tree)
    value = cursor.node
    assert value == 1
    assert cursor.goto_first_child(), "Should be able to move to first child"
    assert cursor.node == 2

    assert cursor.goto_parent()
    assert cursor.node == 1

    assert not cursor.goto_next_sibling()
    assert cursor.node == 1

    assert not cursor.goto_parent()
    assert cursor.node == 1

    cursor.goto_first_child()
    assert cursor.node == 2
    assert cursor.goto_next_sibling()
    assert cursor.node == 4

    assert cursor.goto_first_child()
    assert cursor.node == 5

    assert not cursor.goto_first_child()
    assert cursor.goto_parent()
    assert cursor.node == 4

    assert cursor.goto_parent()
    assert cursor.node == 1

    assert not cursor.goto_parent()
    assert cursor.node == 1

    assert not cursor.goto_parent()
    assert cursor.node == 1


def test_cursor_copy():
    tree = (1, 2, 3)

    original = tuple_cursor(tree)
    assert original.goto_first_child()

    copied = original.copy()

    assert original.node == copied.node
    assert original.goto_parent()
    assert copied.node == 2
