import os
from json import load
from logging import getLogger
from pathlib import Path

from qtpy.QtGui import QColor

config_file = Path(__file__).parent / "config.json"
with config_file.open() as f:
    loaded_json: dict = load(f)

light_stylesheet = Path(__file__).parent / "stylesheets/light_mode.qss"
dark_stylesheet = Path(__file__).parent / "stylesheets/dark_mode.qss"

logger = getLogger("")

datetime_pv = loaded_json["datetime_pv"]

DOCUMENTATION_URL = loaded_json.get("documentation_url")
FEEDBACK_FORM_URL = loaded_json.get("feedback_form_url")

# Set default save file directory
# If the directory does not exist, set it to the home directory
save_file_dir = Path(os.path.expandvars(loaded_json["save_file_dir"]))
if not save_file_dir.is_dir():
    logger.warning(f"Config file's save_file_dir path does not exist: {save_file_dir}")
    save_file_dir = Path.home()
    logger.warning(f"Setting save_file_dir to home: {save_file_dir}")

# Set color palettes from loaded json file
color_palette: dict[str, list[QColor]] = {}
for name, hex_codes in loaded_json["color_palettes"].items():
    color_palette[name] = [QColor(hex_code) for hex_code in hex_codes]

# Set the default thread count for numexpr
# 8 is determined to be a safe default for most systems according to numxerpr documentation
numexpr_threads = os.environ.get("NUMEXPR_MAX_THREADS", None)
if numexpr_threads is None:
    os.environ["NUMEXPR_MAX_THREADS"] = "8"
    logger.debug("NUMEXPR_MAX_THREADS not set, defaulting to 8")
