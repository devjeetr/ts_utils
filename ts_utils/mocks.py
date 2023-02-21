from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from tree_sitter import Node as INode
from tree_sitter import Tree as ITree
from tree_sitter import TreeCursor as ICursor


class Node:
    children: Sequence['Node']  
    is_named: bool
    type: str
    next_sibling: "Node"
    next_named_sibling: "Node"
    has_error: bool
    is_missing: bool
    has_changes: bool
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    start_byte: int
    end_byte: int
    parent: Optional["Node"]
    fields: dict[str, "Node"]
    children_by_field_ids: dict[int, "Node"]

    def child_by_field_id(self, id: int) -> Optional["Node"]:
        return self.children_by_field_ids.get(id, None)
    
    def child_by_field_name(self, name: str) -> Optional["Node"]:
        return self.fields.get(name, None)

    @property
    def child_count(self) -> int:
        return len(self.children)

    @property
    def named_child_count(self) -> int:
        return len(self.children)  
    
    def sexp(self):
        return repr(self)
    
    def walk(self) -> "TreeCursor":
        return TreeCursor(self)

class TreeCursor:
    def __init__(self, root: "Node"):
        self.root = root
        self.curr_node = root
        self.curr_field_name = None

    def current_field_name(self) -> Optional[str]:
        return self.curr_field_name
    
    def goto_first_child(self) -> bool:
        if self.curr_node.child_count == 0:
            return False
        
        self.curr_node = self.curr_node.children[0]

        return True
    
    def goto_next_sibling(self) -> bool:
        if self.curr_node.next_sibling is None:
            return False
        
        self.curr_node = self.curr_node.next_sibling
        return True

    
    def goto_parent(self) -> bool:
        if self.curr_node == self.root or self.curr_node.parent is None:
            return False

        self.curr_node = self.curr_node.parent

        return True

    @property
    def node(self) -> Node:
        return self.curr_node
