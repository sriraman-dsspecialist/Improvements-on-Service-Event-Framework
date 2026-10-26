import os
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from pathlib import Path
from utils.logger import logger
from utils.utility import save_excel_sheets

def disparity_materials(material_df):
    """Identify parent-child material disparity rows and save the processed output workbook."""
    csv_path = os.path.join(config.locations.inputs, config.input_files.parent_child_materials + ".csv")
    parent_child_df = pd.read_csv(csv_path)
    parent_child_df.columns = ['parent_material', 'child_material']

    req_cols = ['Serviceeventcode','Itemnumber','MaterialName']
    m1 = material_df[req_cols].merge(parent_child_df, left_on='Itemnumber', right_on='parent_material', how='left')
    m1.dropna(inplace=True)
    m2 = m1.merge(material_df[req_cols], right_on='Itemnumber', left_on='child_material', how='inner', suffixes=['_parent', '_child'])

    req_cols = ['Serviceeventcode_parent','Serviceeventcode_child']
    m2f = m2[req_cols].drop_duplicates(ignore_index=True)

    m2fg = m2f.groupby(['Serviceeventcode_parent'])['Serviceeventcode_child'].count().reset_index(name='child_count').sort_values(by='child_count', ascending=False)
    df_save_dict = {
        'event_parent_child': m2,
        'event_materialGroup': m2fg,
    }

    save_excel_sheets(df_save_dict, os.path.join(config.locations.processed, config.processed_files.disparity_materials+ "_processed.xlsx"))
    logger.info(f"(6/6) Material Parent-Child analysis data processed for {len(material_df)} records")