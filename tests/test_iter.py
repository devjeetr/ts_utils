from ts_utils.iter import iternodes, iternodes_with_parent, iternodes_with_edges
from ts_utils.cursor_utils import tuple_cursor, Cursor
import ts_utils
import inspect


def hello_world(name):
    print(f"hello, {name}")


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


def test_iternodes_with_parent():
    tree = ts_utils.parse(inspect.getsource(hello_world), "python")

    expected = [
        ("module", None),
        ("function_definition", None),
        ("def", None),
        ("identifier", "name"),
        ("parameters", "parameters"),
        ("(", None),
        ("identifier", None),
        (")", None),
        (":", None),
        ("block", "body"),
        ("expression_statement", None),
        ("call", None),
        ("identifier", "function"),
        ("argument_list", "arguments"),
        ("(", None),
        ("string", None),
        ("string_start", None),
        ("string_content", None),
        ("interpolation", None),
        ("{", None),
        ("identifier", "expression"),
        ("}", None),
        ("string_end", None),
        (")", None),
    ]
    walk_results = [
        (node.type, edge) for node, _, edge in iternodes_with_edges(tree.walk())
    ]
    assert walk_results == expected
