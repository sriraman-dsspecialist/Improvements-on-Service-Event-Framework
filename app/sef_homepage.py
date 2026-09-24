import streamlit as st
from pathlib import Path
import pandas as pd
from tasklist import tasklist_page
from app.material.material_duplicacy import material_duplicacy_page
from app.material.materialgroup_duplicacy  import materialgroup_duplicacy_page
from app.material.material_group_conflict_or import material_group_conflict_page_or
from app.material.material_group_conflict_and import material_group_conflict_page_and
from app.material.materialgroup_mixie import materialgroup_mixie_page


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

pg = st.navigation(
    {
        "Task List Group": [st.Page(tasklist_page.page1, title='TaskList Duplicity')],
        "Material": [mat_page_1, mat_page_2, mat_page_3_AND, mat_page_3_OR, mat_page_4],
    },
    position="sidebar",
    expanded=False,
)

pg.run()   