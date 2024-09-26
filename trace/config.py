import os
from json import load
from logging import getLogger
from pathlib import Path

from qtpy.QtGui import QColor

config_file = Path(__file__).parent / "config.json"
with config_file.open() as f:
    loaded_json = load(f)

logger = getLogger("")

datetime_pv = loaded_json["datetime_pv"]

save_file_dir = Path(os.path.expandvars(loaded_json["save_file_dir"]))
if not save_file_dir.is_dir():
    logger.warning(f"Config file's save_file_dir path does not exist: {save_file_dir}")
    save_file_dir = Path.home()
    logger.warning(f"Setting save_file_dir to home: {save_file_dir}")

archiver_urls = loaded_json["archivers"]
if not archiver_urls:
    archiver_urls = [os.getenv("PYDM_ARCHIVER_URL")]

color_palette = [QColor(hex_code) for hex_code in loaded_json["colors"]]
