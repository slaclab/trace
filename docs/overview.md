# Overview

Trace is a PyDM application used to plot value data for given PVs. The application is capable of plotting both live and archived data, as well as [formulas](traces.md#formula-traces) containing PVs as variables.

The top of the application shows a few buttons for quickly toggling between common time spans (30s, 1m, 1h, 1w, 1M). Below that the application is split into two main parts:
- Plot section
- Properties section

Users are able to control the size of these two sections by clicking and dragging the horizontal gray splitter in the center of the application. The properties section can be completely collapsed so that the application only shows the plot.



## Plot Section & Mouse Interaction

The plot section shows the plot. It displays whatever traces, axes, or other properties the user sets on it.

The plot's axes can be controlled using the mouse. Users can scroll up to zoom in, or scroll down to zoom out. If this is done over a single axis, then just the one axis is affected. However, if the user scrolls in the plotting area, then the X-Axis and all Y-Axes will zoom in the corresponding direction.

Users are able to pan along a single axis by clicking and dragging it. This works on both X and Y-Axes. Clicking and dragging in the plotting area has a different functionality. A box will be drawn between where the mouse button was pressed and where it was released, and then the plot will zoom in to show the selected range.



## Properties Section

The properties section is split into 3 different tabs:
- [Traces](traces.md)
- [Axes](axes.md)
- [Plot](plot_config.md)

Each of these tabs allow the user to set the properties for the given topic. More details can be found in their respective how to article.



## Footer

At the very bottom of the screen is a footer containing some information that may be useful to users. There is also a logger displayed at the bottom, which can show what actions are being performed.

The left side displays (left to right) the application's:
- Current release tag
- Node running it
- User running it
- PID
- Archiver URL being used to fetch archiver data

The right side displays the current date and time, which can be useful when reviewing screenshots.
