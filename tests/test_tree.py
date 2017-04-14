import io
import itertools
import mmap
import os

import pytest

from bplustree.const import ENDIAN, TreeConf
from bplustree.node import Node, RootNode
from bplustree.tree import BPlusTree


def test_create_in_memory():
    b = BPlusTree()
    assert isinstance(b._mm, mmap.mmap)
    b.close()


def test_create_and_load_file():
    filename = '/tmp/testfile.db'

    if os.path.isfile(filename):
        os.unlink(filename)

    b = BPlusTree(filename=filename)
    assert isinstance(b._mm, io.FileIO)
    b.insert(5, b'foo')
    b.close()

    b = BPlusTree(filename=filename)
    assert isinstance(b._mm, io.FileIO)
    assert b.get(5) == b'foo'
    b.close()


def test_write_read_page():
    b = BPlusTree()
    expected = b'abcdefgh' * int(4096 / 8)
    b._write_page(1, expected)
    assert b._read_page(1) == expected
    b.close()


def test_initial_values():
    b = BPlusTree(page_size=512, value_size=128)
    assert b._tree_conf.page_size == 512
    assert b._tree_conf.order == 4
    assert b._tree_conf.key_size == 16
    assert b._tree_conf.value_size == 128
    b.close()


def test_partial_constructors():
    b = BPlusTree()
    node = b.RootNode()
    record = b.Record()
    assert node._tree_conf == b._tree_conf
    assert record._tree_conf == b._tree_conf
    b.close()


def test_insert_get_record_in_tree():
    b = BPlusTree()
    b.insert(1, b'foo')
    assert b.get(1) == b'foo'
    b.close()

iterators = [
    range(0, 1000, 1),
    range(1000, 0, -1),
    list(range(0, 1000, 2)) + list(range(1, 1000, 2))
]
orders = [3, 4, 50]
page_sizes = [4096, 8192]
key_sizes = [4, 16]
values_sizes = [4, 16]
file_names = [None, '/tmp/testfile.index']
matrix = itertools.product(iterators, orders, page_sizes,
                           key_sizes, values_sizes, file_names)


@pytest.mark.parametrize('iterator,order,page_size,k_size,v_size,filename',
                         matrix)
def test_insert_split_in_tree(iterator, order, page_size, k_size, v_size,
                              filename):
    inserted = set()

    if filename and os.path.isfile(filename):
        os.unlink(filename)

    b = BPlusTree(filename=filename, order=order, page_size=page_size,
                  key_size=k_size, value_size=v_size)

    for i in iterator:
        b.insert(i, str(i).encode())
        inserted.add(i)

    if filename:
        # Reload tree from file before checking values
        b.close()
        b = BPlusTree(filename=filename, order=order, page_size=page_size,
                      key_size=k_size, value_size=v_size)

    for x in inserted:
        assert b.get(x) == str(x).encode()

    b.close()


def test_get_node_from_page_data():
    data = (2).to_bytes(1, ENDIAN) + bytes(4096 - 1)
    tree_conf = TreeConf(4096, 7, 16, 16)
    assert isinstance(
        Node.from_page_data(tree_conf, data, 4),
        RootNode
    )
