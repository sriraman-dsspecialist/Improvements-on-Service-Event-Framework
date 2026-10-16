import subprocess
import sys
from pathlib import Path
from pipeline.data_fetch import fetch_tasklist_input
from logic.tasklist.tasklist_duplicacy import tasklist_duplicity
from utils.config import config
from utils.logger import logger


def main():
    if config.run.data_fetch:
        if config.data_fetch.tasklist:
            fetch_tasklist_input()
            tasklist_duplicity()
            logger.info("Tasklist input data fetched and processed.")

    if config.run.build_app:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(config.locations.streamlit_app)],
            check=True,
        )


if __name__ == "__main__":
    main()
