import pytest
from ts_utils.collections import NodeCollection, NodeDict
from ts_utils.iter import iternodes
from ts_utils.parsing import parse

sample_source = """
def node_text(source, node, encoding='utf-8') -> str:
    source_bytes = bytearray(source, encoding)

    return source_bytes[node.start_byte:node.end_byte].decode(encoding)
"""


def test_node_dict_basic_dict_operations():
    tree = parse(sample_source, 'python')
    node_dict = NodeDict()

    node_dict[tree.root_node] = 'root'

    assert tree.root_node in node_dict

    with pytest.raises(KeyError):
        node_dict[tree.root_node.children[0]]

    assert len(node_dict) == 1

    node_dict[tree.root_node] = 'new_root'
    assert len(node_dict) == 1

    assert node_dict[tree.root_node] == 'new_root'
    del node_dict[tree.root_node]
    assert len(node_dict) == 0

    with pytest.raises(KeyError):
        node_dict[tree.root_node]


def test_node_collection_basic_dict_operations():
    tree = parse(sample_source, 'python')
    node_collection = NodeCollection(iternodes(tree.walk()))

    for node_id, node in enumerate(iternodes(tree.walk())):
        assert node_collection[node] == node_id

    node_list = list(iternodes(tree.walk()))
    assert len(node_collection) == len(node_list)

    node_collection.remove(tree.root_node)
    assert len(node_collection) == len(node_list[1:])
    for i, (node_id, node) in enumerate(node_collection):
        assert node_id == i + 1
        assert node == node_list[i + 1]
