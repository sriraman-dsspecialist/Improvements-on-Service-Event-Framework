import pandas as pd

from app.events.event_clustering import filter_cluster_pairs, read_event_clustering_pairs


def test_read_event_clustering_pairs_rounds_similarity_to_one_decimal(tmp_path, monkeypatch):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    workbook = output_dir / "service_event_inconsistencies.xlsx"

    df = pd.DataFrame(
        {
            "event1": ["A", "B"],
            "event2": ["C", "D"],
            "similarity": [0.94, 0.65],
        }
    )
    with pd.ExcelWriter(workbook) as writer:
        df.to_excel(writer, sheet_name="Event Clustering", index=False)

    monkeypatch.setattr(
        "app.events.event_clustering.config.locations.outputs",
        str(output_dir),
    )

    loaded = read_event_clustering_pairs()
    assert loaded["similarity"].tolist() == [0.9, 0.6]


def test_filter_cluster_pairs_uses_selected_threshold():
    df = pd.DataFrame(
        {
            "event1": ["A", "B", "C"],
            "event2": ["C", "D", "E"],
            "similarity": [0.9, 0.7, 0.6],
        }
    )

    filtered = filter_cluster_pairs(df, 0.7)
    assert filtered["similarity"].tolist() == [0.9, 0.7]
    assert filtered["event1"].tolist() == ["A", "B"]
