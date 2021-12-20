from typing import Callable

from tree_sitter import Node

from .iter import iternodes_with_edges

__all__ = ["hash_node", "node_text", "sexp"]


def hash_node(node: Node) -> int:
    """Deterministically hashes a tree_sitter Node. Uses
    the node's start_byte, end_byte, type and node type to
    generate a string hash. 

    Warning: this function only works with nodes that do not
    have errors. If a node has errors, the returned hash is
    not guaranteed to be unique.

    Parameters
    ----------
    node : Node
        tree_sitter node

    Returns
    -------
    str
        hash of the node
    """
    # parent = node.parent
    # parent_type = parent.type if parent else None
    # return hash(f"{node.start_byte}#{node.end_byte}#{node.type}")

    return hash((node.start_byte, node.end_byte, node.type))


def node_text(source: str, node: Node) -> str:
    return source[node.start_byte:node.end_byte]


def sexp(cursor,
         wrap: int = 50,
         node_to_str: Callable[[Node], str] = lambda node: node.type) -> str:
    """Pretty-formatted s-expr representation of
    the tree rooted at the given cursor. Similar to
    Node.sexp() but formatted differently.

    Parameters
    ----------
    cursor : TreeCursor
        tree cursor to print
    wrap : int, optional
        if a nodes representation is longer than this number it is printed
        across multiple lines, by default 50
    node_to_str : Callable[[Node], str], optional
        a function that converts a node into a string representation, by default lambdanode:node.type

    Returns
    -------
    str
        s-expr string
    """
    def named_node_w_edges(cursor):
        for node, parent, edge in iternodes_with_edges(cursor):
            if node.is_named:
                yield node, parent, edge

    def sexp_from_stream(iterator):
        node, parent, edge = next(iterator)

        # first, we collect all the s-exp representations
        # for each child. Because the iterator is assumed
        # to be performing in-order traversal, we can assume
        # that the next 'node.named_child_count' nodes will
        # be children of the current 'node'
        child_outputs = []
        for _ in range(node.named_child_count):
            try:
                child_outputs.extend(sexp_from_stream(iterator))
            except StopIteration:
                raise ValueError(
                    "Iterator raised StopIteration. \n" +
                    "Make sure iterator yields an inorder traversal of the tree."
                )

        # add prefix label when current child is a field member
        # of another node
        field_prefix = f"{edge}: " if edge else ""
        # node's representation itself
        node_repr = f"({node_to_str(node)}"
        final_outputs = [field_prefix + node_repr
                         ]  # either "field: (identifier" . or "(identifier"

        if sum(map(len, child_outputs)) < wrap:
            # if the total length of this node's
            # children representation < wrap,
            # dont' split output into multiple lines.
            child_outputs = " ".join(child_outputs)
            final_outputs = [final_outputs[0] + child_outputs]
        else:
            # If we are splitting onto multiple lines
            # we need to add indentation.
            indentation = " " * len(field_prefix)
            final_outputs += [indentation + output for output in child_outputs]

        # close parenthesis
        final_outputs[-1] += ")"

        # handle special case when we are dealing
        # with the root node
        indentation = "" if parent is None else " "
        return [indentation + output for output in final_outputs]

    outputs = sexp_from_stream(named_node_w_edges(cursor))

    return "\n".join(outputs)
