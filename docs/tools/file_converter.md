# CLI File Converter Tool

Included in this application is a tool for converting files from the Archive Viewer's format or StripTool's format into Trace's format.

It is located at `trace/file_io/trace_file_converter.py` and can be called directly from the command-line.
This allows users to convert their files without having to open Trace.



## Help Message

``` bash
trace/file_io/trace_file_convert.py --help
>  usage: Trace File Converter [-h] [--output_file [OUTPUT_FILE ...]]
>                              [--overwrite] [--clean]
>                              [input_file ...]
>
>  Convert files used by the Java Archive Viewer or StripTool to a file format
>  that can be used with Trace.
>
>  positional arguments:
>    input_file            Path to the file(s) to be converted
>
>  options:
>    -h, --help            show this help message and exit
>    --output_file [OUTPUT_FILE ...], -o [OUTPUT_FILE ...]
>                          Path to the output file(s) (defaults to input file
>                          name); The number of output_files must match the
>                          number of input_files if any are provided
>    --overwrite, -w       Overwrite the target file if it exists
>    --clean               Remove the input file after successful conversion
```


## Positional Arguments

### Input File

``` bash
trace_file_convert.py examples/xml_conversion.xml
```

``` bash
trace_file_convert.py stp_files/*.stp
```

The only positional argument is the file to be converted, labeled `input_file`.
This should be provided as a path to the file, either relative or absolute.
Users can also provide multiple files to be converted at once.

If any file(s) fail the conversion, individual error messages are provided so that users know which to look at.
Some causes of failure are:

- The file does not exist
- The file does not use the `.xml` or `.stp` file extension
- The file is incorrectly formatted


## Optional Arguments

### Output File

`-o OUTPUT_FILE` or `--output_file OUTPUT_FILE`

``` bash
python trace_file_convert.py xml_conversion.xml -o xml_conversion.trc
```

Users can use this argument to pass the name and path the converted file should be saved as.
If not provided, the converter defaults to the name of the input file with the `.trc` file extension.

Users don't need to include a file extension for the output file name.
The conversion fails if the provided output file name has a file extension and it is not `.trc`.

If converting a batch of files, the user can provide multiple output file names to use.


### Overwrite

`-w` or `--overwrite`

The conversion will fail if a file already exists with the new file name (provided or default).
Using the overwrite flag ignores the interrupt, allowing the tool to replace the existing file with the new file.

``` bash
python trace_file_convert.py xml_conversion.xml -o xml_conversion.trc

>  [ERROR] - Failed: xml_conversion.xml --> xml_conversion.trc:
>    Output file exists but overwrite not enabled: /path/to/xml_conversion.trc

python trace_file_convert.py xml_conversion.xml -o xml_conversion.trc -w
```


### Clean

`--clean`

This flag results in the conversion tool removing the input file after the conversion has been made.

``` bash
python trace_file_convert.py examples/FormulaExample.trc --clean
```
