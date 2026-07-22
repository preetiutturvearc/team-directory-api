import logging
import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from controller import register_routes
from directory import EmployeeDirectory
from exceptions import DuplicateEmailError, EmployeeNotFoundError, InvalidEmployeeDataError

STORAGE_PATH = os.environ.get("DIRECTORY_DB_PATH", "directory.json")
API_KEY = os.environ.get("API_KEY", "dev-secret-key")
PORT = int(os.environ.get("PORT", "5000"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("service.log")],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
directory = EmployeeDirectory(storage_path=STORAGE_PATH)
directory.load_from_file(STORAGE_PATH)

STATUS_MAP = {
    EmployeeNotFoundError: 404,
    DuplicateEmailError: 409,
    InvalidEmployeeDataError: 400,
}

register_routes(app, directory, logger, API_KEY, STATUS_MAP)

if __name__ == "__main__":
    app.run(threaded=True, port=PORT, debug=True)
