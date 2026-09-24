from app.material.materialgroup_mixie import split_nodes_into_columns


def test_split_nodes_into_three_columns_evenly():
    nodes = [f"node-{i}" for i in range(8)]

    result = split_nodes_into_columns(nodes, 3)

    assert result == [
        ["node-0", "node-1", "node-2"],
        ["node-3", "node-4", "node-5"],
        ["node-6", "node-7"],
    ]


def test_split_nodes_into_three_columns_handles_empty_input():
    assert split_nodes_into_columns([], 3) == [[], [], []]
