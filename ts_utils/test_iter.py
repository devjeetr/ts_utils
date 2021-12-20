from .iter import traverse, traverse_with_edges
from .parsing import parse


def test_traversal_fn():

    source = """
        x = 22
    """

    tree = parse(source, "python")

    nodes = traverse(
        tree.walk(), traversal_filter=lambda node: node.type != "assignment"
    )

    node_types = list(map(lambda n: n.type, nodes))

    assert node_types == ["module", "expression_statement"]


def test_traversal_filter():

    source = """
        def test_traversal_fn():
            source = ""

            tree = parse(source, "python")

            nodes = traverse(
                tree.walk(), traversal_filter=lambda node: node.type != "assignment"
            )

            node_types = list(map(lambda n: n.type, nodes))

            assert node_types == ["module", "expression_statement"]
    """
    traversal_filter = lambda node: node.type != "assignment"
    tree = parse(source, "python")

    nodes_a = [
        node for node in traverse(tree.walk(), traversal_filter=traversal_filter)
    ]
    nodes_b = [
        node
        for _, node, _ in traverse_with_edges(
            tree.walk(), traversal_filter=traversal_filter
        )
    ]

    assert nodes_a == nodes_b

    traversal_filter = lambda _: True
    tree = parse(source, "python")

    nodes_a = [
        node for node in traverse(tree.walk(), traversal_filter=traversal_filter)
    ]
    nodes_b = [
        node
        for _, node, _ in traverse_with_edges(
            tree.walk(), traversal_filter=traversal_filter
        )
    ]

    assert nodes_a == nodes_b
