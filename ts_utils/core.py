from typing import Callable, Optional

from tree_sitter import Node, TreeCursor, Tree
from typing import Union
from ts_utils.iter import TraversalFilter, iternodes_with_edges

__all__ = ["sexp", "TreeLike"]


TreeLike = Union[TreeCursor, Node, Tree]
"""A type that can be converted to a TreeCursor."""

def tree_like_to_cursor(tree_like: TreeLike) -> TreeCursor:
    if isinstance(tree_like, TreeCursor):
        return tree_like
    return tree_like.walk() 

def sexp(tree: TreeLike,
         wrap: int = 50,
         node_to_str: Callable[[Node], str] = lambda node: node.type,
         traversal_filter: Optional[TraversalFilter] = None) -> str:
    """Pretty-formatted s-expr representation ofthe tree rooted at the given cursor. 

    Examples:
        
        Basic usage:

            >>> source = \"\"\"for i in range(20):
                                print(i)\"\"\"
            >>> tree = parse(source, "python")
            >>> print(sexp(tree))
            (module
                (for_statement
                left: (identifier)
                right: (call
                        function: (identifier)
                        arguments: (argument_list (integer)))
                body: (block
                        (expression_statement
                        (call
                        function: (identifier)
                        arguments: (argument_list (identifier)))))))
            
            
        Customizing output using `node_to_str`:
            
            # Same tree as above
            >>> def custom_node_repr(node):
                    if node.type == "identifier":
                        return f"{node.type} '{node.text.decode()}'"
                    return node.type
            >>> print(sexp(tree))
            (module
                (for_statement
                left: (identifier 'i')
                right: (call
                        function: (identifier 'range')
                        arguments: (argument_list (integer)))
                body: (block
                        (expression_statement
                        (call
                        function: (identifier 'print')
                        arguments: (argument_list (identifier 'i')))))))
        
    Args:
        tree: tree cursor to print
        wrap: line length after which content is wrapped to the next line. Defaults to 50.
        node_to_str: a function that converts a node into a string representation. Defaults to lambda node:node.type.
        traversal_filter: a predicate that decides if a node should be included in the sexp. Defaults to None.

    Returns:
        sexp string representation of tree rooted at cursor.
    """
    cursor = tree_like_to_cursor(tree) 
    def named_node_w_edges(cursor):
        for node, parent, edge in iternodes_with_edges(cursor, traversal_filter=traversal_filter):
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
