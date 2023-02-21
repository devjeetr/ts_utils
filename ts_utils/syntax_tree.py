import functools
import inspect
from typing import (
    Callable,
    Iterable,
    Iterator,
    MutableMapping,
    Optional,
    Protocol,
    Union,
    overload,
)

# import networkx as nx
from ts_utils.collections import NodeDict

# from ts_utils.core import sexp
from ts_utils.iter import (
    TraversalFilter,
    iternodes,
    iternodes_with_edges,
    iternodes_with_parent,
)
from ts_utils.parsing import parse
from tree_sitter import Node, Tree

from .util import all_true


def _default_get_node_attributes(node: Node):
    return {
        "child_count": node.child_count,
        "has_error": node.has_error,
        "is_missing": node.is_missing,
        "named": node.is_named,
        "type": node.type,
        "bytes": (
            node.start_byte,
            node.end_byte,
        ),
    }


class SyntaxTreeBase(Protocol):
    "Base interface for Syntax trees to be used with Mixins"
    source_bytes: bytes
    language: str
    traversal_filter: TraversalFilter
    source_encoding: str
    tree: Tree

    @property
    def nodes(self) -> Iterable[Node]:
        ...

    def node_id(self, node: Node) -> int:
        ...

    def node_text(self, node: Node) -> str:
        ...

    def __contains__(self, node: Node) -> bool:
        ...


class TraversalMixin:
    def iternodes(
        self: SyntaxTreeBase,
        node: Optional[Node] = None,
        traversal_filter: Optional[TraversalFilter] = None,
    ):
        """inorder traversal of the tree."""
        if node is None:
            node = self.tree.root_node

        return iternodes(
            node.walk(),
            traversal_filter=all_true(traversal_filter, self.traversal_filter),
        )

    def iter_with_parent(
        self: SyntaxTreeBase,
        node: Optional[Node] = None,
        parent_filter: Optional[TraversalFilter] = None,
        traversal_filter: Optional[TraversalFilter] = None,
    ):
        """inorder traversal of the tree, with parent pointers."""
        if node is None:
            node = self.tree.root_node

        return iternodes_with_parent(
            node.walk(),
            traversal_filter=all_true(traversal_filter, self.traversal_filter),
            parent_filter=parent_filter,
        )

    def iter_with_edges(self: SyntaxTreeBase, node: Optional[Node] = None, traversal_filter=None):
        """inorder traversal of the tree, with parent pointers and edge information."""
        if node is None:
            node = self.tree.root_node

        return iternodes_with_edges(
            node.walk(), all_true(traversal_filter, self.traversal_filter)
        )


# class NxGraphMixin:
#     """Mixin that provides utilities to convert syntax
#     trees into nx_graphs.
#     """

#     def to_nx_graph(
#         self: SyntaxTreeBase,
#         get_node_attrs: Callable[[Node], MutableMapping] = _default_get_node_attributes,
#     ) -> nx.DiGraph:
#         """Creates a networkx directed graph from the tree sitter tree.

#         Parameters
#         ----------
#         get_node_attrs : Callable[[Node], MutableMapping], optional
#             function that takes a node and returns node properties as a mapping, by default _default_get_node_attributes

#         Returns
#         -------
#         nx.DiGraph
#         """
#         g = nx.DiGraph()

#         for node, parent, edge_type in iternodes_with_edges(
#             self.tree.root_node.walk(), traversal_filter=self.traversal_filter
#         ):
#             g.add_node(
#                 self.node_id(node),
#                 **get_node_attrs(node),
#             )

#             if parent is not None:
#                 g.add_edge(
#                     self.node_id(parent),
#                     self.node_id(node),
#                     edge_type=edge_type or None,
#                 )

#         return g


def sexp(
    cursor,
    wrap: int = 50,
    node_to_str: Callable[[Node], str] = lambda node: node.type,
    traversal_filter: Optional[TraversalFilter] = None,
) -> str:
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

    def sexp_from_stream(iterator):
        node, parent, edge = next(iterator)

        # first, we collect all the s-exp representations
        # for each child. Because the iterator is assumed
        # to be performing in-order traversal, we can assume
        # that the next 'node.named_child_count' nodes will
        # be children of the current 'node'
        child_outputs = []
        for childnode in filter(traversal_filter, node.children):
            try:
                child_outputs.extend(sexp_from_stream(iterator))
            except StopIteration:
                raise ValueError(
                    "Iterator raised StopIteration. \n"
                    + "Make sure iterator yields an inorder traversal of the tree."
                )

        # add prefix label when current child is a field member
        # of another node
        field_prefix = f"{edge}: " if edge else ""
        # node's representation itself
        node_repr = f"({node_to_str(node)}"
        final_outputs = [
            field_prefix + node_repr
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

    traversal_filter = all_true(traversal_filter, lambda node: node.is_named)

    outputs = sexp_from_stream(
        iternodes_with_edges(cursor, traversal_filter=traversal_filter)
    )

    return "\n".join(outputs)


class SyntaxTree(TraversalMixin):
    def __init__(
        self,
        source: Union[str, bytes],
        language: str,
        encoding="utf-8",
        tree: Optional[Tree] = None,
        traversal_filters: Union[TraversalFilter, Iterable[TraversalFilter]] = (),
    ) -> None:
        """Creates a new syntax tree

        Parameters
        ----------
        source : str
            source string or bytes
        language : str
            language of the source code
        encoding : str, optional
            source code encoding, by default "utf-8"
        tree : Tree, optional
            Corresponding tree-sitter tree if already parsed.
        traversal_filters : Union[TraversalFilter, Iterable[TraversalFilter]], optional
            One or more predicates that determine which parts of the
            abstract syntax tree should be traversed, by default ()
        """
        self.source_bytes = (
            bytes(source, encoding) if isinstance(source, str) else source
        )
        self.tree = tree or parse(self.source_bytes, language)
        self.source_encoding = encoding
        self.language = language

        if isinstance(traversal_filters, Iterable):
            traversal_filters = all_true(*traversal_filters)
        self.traversal_filter = traversal_filters

        self._node_to_id = NodeDict(
            (node, i)
            for i, node in enumerate(
                iternodes(
                    self.tree.walk(),
                    self.traversal_filter,
                )
            )
        )

    def from_source(
        self,
        source: Union[str, bytes],
        language: str,
        encoding="utf-8",
        traversal_filters: Union[TraversalFilter, Iterable[TraversalFilter]] = (),
    ):
        ...

    @property
    def nodes(self) -> Iterator[Node]:
        """All the nodes contained in the syntax tree,
        ordered according to the inorder traversal
        of the tree
        """
        return self._node_to_id.keys()

    def node_id(self, node: Node) -> int:
        """Gets the integer id of a given node."""
        return self._node_to_id[node]

    @overload
    def node_text(self, node: Node) -> str:
        ...

    @overload
    def node_text(self, node: Iterable[Node]) -> tuple[str, ...]:
        ...

    def node_text(
        self, node: Union[Node, Iterable[Node]]
    ) -> Union[str, tuple[str, ...]]:
        """Gets the source text that a given node points to"""
        get_node_text = lambda node: self.source_bytes[
            node.start_byte : node.end_byte
        ].decode(self.source_encoding)
        if isinstance(node, Iterable):
            return tuple(map(get_node_text, node))

        return get_node_text(node)

    def __contains__(self, node: Node) -> bool:
        return node in self._node_to_id

    def sexp(self, node: Optional[Node] = None):
        if node is None:
            node = self.tree.root_node

        return sexp(
            node.walk(),  # type: ignore
            node_to_str=lambda node: f'{node.type} "{self.node_text(node)}"'
            if self.is_leaf(node)
            else node.type,
            traversal_filter=self.traversal_filter,
        )

    def __repr__(self):
        return self.sexp()

    def is_leaf(self, node):
        for child in node.children:
            if child in self._node_to_id:
                return False

        return True

    @functools.cached_property
    def leaves(self):
        """Gets all leaves within the tree"""

        return tuple(filter(self.is_leaf, self._node_to_id))

    def children(self, node: Node):
        if node not in self._node_to_id:
            raise ValueError(f"Given node {node} does not exist in this tree.")

        return filter(self.traversal_filter, node.children)

    def __setattr__(self, *args):
        if inspect.stack()[1][3] == "__init__":
            object.__setattr__(self, *args)
        else:
            raise TypeError("Syntax Trees are immutable.")

    def find_all(
        self, filter_fn: TraversalFilter, node: Optional[Node] = None
    ) -> Iterator[Node]:
        if node is None:
            node = self.tree.root_node
        return filter(filter_fn, self.iternodes(node))

    def find(
        self, filter_fn: TraversalFilter, node: Optional[Node] = None
    ) -> Optional[Node]:
        results = tuple(self.find_all(filter_fn, node))
        if len(results) > 1:
            raise ValueError("More than one node")

        return results[0] if results else None
