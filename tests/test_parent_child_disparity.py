import pandas as pd

from app.material.parent_child_disparity import (
    build_material_badges,
    get_child_count_options,
    get_serviceevent_options_for_child_count,
    load_event_material_group_summary,
    load_event_parent_child_rows,
)


def test_parent_child_filters_and_detail_rows(tmp_path):
    xlsx_path = tmp_path / "disparity_parent_child_analysis.xlsx"
    summary_df = pd.DataFrame(
        {
            "Serviceeventcode_parent": [
                "BladeBearingReplace",
                "HydPumpReplace",
                "BladeBearingReplace",
                "GenBearReplace",
            ],
            "child_count": [2, 3, 2, 4],
        }
    )
    detail_df = pd.DataFrame(
        {
            "Serviceeventcode_parent": [
                "BladeBearingReplace",
                "BladeBearingReplace",
                "HydPumpReplace",
                "GenBearReplace",
            ],
            "Itemnumber_parent": [1, 2, 3, 4],
            "MaterialName_parent": ["Parent A", "Parent B", "Parent C", "Parent D"],
            "parent_material": [10, 20, 30, 40],
            "child_material": [100, 200, 300, 400],
            "Serviceeventcode_child": ["ChildA", "ChildB", "ChildC", "ChildD"],
            "Itemnumber_child": [101, 201, 301, 401],
            "MaterialName_child": ["Child A", "Child B", "Child C", "Child D"],
        }
    )

    with pd.ExcelWriter(xlsx_path) as writer:
        summary_df.to_excel(writer, sheet_name="event_materialGroup", index=False)
        detail_df.to_excel(writer, sheet_name="event_parent_child", index=False)

    summary = load_event_material_group_summary(xlsx_path)

    assert get_child_count_options(summary) == [2, 3, 4]
    assert get_serviceevent_options_for_child_count(summary, 2) == ["BladeBearingReplace"]

    rows = load_event_parent_child_rows(xlsx_path, "BladeBearingReplace")
    assert len(rows) == 2
    assert rows["Serviceeventcode_parent"].tolist() == ["BladeBearingReplace", "BladeBearingReplace"]


def test_build_material_badges_uses_name_and_number_format():
    rows = pd.DataFrame(
        {
            "Serviceeventcode_parent": ["BladeBearingReplace", "BladeBearingReplace"],
            "MaterialName_parent": ["BLADE BEARING MODULE", "BLADE BEARING MODULE"],
            "Itemnumber_parent": [760306, 76221971],
            "MaterialName_child": ["LUB SYS F. BLADE BEARING 2 MW", "ANCHOR,50 mm,10 mm,SS,4"],
            "Itemnumber_child": [764330, 29102244],
        }
    )

    badges = build_material_badges(rows)

    assert len(badges) == 2
    assert badges[0]["parent_label"] == "BLADE BEARING MODULE.760306"
    assert badges[0]["children"][0]["label"] == "LUB SYS F. BLADE BEARING 2 MW.764330"
