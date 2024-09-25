# CLI File Converter Tool

Included in this application is a tool for converting files from the Archive Viewer's format into Trace's format. The tool can be found at `trace/trace_file_converter.py` and can be called directly from the command-line. This allows users to convert their files without having to open Trace.



## Usage

`trace_file_convert.py [-h] [--output_file OUTPUT_FILE] [--overwrite] [--clean] input_file`

The file converter tool takes in a few optional arguments to give the user more control over how they use it.


### Positional Arguments

#### Input File

The only positional argument is the file to be converted, labeled `input_file`. This should be provided as a path to the file, either relative or absolute. The conversion will fail if the file does not exist or does not use the `.xml` file extension or if it's incorrectly formatted.

Example: `python trace_file_convert.py examples/FormulaExample.trc`


### Optional Arguments

#### Output File: -o, --output_file

Users can use this argument to pass the name and path the converted file should be saved as. If not provided, the new file will be the same as the input file. A file extension does not need to be provided in the new name. The conversion fails if the provided output file name has a file extension and it is not `.trc`.

Example: `python trace_file_convert.py examples/FormulaExample.trc -o some_file.trc`


#### Overwrite: -w, --overwrite

The conversion will fail if a file already exists with the new file name (provided or default). Using the overwrite flag ignores the interrupt, allowing the tool to replace the existing file with the new file.

Example: `python trace_file_convert.py examples/FormulaExample.trc -o some_file.trc -w`


#### Clean: --clean

This flag results in the conversion tool removing the input file after the conversion has been made.

Example: `python trace_file_convert.py examples/FormulaExample.trc --clean`
