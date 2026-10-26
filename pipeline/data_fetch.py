import os
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from pathlib import Path
from utils.utility import sql_to_df
from utils.logger import logger

LEGACY_SQL_ALIASES = {
    "Service_Event_Distribution": "ServiceEvent_Order_Counts",
}


def resolve_sql_filename(filename):
    """Normalize a configured SQL filename to the expected query name.

    Some historical filenames used older aliases that are still kept for backward
    compatibility. This helper resolves both the current and legacy query names.
    """
    if filename is None:
        return None
    normalized = filename[:-4] if filename.lower().endswith(".sql") else filename
    return LEGACY_SQL_ALIASES.get(normalized, normalized)


def fetch_tasklist_input():
    """Fetch tasklist input data from the database and persist it to Excel."""
    sql_filename = config.input_files.tasklist
    df = sql_to_df(sql_filename)
    df.to_excel(os.path.join(config.locations.inputs, sql_filename+'.xlsx'), index=False)
    logger.info(f"Tasklist input data fetched with shape {df.shape}")

def get_tasklist_descriptions(tasklist_values):
    """Return a cleaned mapping of task list group IDs to their descriptions.

    Parameters
    ----------
    tasklist_values : iterable
        Task list group identifiers to retrieve from the source database or saved
        Excel files.
    """
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

    if not config.data_fetch.tasklist:
        # start_time = pd.Timestamp.now()
        # logger.info(f"Executing SQL query to fetch tasklist descriptions")
        tasklist_detail = pd.read_sql_query(sql, engine)
        # end_time = pd.Timestamp.now()
        # logger.info(f"Time taken to fetch tasklist descriptions: {(end_time - start_time)} seconds")
    else:
        tasklist_desc_path = os.path.join(config.locations.inputs, config.input_files.tasklist_descriptions+'.xlsx')
        tasklist_detail = pd.read_excel(tasklist_desc_path)
        logger.info(f"Tasklist descriptions loaded from Excel: {tasklist_desc_path}")

    tasklist_detail['TaskListGroup'] = tasklist_detail['TaskListGroup'].astype(int)
    tasklist_detail = tasklist_detail.groupby(['TaskListGroup']).agg({'TaskListDescription':'first'})
    tasklist_detail = tasklist_detail.reset_index()
    tasklist_detail.to_excel(os.path.join(config.locations.inputs, config.input_files.tasklist_descriptions+'.xlsx'), index=False)
    logger.info(f"Tasklist descriptions data fetched for {len(tasklist_detail)} TaskListGroups")
    return tasklist_detail

def fetch_input_from_DB(filename = None, need_output=False):
    """Fetch a configured SQL dataset from the database and save a local Excel copy.

    Parameters
    ----------
    filename : str, optional
        Name of the SQL file without the .sql extension.
    need_output : bool, default False
        If True, return the DataFrame after saving it locally.
    """
    if filename is None:
        raise ValueError("No filename provided for fetching input from the database")

    resolved_filename = resolve_sql_filename(filename)
    if resolved_filename is None:
        raise ValueError(f"No SQL query found for filename: {filename}")

    df = sql_to_df(resolved_filename)
    df.to_excel(os.path.join(config.locations.inputs, resolved_filename+'.xlsx'), index=False)
    logger.info(f"{resolved_filename} input data fetched with shape {df.shape}")
    if need_output:
        return df