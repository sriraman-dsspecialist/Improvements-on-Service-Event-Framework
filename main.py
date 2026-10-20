import subprocess
import sys
from pathlib import Path
from pipeline.data_fetch import fetch_tasklist_input, fetch_input_from_DB
from processing.tasklist.tasklist_duplicacy import tasklist_duplicity
from processing.material.material_duplicity import processing_material_allthreads
from utils.config import config
from utils.logger import logger


def main():
    if config.run.data_fetch:
        if config.data_fetch.tasklist:
            fetch_tasklist_input()
            tasklist_duplicity()
            logger.info("Tasklist input data fetched and processed.")

        if config.data_fetch.material:
            smat =fetch_input_from_DB(config.input_files.serviceEvent_material, True)
        if config.data_fetch.materialgroup:
            smg = fetch_input_from_DB(config.input_files.serviceEvent_materialgroup, True)
        if config.data_fetch.material or config.data_fetch.materialgroup:
            processing_material_allthreads(smat, smg)
            logger.info("Service event material input data fetched and processed.")

        if config.data_fetch.event:
            pass

    if config.run.build_app:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(config.locations.streamlit_app)],
            check=True,
        )


if __name__ == "__main__":
    main()
