from typing import Callable

from tree_sitter import Node

Predicate = Callable[[Node], bool]


def of_type(*node_types: str) -> Predicate:
    return lambda node: node.type in node_types


def named_only(node: Node) -> bool:
    return node.is_named


def is_leaf(node: Node) -> bool:
    return node.child_count == 0
