import os
import re
from datetime import datetime, date
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from pathlib import Path

from utils.config import config
from utils.dbconnection import engine as sqlengine

# lambda function to set the given location under the results folder if not provided
set_default_location = lambda results_folder, config_attr, filename :  os.path.join(results_folder, filename) if config_attr is None or config_attr.strip()=="" else config_attr

def create_csv_file_if_absent(registry_file, columns=[]):
    """
    Creates a CSV file with specified columns if it doesn't exist, or reads existing file.
    
    Arguments:
        registry_file (str): Full path to the CSV file
        columns (list): List of column names for new CSV file (default: empty list)
    
    Returns:
        pandas.DataFrame: Existing DataFrame if file exists, or empty DataFrame with specified columns
    """
    if os.path.exists(registry_file):
        regis_df = pd.read_csv(registry_file)
    else:
        regis_df = pd.DataFrame(columns=columns)
        regis_df.to_csv(registry_file, header=True, index=False)
    return regis_df

def create_directory_if_absent(directory_path):
    """
    Creates a directory if it doesn't already exist.
    
    Arguments:
        directory_path (str): Full path to the directory to create
    
    Returns:
        None
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def _split_sql_statements(sql_query):
    """Split a SQL script into executable statements while ignoring database switches like USE."""
    statements = []
    for part in sql_query.split(';'):
        statement = part.strip()
        if not statement:
            continue
        if re.fullmatch(r'USE\s+\w+', statement, flags=re.IGNORECASE):
            continue
        statements.append(statement)
    return statements


def _get_result_statement(statements):
    """Pick the last statement in a script that returns rows so it can be materialized as a DataFrame."""
    result_statements = [
        statement for statement in statements
        if re.search(r'\b(SELECT|WITH)\b', statement, flags=re.IGNORECASE)
    ]
    if not result_statements:
        return statements[-1]
    return result_statements[-1]


def sql_to_df(filename, return_query = 0):
    """
    Executes a SQL query from a file and returns the result as a DataFrame.
    
    Arguments:
        filename (str): Name of the SQL file (without .sql extension) located in sql/ folder
        return_query (int): If 1, returns both DataFrame and query string; if 0, returns only DataFrame (default: 0)
    
    Returns:
        pandas.DataFrame: Query results as DataFrame
        OR
        tuple: (DataFrame, str) if return_query=1, containing both results and query string
    """
    file_path = os.path.join(config.locations.sql_queries, filename+'.sql')
    sql_query = read_sql_file(file_path)
    statements = _split_sql_statements(sql_query)
    result_statement = _get_result_statement(statements)

    if len(statements) == 1:
        df = pd.read_sql(result_statement, sqlengine)
        if return_query: return df, result_statement
        return df

    with sqlengine.begin() as connection:
        for statement in statements:
            if statement == result_statement:
                break
            connection.exec_driver_sql(statement)
        df = pd.read_sql(result_statement, connection)

    if return_query: return df, result_statement
    return df


# Read and execute SQL file from the sql folder
def read_sql_file(file_path):
    """
    Reads SQL query content from a file.
    
    Arguments:
        file_path (str): Full path to the SQL file
    
    Returns:
        str: SQL query content as a string, or None if file reading fails
    """
    """Read SQL content from file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    return None

# Store interim data for analysis
def store_interim_data(df, filename):
    """
    Saves a DataFrame to the interim folder as a CSV file for analysis and debugging.
    
    Arguments:
        df (pandas.DataFrame): DataFrame to save
        filename (str): Name of the file (without .csv extension)
    
    Returns:
        None - Saves CSV file to config.locations.interim_folder
    """
    df.to_csv(os.path.join(config.locations.interim_folder, filename+'.csv'), index=False)

# Create equal divisions between any two numbers with a given precision
def create_equal_divisions(start, stop, num_divisions, precision=2):
    """
    Creates evenly spaced divisions between two numbers with specified precision.
    
    Arguments:
        start (float): Starting value
        stop (float): Ending value
        num_divisions (int): Number of divisions to create
        precision (int): Number of decimal places (default: 2)
    
    Returns:
        pandas.Series: Series of evenly spaced float values rounded to specified precision
    """
    return pd.Series(  [ round(x, precision) for x in  list( pd.np.linspace(start, stop, num=num_divisions) ) ]  )

# Generate a float sequence between start and stop with num number of values
def get_float_sequence(start=1, stop=7.99, num=0):
    """
    Generates an evenly distributed sequence of float values between start and stop.
    
    Arguments:
        start (float): Starting value (default: 1)
        stop (float): Ending value (default: 7.99)
        num (int): Number of values to generate (default: 0)
    
    Returns:
        pandas.Series: Series containing num evenly spaced values rounded to 2 decimal places
    """
    return pd.Series(np.round(np.linspace(start, stop, num),2))

make_df_cols_lowercase = lambda df: df.rename(columns={col: col.lower() for col in df.columns})

def load_input_excel(file_key):
    """Load an Excel file from the configured inputs directory by file key name."""
    base_dir = Path(config.locations.inputs)
    file_name = getattr(config.input_files, file_key, None)
    if file_name is None:
        raise ValueError(f"No input file configured for '{file_key}'")
    
    file_name += '.xlsx'    
    full_path = (base_dir / file_name).resolve()
    if full_path.exists():
        return pd.read_excel(full_path)
    raise FileNotFoundError(f"No file found for '{file_key}' in {base_dir}")

def save_excel_sheets(data_dict, excel_path):

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for sheet_name, df_sheet in data_dict.items():
            if isinstance(df_sheet, pd.DataFrame):
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                pd.DataFrame(df_sheet).to_excel(writer, sheet_name=sheet_name, index=False)