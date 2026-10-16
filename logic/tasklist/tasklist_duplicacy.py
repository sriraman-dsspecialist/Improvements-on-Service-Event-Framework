import os
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from pathlib import Path
from pipeline.data_fetch import get_tasklist_descriptions


def tasklist_duplicity():
    xlsx_path = os.path.join(config.locations.inputs, config.input_files.tasklist + ".xlsx")
    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"File not found: {xlsx_path}")

    tasklist = pd.read_excel(xlsx_path)
    tasklist_all = tasklist[['Serviceeventcode','TaskListGroup']]
    tasklist_all = tasklist_all.drop_duplicates()
    tasklist_2 = tasklist_all.loc[tasklist_all['TaskListGroup'].isin(tasklist_all['TaskListGroup'])]
    tasklist_2['TaskListGroup'] = tasklist_2['TaskListGroup'].astype('str')

    # Preprocess the tasklist IDs to ensure consistent formatting
    add_zeros = lambda x: '000'+x if len(x)==5 else x
    tasklist_2['TaskListGroup_normal'] = tasklist_2['TaskListGroup'].copy()
    tasklist_2['TaskListGroup'] = tasklist_2['TaskListGroup'].apply(add_zeros)
    tasklist_values = tasklist_2["TaskListGroup"].dropna().astype(str).unique().tolist()

    # Get tasklistgroup descriptions for better clarity
    tasklist_desc = get_tasklist_descriptions(tasklist_values)
    tasklist_2['TaskListGroup'] = tasklist_2['TaskListGroup'].astype(int)
    tasklist_merged = tasklist_2.merge(tasklist_desc, on='TaskListGroup', how='left')
    req_cols = ['Serviceeventcode', 'TaskListGroup', 'TaskListDescription']
    tasklist_merged = tasklist_merged[req_cols]
    tasklist_merged.to_excel(os.path.join(config.locations.processed, config.input_files.tasklist + "_processed.xlsx"), index=False)
    