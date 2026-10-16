import streamlit as st
from pathlib import Path
import pandas as pd
from tasklist import tasklist_page
from app.material.material_duplicacy import material_duplicacy_page
from app.material.materialgroup_duplicacy  import materialgroup_duplicacy_page
from app.material.material_group_conflict_or import material_group_conflict_page_or
from app.material.material_group_conflict_and import material_group_conflict_page_and
from app.material.materialgroup_mixie import materialgroup_mixie_page
from app.material.material_multiple_mgs import material_multiple_mgs_page
from app.material.parent_child_disparity import disparity_parent_child_page
from app.events.event_clustering import event_clusters
from app.events.misspelt_events import misspelt_events
from app.events.event_distribution import event_distribution


ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "icons"

st.logo(
    image=str(ICONS / "vestas_logo.jpg"),
    link="https://www.vestas.com/en",
)

st.set_page_config(layout="wide")
st.header("Improvements on Service Event Framework")
st.divider()

# Pages under material section
mat_page_1 = st.Page(material_duplicacy_page, title="Material Duplicity")
mat_page_2 = st.Page(materialgroup_duplicacy_page, title="Material Group Duplicity")
mat_page_3_AND = st.Page(material_group_conflict_page_and, title="Material Group Conflict \\{AND\\}")
mat_page_3_OR = st.Page(material_group_conflict_page_or, title="Material Group Conflict \\{OR\\}")
mat_page_4 = st.Page(materialgroup_mixie_page, title="Material Group Mixie")
mat_page_5 = st.Page(material_multiple_mgs_page, title="Multiple Material Groups")
mat_page_6 = st.Page(disparity_parent_child_page, title="Parent and Child Materials")

# Pages under service event inconsistencies section
event_page_1 = st.Page(event_clusters, title="Event Clustering")
event_page_2 = st.Page(misspelt_events, title="Misspelt Events")
event_page_3 = st.Page(event_distribution, title="Distribution of Service Events")

pg = st.navigation(
    {
        "Task List Group": [st.Page(tasklist_page.page1, title='TaskList Duplicity')],
        "Material": [mat_page_1, mat_page_2, mat_page_3_AND, mat_page_3_OR, mat_page_4, mat_page_5, mat_page_6],
        "Service Event Inconsistencies": [event_page_1, event_page_2, event_page_3],
    },
    position="sidebar",
    expanded=False,
)

pg.run()   