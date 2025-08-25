# Traces

Traces, sometimes called curves, are the lines that are shown on the application's plot. They show both live and archive data for the given channel.

The properties of each trace can be controlled by the user in the application's traces table, which can be found by navigating to the properties section of the app and selecting the tab labeled "Traces". This tab will be shown by default.



## Formula Traces

Users can add formulas to the plot by entering their formula to be calculated as the trace's channel. The formula should be prepended with "f://" to signify that the channel is a formula. Formulas can also be added using the [formula input tool](traces_table_menu.md#formula).

Other traces the formula uses are represented by their unique row header in a set of curly brackets, e.g. {A}, {X}, {AV}. Formulas can include all basic arithmetic and binary operations, as well as `mean` and all functions in Python's [standard math library](https://docs.python.org/library/math.html).

As an example, if we have some 2 PVs with the row headers A and B, then we may have the formula `f://{A} + {B}` or maybe `f://min({A}, {B})` or `f://{A} ^ {B}`.



## Adding Traces

Users can add traces to the plot by including them in the traces table. This can be done by entering a channel into the last row, which should always be empty. Once a channel is included, the trace should be added to the plot and both live and archived data will be shown. Traces can also be added using the [PV Search tool](traces_table_menu.md#search-pv)

In addition, users can paste multiple PVs at once into the table in one row's channel box, and it will append them as separate PVs, as long as their names are separated by commas or white space.

When adding new traces, they will be attached to a y-axis with the same unit. If no such axis exists, a new one will be created for the channel's unit. If the channel has no units, a new axis will be created with no associated units.



## Removing Traces

Traces can be removed by the user by clicking the "Delete Row" button for the given trace entry in the rightmost column. This will remove the row from the table and remove the trace from the plot in one swift motion.



## Trace Properties
### Channel

Setting a trace's channel is necessary for the trace to exist. This is the data source that the trace will represent. This is also the section where a user can add a formula. More details can be found [above](#formula-traces).


### Live Data & Archive Data

The user can determine what kind of data should be fetched. Live data will be added to the trace on the channel's value change. If Live data fetching is disabled and then later reenabled, then archiver data will be fetched to backfill the missing section. By default, both Live data and Archive data fetching are enabled.


### Label

The string the curve should be represented as on the axes and in the legend. Defaults to the channel name.


### Color

The color the curve should show up as on the plot. Sets the color for the trace and its symbols. Clicking this button will open the default PyQT color selector dialog window. Once the color has been changed, right clicking the button will set it back to its initial color.


### Y-Axis Name

A dropdown menu of all of the y-axes on the plot. This allows the user to determine which axis the trace should be attached to. Defaults to y-axis containing curves with the same unit if one exists. If there is no such y-axis, then a new axis will be created.


### Style

A dropdown menu containing 2 options: Direct and Step. The direct style draws sloped lines directly between points on the plot. The step style draws the trace as horizontal lines to the right of their points and continue until a new point on the plot.


### Line Style & Line Width

Controls the style and size of the trace on the plot. The styles include no line, solid (-----), dash (- - -), dot (...), dash dot (-.-.-), and dash dot dot (-..-..). The widths are limited to 1px - 5px, with 1px being the default.


### Symbol & Symbol Size

Controls what symbols should be shown at each point on the trace. By default no symbols are shown, but users have many shapes they can choose from including circles, triangles, squares, etc. Users can also choose the size of the symbol at 5px, 10px, 15px, or 20px with 10px being the default.


### Hidden

Users can choose if they want individual traces to be shown/hidden on the plot. If all of the curves for a given axis are hidden, then the axis will be hidden as well.
