# Import and Export

Trace allows users to export their current configuration of the application into a save file so that it can be imported later. The exported files include the archiver URL used, plot's configuration, the X-axis' time range, all of the Y-axes, and all of the traces.

The importing and exporting features can be found in the menu bar at the top of the application under the Action menu. Alternatively, users can export their current configuration with `Ctrl+S` or import a file with `Ctrl+L`.

Files can also be imported on startup using the `-i` flag followed by the path to the file. Find more information on application arguments [here](../api_reference/trace.md#arguments-and-macros).



## Save Files

Trace's save files are in JSON format as to be human readable/writeable and they use their own file extension: `.trc`.


### Java Save Files

Save files for the Java-based Archive Viewer can also be imported into Trace. They are hidden in the file explorer by default. To show them, click the dropdown at the bottom of the file explorer dialog labeled `Files of type:` and select the option for `Java Archive Viewer (*.xml)`. Now you should be see only directories and `.xml` files.

Trace will not save new files in the Java-based Archive Viewer's format, only as `.trc` files.

Files can be converted en masse from the Java-based file format to Trace's formate using the [CLI file converter tool](file_conversion.md).


### Note About Colors

Colors in the save file will typically be represented as RGB values in hexidecimal format. Since the string will be passed into a QColor when loaded, these strings can be names of colors as well e.g. "red", "blue", "white", etc.