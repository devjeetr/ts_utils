# ts_utils (Experimental)

`ts_utils` provides a lightweight set of utilities to make working with `tree_sitter` more pythonic. It is aimed at users wanting to perform
read-only analysis of programs using `tree-sitter`.

**Warning**: ts_utils is currently unstable and under active development, with parts of the API likely to change.

## Getting Started

### Installation

`ts_utils` can be installed directly from GitHub via:
```
pip install git+https://github.com/devjeetr/ts_utils
```

## Usage

### Parsing and language grammar management

`ts_utils.parsing` provides utilities that automate management of language libraries to ease parsing of source code.

```python
from ts_utils import parse, sexp

source = """
    def main():
        print("Hello, World!")
"""
# automatically downloads, caches and builds
# language library for 'python'
tree = parse(source, "python")
# You can also provide your own
# language library
tree = parse(source, language_library)
```

### Investigating `node_types` of a language grammar

You can investigate [node_types](https://tree-sitter.github.io/tree-sitter/using-parsers#static-node-types) of a language as follows:

```python
from ts_utils import get_node_types, get_supernode_mappings

node_types = get_node_types('python') # loads 'node_types.json' if
                                      # provided by language grammar.

```

### Working with `tree_sitter` trees

#### High Level Iterators
`ts_utils.iter` provides `itertool` style utilities to iterate over
nodes in a tree. Behind the scenes, `ts_utils.iter` uses efficient `TreeCursor` operations
resulting in as close to bare-bones performance as possible.
```python
from ts_utils.iter import iternodes, iternodes_with_parent

tree = parse(...)

for node in iternodes(tree.walk()):
    ...
```

All functions in `ts_utils.iter` take an optional argument `traversal_filter`, which allows you to filter out nodes from the
traversal. If a `traversal_filter(node) == False`, the entire subtree
rooted at `node` is skipped.

```python
only_named_nodes = lambda node: node.is_named
tree = parse(...)

for node in iternodes(tree, only_named_nodes):
    # skips over any node that is not named
    ...
```

Since `ts_utils.iter` provides pure functions to transform `TreeCursors` into iterators, their outputs can be arbitrarily composed with `map`, `compose`, `reduce` and `itertools.*`. This composition allows you to create 

```python
node_iter = iternodes(tree.walk())
def find(node_types: Set[str], tree: Tree):
    "Finds all nodes that are of a type specified in node_types"
    return filter(lambda node: node.type in node_types, iternodes(tree.walk()))
```

#### Low Level Iterators
If you want to implement your own tree traversals, use `traversals.walk_tree`. `walk_tree`
traverses the tree using the `TreeCursor` API in the minimum number of moves. Unlike traditional
traversals, `walk_tree` visits each node twice - when the node is first reached, and after the
processing of all it's children. For example, consider the following tree structure:
```python
from ts_utils.cursor_utils import tuple_cursor
from ts_utils.traversals import walk_tree
tree = (1, 
        (2, 3),
        (4, 5))

list(walk_tree(tree))
```
This will yield nodes in the following order:
``` python
[(1, 'DOWN'), # Start the traversal by descending into the root
 (2, 'DOWN'),
 (3, 'DOWN'), # Each node is visited twice. If a node is a leaf,
 (3, 'UP'),   # it will be yielded twice.
 (2, 'UP'),
 (4, 'RIGHT'),
 (5, 'DOWN'),
 (5, 'UP'),
 (4, 'UP'),
 (1, 'UP')]   # End traversal by moving up beyond tree root
```

Using the move information can allow you to hook into enter and exit lifecycles for
nodes to implement higher level traversal operations. For example:
```python
def filter_moves(valid_moves, cursor):
    return filter(
        lambda cursor, move: move in valid_moves, 
        walk_tree(cursor))

preorder = filter_moves((Moves.DOWN, Moves.RIGHT))
postorder = filter_moves((Moves.UP))
```