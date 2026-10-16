import os
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from pathlib import Path
from utils.utility import sql_to_df
from utils.logger import logger

def fetch_tasklist_input():
    """Fetch tasklist input data from the database."""
    sql_filename = config.input_files.tasklist
    df = sql_to_df(sql_filename)
    df.to_excel(os.path.join(config.locations.inputs, sql_filename+'.xlsx'), index=False)
    logger.info(f"Tasklist input data fetched with shape {df.shape}")

def get_tasklist_descriptions(tasklist_values):
    if not tasklist_values:
        raise ValueError("No TaskListGroup values found")

    normalized_values = []
    for value in tasklist_values:
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned and cleaned.lower() not in {"nan", "none"}:
            normalized_values.append(cleaned.replace("'", "''"))

    if not normalized_values:
        raise ValueError("No valid TaskListGroup values found")

    unique_values = list(dict.fromkeys(normalized_values))
    values_sql = ", ".join(f"'{value}'" for value in unique_values)

    sql = f"""
    SELECT DISTINCT
        SAPGroup AS TaskListGroup,
        TaskListDescription AS TaskListDescription
    FROM dim.tasklistdetail
    WHERE SAPGroup IN ({values_sql})
    """

    # start_time = pd.Timestamp.now()
    # logger.info(f"Executing SQL query to fetch tasklist descriptions")
    tasklist_detail = pd.read_sql_query(sql, engine)
    # end_time = pd.Timestamp.now()
    # logger.info(f"Time taken to fetch tasklist descriptions: {(end_time - start_time)} seconds")

    tasklist_detail['TaskListGroup'] = tasklist_detail['TaskListGroup'].astype(int)
    tasklist_detail = tasklist_detail.groupby(['TaskListGroup']).agg({'TaskListDescription':'first'})
    tasklist_detail = tasklist_detail.reset_index()
    tasklist_detail.to_excel(os.path.join(config.locations.inputs, config.input_files.tasklist_descriptions+'.xlsx'), index=False)
    logger.info(f"Tasklist descriptions data fetched for {len(tasklist_detail)} TaskListGroups")
    return tasklist_detail