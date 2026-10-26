# User Guide

## 1. Overview
This project is a data-quality and service-event analysis toolkit. It reads source information from SQL Server and/or Excel files, then highlights issues such as duplicate task lists, inconsistent material groups, event clustering, misspellings, and material-parent/child mismatches.

The user interface is a Streamlit application found in `app/sef_homepage.py`, and the processing entry point is `main.py`.

## 2. Prerequisites
Before running the project, ensure that you have:
- Windows with SQL Server access configured
- Conda installed
- Access to the project folder
- An available ODBC SQL Server driver

## 3. Set up the Conda environment
Use the project’s recommended runtime version:

```bash
conda create -n build_app python=3.10 -y
conda activate build_app
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Important: The project is intended to run on Python 3.10. A newer Python version such as 3.14 may fail because `pyenchant` is not available there.

## 4. Configure the project
Update `config.yaml` before running the app. The file contains the main runtime settings.

### Core configuration values

#### `run`
- `data_fetch`: enable SQL/Excel data extraction
- `data_processing`: enable processing logic
- `build_app`: launch the Streamlit app after the pipeline completes

Example:

```yaml
run:
  data_fetch: False
  data_processing: False
  build_app: True
```

#### `data_fetch`
Controls which datasets are loaded.

- `tasklist`: fetch task list data
- `material`: fetch material data
- `materialgroup`: fetch material group data
- `event`: fetch event distribution data

#### `locations`
Defines the main folder paths used by the app.

- `base_dir`: project root directory
- `inputs`: folder for raw input files
- `processed`: folder for processed files
- `outputs`: final output folder
- `sql_queries`: SQL directory
- `streamlit_app`: dashboard entry script

#### `input_files`
Configures the expected source file names and SQL query names.

Examples:
- `tasklist`
- `serviceEvent_material`
- `serviceEvent_materialgroup`
- `parent_child_materials`
- `serviceEvent_distribution`

#### `processed_files`
Defines the output names used when saving processed spreadsheets.

Examples:
- `event_inconsistencies`
- `materialgroup_mixie`
- `multiple_materialgroups`
- `disparity_materials`

## 5. Database connection
The SQL Server connection is configured in `utils/constants.py`.

```python
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=sql-vdc\\dpa;"
    "DATABASE=vpdc;"
    "Trusted_Connection=yes;"
)
```

If your environment uses a different SQL Server name, database, or authentication model, update this value before running the project.

## 6. Run the application
From the project root, run:

```bash
python main.py
```

This command will:
1. load the configuration
2. fetch data if enabled
3. process the configured datasets if enabled
4. launch the Streamlit dashboard if `build_app` is true

### Alternative: run the dashboard directly
```bash
streamlit run app/sef_homepage.py
```

## 7. Data flow
The application follows this pattern:
1. Source data is fetched from SQL Server or an input Excel file.
2. Data is processed in `processing/` modules.
3. Results are saved to the configured processed and output folders.
4. The dashboard displays them in interactive tabs.

## 8. Expected output folders
- `data/inputs/`: raw source files used by the project
- `data/processed/`: processed analysis outputs
- `data/outputs/`: final dashboard or summary exports
- `logs/`: runtime and error logs

## 9. Troubleshooting

### Python version mismatch
If `pip install -r requirements.txt` fails with `pyenchant` issues, make sure you are using Python 3.10:

```bash
conda activate build_app
python --version
```

### Missing database driver
If SQL queries fail or the connection cannot be created, verify that the SQL Server ODBC driver is installed and the connection string in `utils/constants.py` is valid.

### Missing output folders
The application creates the main data folders automatically when it loads the YAML configuration, but you should verify that the paths in `config.yaml` are valid.

## 10. Typical usage
A common setup for running the tool is:

```yaml
run:
  data_fetch: True
  data_processing: True
  build_app: True
```

This fetches, processes, and then opens the dashboard. If you only want to review the dashboard without re-fetching data, set `data_fetch` to `False` and leave the local Excel files in place.

## 11. Support and maintenance
If the app needs to be extended, the usual places to edit are:
- `config.yaml` for runtime behavior
- `processing/` for algorithm or validation logic
- `pipeline/` for source data extraction
- `app/` for dashboard page composition
- `utils/` for shared helpers and database setup
