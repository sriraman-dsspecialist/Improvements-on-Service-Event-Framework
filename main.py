import logging
import os
import subprocess
import sys
import warnings
from pathlib import Path
from pipeline.data_fetch import fetch_tasklist_input, fetch_input_from_DB
from utils.utility import load_input_excel
from processing.events.event_inconsistencies import processing_events_allThreads, get_event_distribution
from processing.tasklist.tasklist_duplicacy import tasklist_duplicity
from processing.material.material_duplicity import processing_material_allthreads
from utils.config import config
from utils.dbconnection import close_db_connection
from utils.logger import logger

# Silence noisy runtime warnings that are not actionable for this app.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, message=".*use_container_width.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*You are sending unauthenticated requests to the HF Hub.*")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("streamlit").setLevel(logging.ERROR)

def main():
    try:
        # Data fetch stage
        if config.run.data_fetch:
            if config.data_fetch.tasklist:
                fetch_tasklist_input()

            global smat, smg
            if config.data_fetch.material:
                smat = fetch_input_from_DB(config.input_files.serviceEvent_material, True)
            else:
                smat = load_input_excel(config.input_files.serviceEvent_material)

            if config.data_fetch.materialgroup:
                smg = fetch_input_from_DB(config.input_files.serviceEvent_materialgroup, True)
            else:
                smg = load_input_excel(config.input_files.serviceEvent_materialgroup)
                smg['MaterialGroup'] = smg['MaterialGroup'].astype(str)

        # Data processing stage
        if config.run.data_processing:
            if config.data_fetch.tasklist:
                tasklist_duplicity()
                logger.info("Tasklist input data fetched and processed.")

            if config.data_fetch.material or config.data_fetch.materialgroup:
                processing_material_allthreads(smat, smg)
                logger.info("Service event material input data fetched and processed.")

            if config.data_fetch.event:
                event_material_df = smat if config.data_fetch.material else None
                get_event_distribution()
                processing_events_allThreads(event_material_df)
                logger.info("Service event input data fetched and processed.")
    finally:
        close_db_connection()

    if config.run.build_app:
                subprocess.run(
                    [sys.executable, "-m", "streamlit", "run", str(config.locations.streamlit_app)],
                    check=True,
                )


if __name__ == "__main__":
    main()
