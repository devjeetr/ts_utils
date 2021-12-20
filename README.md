## ts_utils (Experimental)

`ts_utils` provides a lightweight set of utilities to make working with `tree_sitter` more pythonic. It is aimed at users wanting to perform
read-only analysis of programs using `tree-sitter`.

**Warning**: ts_utils is currently unstable and under active development, with parts of the API likely to change.

### Parsing source into a tree

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

`ts_utils.iter` provides `itertool` style utilities to iterate over
nodes in a tree. Behind the scenes, `ts_utils.iter` uses efficient `TreeCursor` operations
resulting in as close to bare-bones performance as possible.

```python
from ts_utils.iter import iternodes, iternodes_with_parent

tree = parse(...)

for node in iternodes(tree.walk()):
    ...
```

All functions in `ts_utils.iter` take an optional argument `traversal_fitler`, which allows you to filter out nodes from the
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

The traversal order of all functions in `ts_utils.iter` is deterministic
for a given tree and `traversal_filter`, meaning that regardless of which function you use, nodes will be yielded in the same order. This allows you to simply wrap an iterator with `enumerate` to assign each node a unique id that will be consistent across multiple traversals/iterations.

```python
only_named_nodes = lambda node: node.is_named
a = list(iternodes(tree.walk(), only_named_nodes))
b = list(node for node,parent in iternodes_with_parent(tree.walk(), only_named_nodes))

assert a == b # OK
```

### Hashing nodes

`ts_utils.hash_node` can hash `tree_sitter` nodes, which by default, are not hashable.

Note: `ts_utils.hash_node` only works with nodes that do not contain errors (`node.has_errors == False`).

### Converting trees to sparse adjacency matrices

`ts_utils.matrix` provides utilities to convert trees to sparse adjacency matrices.

```python
matrix = ts_utils.matrix.parent_mask(...)
child_mask = matrix.transpose()

next_sibling_mask = ts_utils.matrix.next_sibling_mask(...)
prev_sibling_mask = ts_utils.matrix.prev_sibling_mask(...)

all_edges = parent_mask * child_mask * next_sibling_mask * prev_sibling_mask
```
