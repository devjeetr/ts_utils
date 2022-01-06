import pytest
from ts_utils.collections import NodeDict
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

