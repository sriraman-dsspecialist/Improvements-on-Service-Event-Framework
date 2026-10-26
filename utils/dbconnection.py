from sqlalchemy import create_engine
import urllib.parse

from utils.logger import logger
from utils.constants import *

logger_package_string = "SQLAlchemy: "

# Create SQLAlchemy connection string
# URL-encode the connection string for SQLAlchemy
params = urllib.parse.quote_plus(conn_str)
sqlalchemy_conn_str = f"mssql+pyodbc:///?odbc_connect={params}"
# Create engine
engine = create_engine(sqlalchemy_conn_str)
logger.info(f"{logger_package_string}Database connection configured successfully!")


def close_db_connection():
    """Dispose the configured SQLAlchemy engine to close the database connection."""
    if engine is not None:
        logger.info(f"{logger_package_string}Closing database connection...")
        engine.dispose()
        logger.info(f"{logger_package_string}Database connection closed successfully!")