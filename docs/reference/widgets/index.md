# Widgets

This section documents the customized PyQt/PyDM widgets used throughout Trace. These components wrap common workflows (plot configuration, data exploration, archiver search, and E-Log posting) with a consistent API and theme-aware UI.


### What you'll find
- **Control Panel**: Main sidebar for managing curves, axes, and plot actions. See [Control Panel].
- **Data Insight Tool**: Explore, aggregate, and compare PV data interactively. See [Data Insight Tool].
- **Archive Search**: Query the EPICS Archiver Appliance for PVs and add results to the plot. See [Archive Search].
- **Settings popups**: Modals and components for plot settings, axis settings, and curve customization. See [Settings popups].
- **E-Log Post Modal**: Capture the current plot and post entries to the E-Log. See [E-Log Post Modal].
- **Helper widgets**: Reusable building blocks (e.g., color pickers, frozen table views, toggle buttons). See [Helper widgets].

  [Control Panel]: ./control_panel.md
  [Data Insight Tool]: ./data_insight_tool.md
  [Archive Search]: ./archive_search.md
  [Settings popups]: ./settings_popups.md
  [E-Log Post Modal]: ./elog_post_modal.md
  [Helper widgets]: ./helper_widgets.md


## Getting started

```python
from trace.widgets import ControlPanel, DataInsightTool

# Example: attaching the control panel to an existing PyDMArchiverTimePlot
control_panel = ControlPanel(theme_manager=theme_manager)
control_panel.plot = pydm_archiver_time_plot
```


## Additional reference

For standard Qt widget behavior, refer to `QWidget` in the Qt for Python docs found [here].

  [here]: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html
