
## `walk_tree`
### Traversals
Common traversal patterns like preorder and postorder traversals are
trivial to implement.

```python
def filter_moves(valid_moves, cursor):
    return filter(
        lambda cursor, move: move in valid_moves, 
        walk_tree(cursor))

preorder = filter_moves((Moves.DOWN, Moves.RIGHT))
postorder = filter_moves((Moves.UP))
```

### Maintaining per-node context
This example shows how you can maintain a stack to provide
each node it's own context based on it's parent structure. Specifically,
we maintain a stack of the current node's parent. 
```python
from ts_utils import parse
from ts_utils import traversals

tree = ts_utils.parse("x = 22\nfor i in range(10): pass", "python")
RootContext = object()
parent_stack = [RootContext]
cursor = tree.walk()

for cursor, move in traversals.walk_tree(cursor):
    match move:
        case (Moves.DOWN | Moves.RIGHT):
            context = parent_stack[-1]
            # perform operations on current node using 
            # in this node's context
            ...
            # Update stack before next iteration
            parent_stack.append(cursor.node)
        case Moves.UP:
            if parent_stack[-1] != RootContext and cursor.node.id == parent_stack[-1].id:
                parent_stack.pop()
```
### tree-sitter tree to nx-graph
This recipe shows how the flexibility of `walk_tree` can be used to convert
a `tree-sitter` tree into an `networkx.DiGraph`.

```python
import networkx as nx
from ts_utils import parse
from ts_utils import traversals
nx_tree = nx.DiGraph()
tree = ts_utils.parse("x = 22\nfor i in range(10): pass", "python")

parent_stack = []
cursor = tree.walk()
for cursor, move in traversals.walk_tree(cursor):
    match move:
        case (Moves.DOWN | Moves.RIGHT):
            nx_tree.add_node(cursor.node.id, nodetype=cursor.node.type)
            parent_stack.append(cursor.node)
        case Moves.UP:
            if cursor.node.id == parent_stack[-1].id:
                parent_stack.pop()
            if parent_stack:
                nx_tree.add_edge(parent_stack[-1].id, cursor.node.id) 
```