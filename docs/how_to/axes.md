# Axes

The Axes tab of the properties section is where users will be able to manage the axes on their plot. From adding/removing axes, hiding axes, or changing an axis' properties, users have plenty of control over the Y-Axes of their plot.

While most X-Axis (timerange) controls should be conducted through the mouse, users can set their time range in the Axes tab as well. This can be done with the 2 datetime widgets at the top of the tab. They can be used to set an absolute date and time for either side of the X-Axis.

Users can control which Y-Axis each curve is attached to from the Traces tab. [More information here](traces.md#trace-properties).



## Adding Axes

Y-Axes should be added automatically, but users can add more as needed using the "Add Axis" button at the bottom of the section. By default, new axes will have these properties:
- Named "Axis #" (where `#` is an incrementing number)
- Oriented to the left
- Auto Range enabled
- Log Mode disabled
- Not Hidden



## Deleting Axes

Users can remove axes by clicking the "Delete Row" button for the given axis in the rightmost column. Deleting an axis will remove the axis from both the table and the plot, as well as all of the traces attached to that axis.



## Hiding Axes

Users have the option to hide/show Y-Axes on the plot using the checkbox in the second to last column. By hiding a Y-Axis, all curves attached to that axis will be hidden as well.
