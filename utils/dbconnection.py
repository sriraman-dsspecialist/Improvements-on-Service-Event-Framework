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