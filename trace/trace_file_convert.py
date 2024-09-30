#!/usr/bin/env python3

import re
import json
import logging
import xml.etree.ElementTree as ET
from os import path, getenv
from re import compile
from typing import Dict, List, Union
from pathlib import Path
from argparse import Action, Namespace, ArgumentParser
from datetime import datetime
from collections import OrderedDict

from qtpy.QtGui import QColor

from pydm.widgets.timeplot import PyDMTimePlot

if __name__ in logging.Logger.manager.loggerDict:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger("")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("INFO")
    handler.setLevel("INFO")


class TraceFileConverter:
    """Converter class that will convert save files for the Java-based Archive
    Viewer into a format readable by the Trace application. This class can also
    be used for importing data into Trace or exporting data from it.
    """

    # Java date time conversion regex
    full_java_absolute_re = compile(r"^[01]\d/[0-3]\d/\d{4}\s*((?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?)?$")
    java_date_re = compile(r"^[01]\d/[0-3]\d/\d{4}")
    time_re = compile(r"(?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?")

    def __init__(self, input_file: Union[str, Path] = "", output_file: Union[str, Path] = "") -> None:
        self.input_file = input_file
        self.output_file = output_file

        self.stored_data = None

    def import_is_xml(self):
        """Helper function to determine if the import file is in XML format."""
        with self.input_file.open() as f:
            return f.readline().startswith("<?xml")

    def import_is_stp(self):
        """Helper function to determine if the import file is a StripTool file."""
        with self.input_file.open() as f:
            return f.readline().startswith("StripConfig")

    def import_file(self, file_name: Union[str, Path] = None) -> Dict:
        """Import Archive Viewer save data from the provided file. The file
        should be one of two types: '.trc' or '.xml'. The data is returned as
        well as saved in the stored_data property.

        Parameters
        ----------
        file_name : str or pathlib.Path
            The absolute filepath for the input file to import

        Returns
        -------
        dict
            A python dictionaty containing the data imported from the provided file
        """
        if file_name:
            self.input_file = Path(file_name)
        if not self.input_file.is_file():
            raise FileNotFoundError(f"Data file not found: {self.input_file}")

        text = self.input_file.read_text()
        if self.import_is_xml():
            etree = ET.ElementTree(ET.fromstring(text))
            self.stored_data = self.xml_to_dict(etree)
            if not (self.stored_data["pv"] or self.stored_data["formula"]):
                raise FileNotFoundError(f"Incorrect input file format: {self.input_file}")
            self.stored_data = self.convert_xml_data(self.stored_data)
        elif self.import_is_stp():
            self.stored_data = self.stp_to_dict(text)
            self.stored_data = self.convert_stp_data(self.stored_data)
        else:
            self.stored_data = json.loads(text)
            if not self.stored_data["curves"]:
                raise FileNotFoundError(f"Incorrect input file format: {self.input_file}")

        return self.stored_data

    def export_file(self, file_name: Union[str, Path] = None, output_data: Union[Dict, PyDMTimePlot] = None) -> None:
        """Export the provided Archive Viewer save data to the provided file.
        The file to export to should be of type '.trc'. The provided data can
        be either a dictionary or a PyDMTimePlot object. If no data is provided,
        then the converter's previously imported data is exported.

        Parameters
        ----------
        file_name : str or pathlib.Path
            The absolute file path of the file that save data should be written
            to. Should be of file type '.trc'.
        output_data : dict or PyDMTimePlot, optional
            The data that should be exported, by default uses previously imported data

        Raises
        ------
        FileNotFoundError
            If the provided file name does not match the expected output file type '.trc'
        ValueError
            If no output data is provided and the converter hasn't imported data previously
        """
        if file_name:
            self.output_file = Path(file_name)
        if not self.output_file.suffix:
            self.output_file = self.output_file.with_suffix(".trc")
        elif not self.output_file.match("*.trc"):
            raise FileNotFoundError(f"Incorrect output file format: {self.output_file.suffix}")

        if not output_data:
            if not self.stored_data:
                raise ValueError(
                    "Output data is required but was not provided " "and the 'stored_data' property is not populated."
                )
            output_data = self.stored_data
        elif isinstance(output_data, PyDMTimePlot):
            output_data = self.get_plot_data(output_data)

        for obj in output_data["y-axes"] + output_data["curves"] + output_data["formula"]:
            for k, v in obj.copy().items():
                if v is None:
                    del obj[k]

        with open(self.output_file, "w") as f:
            json.dump(output_data, f, indent=4)

    def convert_xml_data(self, data_in: Dict = {}) -> Dict:
        """Convert the inputted data from being formatted for the Java Archive
        Viewer to a format used by trace. This is accomplished by converting one
        dictionary structure to another.

        Parameters
        ----------
        data_in : dict, optional
            The input data to be converted, by default uses previously imported data

        Returns
        -------
        dict
            The converted data in a format that can be used by trace
        """
        if not data_in:
            data_in = self.stored_data

        converted_data = {}

        converted_data["archiver_url"] = data_in.get("connection_parameter", getenv("PYDM_ARCHIVER_URL"))
        converted_data["archiver_url"] = converted_data["archiver_url"].replace("pbraw://", "http://")

        legend_dict = data_in["legend_configuration"]
        legend_dict["show_curve_name"] = legend_dict["show_ave_name"]
        del legend_dict["show_ave_name"]

        converted_data["plot"] = {"title": data_in["plot_title"], "legend": legend_dict}

        # Convert date formats from MM/DD/YYYY --> YYYY-MM-DD
        converted_data["time_axis"] = {}
        for key, val in data_in["time_axis"][0].items():
            if key in ["start", "end"]:
                val = self.reformat_date(val)
            converted_data["time_axis"][key] = val

        converted_data["y-axes"] = []
        for axis_in in data_in["range_axis"]:
            ax_dict = {
                "name": axis_in["name"],
                "label": axis_in["name"],
                "minRange": axis_in["min"],
                "maxRange": axis_in["max"],
                "orientation": axis_in["location"],
                "logMode": axis_in["type"] != "normal",
            }
            filtered_dict = self.remove_null_values(ax_dict)
            converted_data["y-axes"].append(filtered_dict)

        converted_data["curves"] = []
        for pv_in in data_in["pv"]:
            color = self.srgb_to_qColor(pv_in["color"])
            pv_dict = {
                "name": pv_in["name"],
                "channel": pv_in["name"],
                "yAxisName": pv_in["range_axis_name"],
                "lineWidth": int(float(pv_in["draw_width"])),
                "color": color.name(),
                "thresholdColor": color.name(),
            }
            filtered_dict = self.remove_null_values(pv_dict)
            converted_data["curves"].append(filtered_dict)

        converted_data["formula"] = []
        for formula_in in data_in["formula"]:
            color = self.srgb_to_qColor(pv_in["color"])
            formula = "f://" + formula_in["term"]
            for curve in formula_in["curveDict"].keys():
                insert = "{" + curve + "}"
                formula = re.sub(curve, insert, formula)
            formula_dict = {
                "name": formula_in["name"],
                "formula": formula,
                "curveDict": formula_in["curveDict"],
                "yAxisName": formula_in["range_axis_name"],
                "lineWidth": float(formula_in["draw_width"]),
                "color": color.name(),
                "thresholdColor": color.name(),
            }
            filtered_dict = self.remove_null_values(formula_dict)
            converted_data["formula"].append(filtered_dict)

        self.stored_data = converted_data
        return self.stored_data

    def convert_stp_data(self, data_in: Dict = {}) -> Dict:
        """Convert the inputted data from a format used by StripTool to a format
        used by Trace. This is accomplished by converting one dictionary structure
        to another.

        Parameters
        ----------
        data_in : dict, optional
            The input data to be converted, by default uses previously imported data

        Returns
        -------
        dict
            The converted data in a format that can be used by trace
        """
        if not data_in:
            data_in = self.stored_data

        converted = {"archiver_url": getenv("PYDM_ARCHIVER_URL")}

        # Convert all colors to a usable format
        for k, v in data_in["Color"].items():
            color = self.xColor_to_qColor(v)
            data_in["Color"][k] = color.name()

        # Convert plot config
        converted["plot"] = {}
        converted["plot"]["xGrid"] = bool(data_in["Option"]["GridXon"])
        converted["plot"]["yGrid"] = bool(data_in["Option"]["GridYon"])
        converted["plot"]["backgroundColor"] = data_in["Color"]["Background"]

        # Convert time_axis
        converted["time_axis"] = {"name": "Main Time Axis", "location": "bottom"}
        converted["time_axis"]["start"] = "-" + data_in["Time"]["Timespan"] + "s"
        converted["time_axis"]["end"] = "now"

        y_axis_names = {}

        # Convert curves
        converted["curves"] = []
        converted["formula"] = []
        for ind, data in data_in["Curve"].items():
            curve = {}
            curve["name"] = data["Name"]
            curve["channel"] = data["Name"]

            color_key = f"Color{int(ind) + 1}"
            curve["color"] = data_in["Color"][color_key]
            curve["thresholdColor"] = data_in["Color"][color_key]

            # Set curve's axis to the curve's units
            if "Units" not in data:
                continue
            unit = data["Units"]
            curve["yAxisName"] = unit

            # Set the associated axis' log mode
            log_mode = data["Scale"] == "1"
            if unit not in y_axis_names:
                y_axis_names[unit] = []
            y_axis_names[unit].append(log_mode)

            converted["curves"].append(curve)

        # Convert y-axes
        converted["y-axes"] = []
        for axis_name, log_mode in y_axis_names.items():
            axis = {"name": axis_name, "label": axis_name, "orientation": "left"}
            axis["logMode"] = all(log_mode)
            converted["y-axes"].append(axis)

        return converted

    @classmethod
    def reformat_date(cls, input_str: str) -> str:
        """Convert a time string from the format 'MM/DD/YYYY' --> 'YYYY-MM-DD'
        and retain time if included

        Parameters
        ----------
        input_str : str
            Date string in the format of 'MM/DD/YYYY'; can include a time

        Returns
        -------
        str
            Date string in the format of 'YYYY-MM-DD'
        """
        if not cls.full_java_absolute_re.fullmatch(input_str):
            return input_str

        date = cls.java_date_re.search(input_str).group()
        m, d, y = date.split("/")
        formatted_date = f"{y}-{m}-{d}"

        time_match = cls.time_re.search(input_str)
        if time_match:
            formatted_date += " " + time_match.group()
        return formatted_date

    @staticmethod
    def xml_to_dict(xml: ET.ElementTree) -> Dict:
        """Convert an XML ElementTree containing an Archive Viewer save
        file to a dictionary for easier use

        Parameters
        ----------
        xml : ET.ElementTree
            The XML ElementTree object read from the file

        Returns
        -------
        dict
            The data in a dictionary format
        """
        data_dict = {
            "connection_parameter": "",
            "plot_title": "",
            "legend_configuration": {},
            "time_axis": [],
            "range_axis": [],
            "pv": [],
            "formula": [],
        }

        data_dict["connection_parameter"] = xml.find("connection_parameter").text
        data_dict["plot_title"] = xml.find("plot_title").text
        data_dict["legend_configuration"] = xml.find("legend_configuration").attrib

        for key in ("time_axis", "range_axis", "pv"):
            for element in xml.findall(key):
                ele_dict = element.attrib
                ele_dict |= {sub_ele.tag: sub_ele.text for sub_ele in element}
                data_dict[key].append(ele_dict)
        key = "formula"
        for element in xml.findall(key):
            ele_dict = element.attrib
            curveDict = dict()
            for sub_ele in element:
                if sub_ele.tag == "argument_ave":
                    tempDict = sub_ele.attrib
                    curveDict[tempDict["variable"]] = tempDict["name"]
                else:
                    ele_dict |= {sub_ele.tag: sub_ele.text}
            ele_dict["curveDict"] = curveDict
            data_dict[key].append(ele_dict)
        return data_dict

    @staticmethod
    def stp_to_dict(stp_text: str) -> Dict:
        """Convert the StripTool file's text into a dictionary.

        Parameters
        ----------
        stp_text : str
            The full file text from the StripTool file

        Returns
        -------
        dict
            The data in a dictionary format
        """
        extracted_data = {}

        for line in stp_text.splitlines():
            line_split = line.split()
            if not line_split:
                continue

            key = line_split[0].removeprefix("Strip.")
            val = None
            if len(line_split) == 1:
                val = ""
            elif len(line_split) == 2:
                val = line_split[1]
            else:
                val = line_split[1:]

            # Find which child dictionary should contain the key-value pair
            data_loc = extracted_data
            key_split = key.split(".")
            for k in key_split[:-1]:
                if k not in data_loc:
                    data_loc[k] = {}
                data_loc = data_loc[k]
            data_loc[key_split[-1]] = val

        return extracted_data

    @staticmethod
    def get_plot_data(plot: PyDMTimePlot) -> dict:
        """Extract plot, axis, and curve data from a PyDMTimePlot object

        Parameters
        ----------
        plot : PyDMTimePlot
            The PyDM Plotting object to extract data from. Gets plot, axis, and curve data.

        Returns
        -------
        dict
            A dictionary representation of all of the relevant data for the given plot
        """
        output_dict = {
            "archiver_url": getenv("PYDM_ARCHIVER_URL"),
            "plot": {},
            "time_axis": {},
            "y-axes": [],
            "curves": [],
            "formula": [],
        }

        [start_ts, end_ts] = plot.getXAxis().range
        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(end_ts)
        output_dict["plot"] = plot.to_dict()
        output_dict["time_axis"] = {
            "name": "Main Time Axis",
            "start": start_dt.isoformat(sep=" ", timespec="seconds"),
            "end": end_dt.isoformat(sep=" ", timespec="seconds"),
            "location": "bottom",
        }

        for a in plot.getYAxes():
            axis_dict = json.loads(a, object_pairs_hook=OrderedDict)
            output_dict["y-axes"].append(axis_dict)

        for c in plot.getCurves():
            curve_dict = json.loads(c, object_pairs_hook=OrderedDict)
            if "channel" in curve_dict:
                if not curve_dict["channel"]:
                    continue
                output_dict["curves"].append(curve_dict)
            else:
                if not curve_dict["formula"]:
                    continue
                output_dict["formula"].append(curve_dict)

        return output_dict

    @staticmethod
    def srgb_to_qColor(srgb: str) -> QColor:
        """Convert RGB strings to QColors. The string is a 32-bit
        integer containing the aRGB values of a color. (e.g. #FF0000 or -65536)

        Parameters
        ----------
        srgb : str
            Either a hex value or a string containing a signed 32-bit integer

        Returns
        -------
        QColor
            A QColor object storing the color described in the string
        """
        if not srgb:
            return QColor()
        elif srgb[0] != "#":
            rgb_int = int(srgb) & 0xFFFFFFFF
            srgb = f"#{rgb_int:08X}"
        return QColor(srgb)

    @staticmethod
    def xColor_to_qColor(rgb: List[str]) -> QColor:
        """Convert XColor values into QColors. Colors in StripTool files (*.stp)
        are saved as XColors.

        Parameters
        ----------
        rgb : list(str)
            A list of strings containing the rgb values (0 <= rgb < 0xFFFF)

        Returns
        -------
        QColor
            A QColor object storing the color described in the string
        """
        for i in range(3):
            rgb[i] = int(rgb[i]) // 256

        return QColor(*rgb)

    @staticmethod
    def remove_null_values(dict_in: dict) -> dict:
        """Remove all key-value pairs from a given dictionary where the value is None

        Parameters
        ----------
        dict_in : dict
            Some dictionary, possibly containing key-value pairs where value is None

        Returns
        -------
        dict
            The same dictionary, but with those key-value pairs deleted
        """
        dict_out = dict_in.copy()
        for k, v in dict_in.items():
            if v is None:
                del dict_out[k]
        return dict_out


def main(input_file: Path = None, output_file: Path = None, overwrite: bool = False, clean: bool = False):
    # Check that the input file is usable
    if not input_file:
        raise FileNotFoundError("Input file not provided")
    elif not input_file.is_file():
        raise FileNotFoundError(f"Data file not found: {input_file}")
    elif not (input_file.match("*.xml") or input_file.match("*.stp")):
        raise FileNotFoundError(f"Incorrect input file format: {input_file}")

    # Check that the output file is usable
    if not output_file:
        output_file = input_file.with_suffix(".trc")
    elif not output_file.suffix:
        output_file = output_file.with_suffix(".trc")
    elif not output_file.match("*.trc"):
        raise FileNotFoundError(f"Incorrect output file format: {output_file}")

    # Check if file exists, and if it does if the overwrite flag is used
    if output_file.is_file() and not overwrite:
        raise FileNotFoundError(f"Output file exists but overwrite not enabled: {output_file}")

    # Complete the requested conversion
    converter = TraceFileConverter()

    converter.import_file(input_file)
    converter.export_file(output_file)

    # Remove the input file if requested
    if clean:
        input_file.unlink()
        logger.debug(f"Removing input file: {input_file}")

    return 0


class PathAction(Action):
    def __call__(self, parser: ArgumentParser, namespace: Namespace, values: str, option_string: str = None) -> None:
        """Convert filepath string from argument into  a pathlib.Path object"""
        new_path = path.expandvars(values)
        new_path = Path(new_path).expanduser()
        new_path = new_path.resolve()
        setattr(namespace, self.dest, new_path)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Trace File Converter",
        description="Convert files used by the Java Archive" " Viewer to a file format that can be used with Trace.",
    )
    parser.add_argument("input_file", action=PathAction, type=str, help="Path to the file to be converted")
    parser.add_argument(
        "--output_file", "-o", action=PathAction, type=str, help="Path to the output file (defaults to input file name)"
    )
    parser.add_argument("--overwrite", "-w", action="store_true", help="Overwrite the target file if it exists")
    parser.add_argument("--clean", action="store_true", help="Remove the input file after successful conversion")
    args = parser.parse_args()

    try:
        main(**vars(args))
    except Exception as e:
        logger.error(e)
