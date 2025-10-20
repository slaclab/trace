# Plot Section & Mouse Interaction

<figure markdown="span">
  ![Image of Plot Section](../images/plot_section.png)
</figure>

The plot section is primarily for viewing the plot, but also has some control over the plot's settings.
It displays whatever traces, axes, or other properties the user sets.



## Mouse Controls

The plot's axes can be controlled using the mouse. Users can scroll up to zoom in, or scroll down to zoom out. If this is done over a single axis, then just the one axis is affected.
However, if the user scrolls in the plotting area, then the X-Axis and all Y-Axes will zoom in the corresponding direction.

Users are able to pan along a single axis by clicking and dragging it. This works on both X and Y-Axes.
Clicking and dragging in the plotting area has a different functionality.
A box will be drawn between where the mouse button was pressed and where it was released, and then the plot will zoom in to show the selected range.



## Feedback Form & Documentation Buttons

Above the plotting section are a couple of buttons to assist users in using Trace.

The leftmost button marked with a :material-chat-processing-outline: icon will open a feedback form where users can request features, report bugs, or provide general feedback. The button just to the right with a :octicons-question-16: icon can be used to open the documentation page for Trace.

Both of these actions are also available under the Help menu in the menu bar at the top of the application.



## Time Span Buttons

Above the plotting section are a few buttons for quickly toggling between common time spans (30s, 1m, 1h, 1w, 1M).
Clicking these will cause the plot to consistently update to show that time range.
For instance, toggling the 1h button will result in the last hour of data being shown, and every 5 seconds the plot will shift to the right to update.



## Plot Settings

Users can change the settings of the plot using the settings button in the top left corner of the plot marked with a :octicons-gear-24: icon.
Clicking this button opens a pop-up window with controls over the plot's configuration such as background color, time-range, show gridlines, etc.
