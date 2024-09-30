# Import and Export

Trace allows users to export their current configuration of the application into a save file so that it can be imported later. The exported files include the archiver URL used, plot's configuration, the X-axis' time range, all of the Y-axes, and all of the traces.

The importing and exporting features can be found in the menu bar at the top of the application under the Action menu. Alternatively, users can export their current configuration with `Ctrl+S` or import a file with `Ctrl+L`.

Files can also be imported on startup using the `-i` flag followed by the path to the file. Find more information on application arguments [here](../api_reference/trace.md#arguments-and-macros).



## Save Files

Trace's save files are in JSON format as to be human readable/writeable and they use their own file extension: `.trc`.


### Java Save Files

Save files for the Java-based Archive Viewer can also be imported into Trace. They can be found in the import tool's file selection tool along with Trace's save files. Users can show only Java Archive Viewer files by changing the file format filter at the bottom of the dialog window.

Trace will not save new files in the Java-based Archive Viewer's format, only as `.trc` files.

Files can be converted en masse from the Java-based file format to Trace's formate using the [CLI file converter tool](file_conversion.md).


### StripTool Save Files

Save files for the StripTool can be converted using the same tool or imported directly into Trace. They can be found in the import tool's file selection tool alongside Trace's save files and the Java Archive Viewer's save files. Users can show only StripTool files by changing the file format filter at the bottom of the dialog window.

Trace will not save new files in the Java-based Archive Viewer's format, only as `.trc` files.

Files can be converted en masse from the StripTool file format to Trace's formate using the [CLI file converter tool](file_conversion.md).


### Note About Colors

Colors in the save file will typically be represented as RGB values in hexidecimal format. Since the string will be passed into a QColor when loaded, these strings can be names of colors as well e.g. "red", "blue", "white", etc.