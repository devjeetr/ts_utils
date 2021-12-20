"""Contains utilities to convert tree_sitter
trees into scipy sparse matrices. 
"""
from typing import Tuple

from scipy.sparse import coo_matrix
from tree_sitter import Node, TreeCursor

from ts_utils.core import hash_node
from ts_utils.iter import (TraversalFilter, default_traversal_filter,
                           iternodes, iternodes_with_parent)

NodesById = dict[int, Tuple[int, Node]]

__all__ = ["parent_mask", "next_sibling_mask", "prev_sibling_mask"]


def parent_mask(cursor: TreeCursor,
                nodes: NodesById = None,
                traversal_filter: TraversalFilter = default_traversal_filter):
    """Returns a sparse boolean matrix representing an adjacency
    matrix of the tree rooted at cursor
    """
    if not nodes:
        nodes = {
            hash_node(node): (i, node)
            for i, node in enumerate(
                iternodes(cursor, traversal_filter=traversal_filter))
        }

    data = []
    rows = []
    cols = []

    for node, parent in iternodes_with_parent(
            cursor, traversal_filter=traversal_filter):
        if parent:
            parent_id = nodes[hash_node(parent)][0]
            node_id = nodes[hash_node(node)][0]

            data.append(1)
            rows.append(parent_id)
            cols.append(node_id)

    return coo_matrix((data, (rows, cols)),
                      dtype=bool,
                      shape=(len(nodes), len(nodes)))


def next_sibling_mask(
        cursor,
        nodes=None,
        traversal_filter: TraversalFilter = default_traversal_filter):
    if not nodes:
        nodes = {
            hash_node(node): (i, node)
            for i, node in enumerate(
                iternodes(cursor, traversal_filter=traversal_filter))
        }

    data = []
    rows = []
    cols = []

    for node in iternodes(cursor, traversal_filter=traversal_filter):
        curr = node
        node_id = nodes[hash_node(node)][0]
        while curr := curr.next_sibling:
            sibling_id = nodes[hash_node(node)][0]
            data.append(1)
            rows.append(node_id)
            cols.append(sibling_id)

    return coo_matrix((data, (rows, cols)),
                      dtype=bool,
                      shape=(len(nodes), len(nodes)))


def prev_sibling_mask(
        cursor,
        nodes=None,
        traversal_filter: TraversalFilter = default_traversal_filter):
    if not nodes:
        nodes = {
            hash_node(node): (i, node)
            for i, node in enumerate(
                iternodes(cursor, traversal_filter=traversal_filter))
        }

    data = []
    rows = []
    cols = []

    for node in iternodes(cursor, traversal_filter=traversal_filter):
        curr = node
        node_id = nodes[hash_node(node)][0]
        while curr := curr.prev_sibling:
            sibling_id = nodes[hash_node(node)][0]
            data.append(1)
            rows.append(node_id)
            cols.append(sibling_id)

    return coo_matrix((data, (rows, cols)),
                      dtype=bool,
                      shape=(len(nodes), len(nodes)))


sparse_adjacency_matrix = parent_mask
