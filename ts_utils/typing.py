from typing import Optional, Protocol, Sequence, Tuple


class Tree(Protocol):
    def edit(self, start_byte: int, old_end_byte: int, new_end_byte: int, start_point: Tuple[int, int], old_end_point: Tuple[int, int], new_end_point: Tuple[int, int]):
        ...

    def walk(self) -> "TreeCursor":
        ...
    
    @property
    def root_node(self) -> "Node":
        ...


class Node(Protocol):
    def child_by_field_id(self, id: int) -> Optional["Node"]:
        ...
    
    def child_by_field_name(self, name: str) -> Optional["Node"]:
        ...
    
    def walk(self) -> "TreeCursor":
        ...
    
    def sexp(self) -> str:
        ...
    
    @property
    def children(self) -> Sequence['Node']:
        ...

    @property
    def child_count(self) -> int:
        ...
    
    @property
    def named_child_count(self) -> int:
        ...
    
    @property
    def parent(self) -> Optional["Node"
    ]:
        ...

    @property
    def end_byte(self) -> int:
        ...
    
    @property
    def start_byte(self) -> int:
        ...
    
    @property
    def start_point(self) -> Tuple[int, int]:
        ...
    
    @property
    def end_point(self)-> Tuple[int, int]:
        ...
    
    @property
    def has_changes(self )-> bool:
        ...
        
    @property
    def has_error(self) -> bool:
        ...

    @property
    def is_missing(self) -> bool:
        ...
    
    @property
    def is_named(self) -> bool:
        ...
    
    @property
    def next_sibling(self) -> "Node":
        ...
    
    @property
    def next_named_sibling(self) -> "Node":
        ...

    @property
    def type(self) -> str:
        ...

class TreeCursor(Protocol):
    def current_field_name(self) -> Optional[str]:
        ...
    
    def goto_first_child(self) -> bool:
        ...
    
    def goto_next_sibling(self) -> bool:
        ...
    
    def goto_parent(self) -> bool:
        ...

    @property
    def node(self) -> Node:
        ...
