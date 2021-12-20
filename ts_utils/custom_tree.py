from collections import defaultdict
from dataclasses import dataclass, field
from typing import (Callable, Dict, Generator, Iterable, List, Optional,
                    Sequence, Tuple, Union, overload)

Position = Tuple[int, int]

Sentinel = object()


@dataclass
class SyntaxNode:
    id: int
    named: bool
    type: str
    source: str
    span: Tuple[int, int]
    range: Tuple[Position, Position]
    fields: Dict[str, List["SyntaxNode"]] = field(default_factory=dict)
    parent: Optional["SyntaxNode"] = None
    children: Sequence["SyntaxNode"] = field(default_factory=list)
    parent_field: Optional[str] = None
    n_descendants: int = 0

    @property
    def text(self):
        start, end = self.span
        return self.source[start:end]

    def __iter__(self):
        return preorder_traversal(self)

    def inorder(self):
        return inorder_traversal(self)

    def descendants(self) -> Generator["SyntaxNode", None, None]:
        for node in self.children:
            yield node
            for descendant in node.descendants():
                yield descendant

    def sexp(
        self, wrap: int = 50, node_to_str: Callable[["SyntaxNode"], str] = lambda node: node.type
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
        return _sexp(self, wrap=wrap, node_to_str=node_to_str)

    @overload
    def __getitem__(self, field_name_or_child_index: str) -> List["SyntaxNode"]:
        ...

    @overload
    def __getitem__(self, field_name_or_child_index: int) -> "SyntaxNode":
        ...

    def __getitem__(
        self,
        field_name_or_child_index: Union[str,
                                         int]) -> Union["SyntaxNode", List["SyntaxNode"]]:
        if isinstance(field_name_or_child_index, str):
            assert (
                field_name_or_child_index in self.fields
            ), f"Field name {field_name_or_child_index} does not exist in node of type {self.type}"
            return self.fields[field_name_or_child_index]
        elif isinstance(field_name_or_child_index, int):
            assert field_name_or_child_index < len(
                self.children
            ), f"Node has only {len(self.children)} children, index {field_name_or_child_index} is out of bounds."
            return self.children[field_name_or_child_index]

        raise ValueError('Only string or integer indices are supported')
        
    def __repr__(self) -> str:
        outputs = []
        outputs.append(self.type)
        code_indent = " "

        ((start_line, _), (end_line, _)) = self.range
        width = max(len(str(start_line)), len(str(end_line)))

        outputs.extend([
            f"{code_indent}{str(start_line + i).rjust(width)}|  {line}"
            for i, line in enumerate(self.text.split("\n"))
        ])

        return "\n".join(outputs)

    @staticmethod
    def from_ts(cursor, source, named_only=True):
        return _build_tree(cursor, source, named_only=named_only)


def _build_tree(cursor, source: str, named_only=True) -> SyntaxNode:
    def _build_tree_inner(cursor, i=0, parent=None):

        if named_only and not cursor.node.is_named:
            return None, i

        field_name = cursor.current_field_name()
        node = cursor.node

        n_descendants = 0
        constructed_node = SyntaxNode(id=i,
                                source=source,
                                type=node.type,
                                span=(node.start_byte, node.end_byte),
                                range=(node.start_point, node.end_point),
                                parent=parent,
                                parent_field=field_name,
                                named=node.is_named,
                                n_descendants=n_descendants)


        i += 1
        original_i = i
        children = []
        if cursor.goto_first_child():
            child, i = _build_tree_inner(cursor, i, parent=constructed_node)
            if child:
                children.append(child)

                child_field = cursor.current_field_name()
                if child_field is not None:
                    if child_field not in constructed_node.fields:
                        constructed_node.fields[child_field] = [child]
                    else:
                        constructed_node.fields[child_field].append(child)
            while cursor.goto_next_sibling():
                child, i = _build_tree_inner(cursor,
                                             i,
                                             parent=constructed_node)

                if child:
                    children.append(child)

                    child_field = cursor.current_field_name()
                    if child_field not in constructed_node.fields:
                        constructed_node.fields[child_field] = [child]
                    else:
                        constructed_node.fields[child_field].append(child)

            # restore cursor position
            cursor.goto_parent()
        constructed_node.children = tuple(children)
        constructed_node.n_descendants = i - original_i
        return constructed_node, i

    root_node, _ = _build_tree_inner(cursor)

    assert root_node is not None

    return root_node


def inorder_traversal(root: SyntaxNode) -> Generator[SyntaxNode, None, None]:
    if not root:
        return

    if not root.children:
        yield root
        return

    for child in root.children[:-1]:
        yield from inorder_traversal(child)

    yield root

    yield from inorder_traversal(root.children[-1])

def preorder_traversal(root: SyntaxNode) -> Generator[SyntaxNode, None, None]:
    if not root:
        return

    yield root
    
    if not root.children:
        return

    for child in root.children[:-1]:
        yield from preorder_traversal(child)


    yield from preorder_traversal(root.children[-1])


def build_adjacency_dict(root: SyntaxNode) -> Dict[int, List[int]]:
    adj_dict: defaultdict[int, List[int]] = defaultdict(list)

    for node in root:
        for child in node.children:
            adj_dict[node.id].append(child.id)
            adj_dict[child.id].append(node.id)

    return adj_dict

def _sexp(
    node: SyntaxNode, wrap: int = 50, node_to_str: Callable[[SyntaxNode], str] = lambda node: node.type
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
    def sexp_from_stream(node):
        # first, we collect all the s-exp representations
        # for each child. Because the iterator is assumed
        # to be performing in-order traversal, we can assume
        # that the next 'node.named_child_count' nodes will
        # be children of the current 'node'
        child_outputs = []
        for child in node.children:
            try:
                child_outputs.extend(sexp_from_stream(child))
            except StopIteration:
                raise ValueError(
                    "Iterator raised StopIteration. \n"
                    + "Make sure iterator yields an inorder traversal of the tree."
                )

        # add prefix label when current child is a field member
        # of another node
        field_prefix = f"{node.parent_field}: " if node.parent_field else ""
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
        indentation = "" if node.parent is None else " "
        return [indentation + output for output in final_outputs]

    outputs = sexp_from_stream(node)

    return "\n".join(outputs)
