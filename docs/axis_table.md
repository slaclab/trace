# Axis Table

The Axis Table is where you would manage the Y-axes your curves could be on. You can change their vertical range and change their labels, as well as put them into log mode or hide them.

Move curves onto the axes you want them on from the Traces Table.

Hiding an axis hides all of its connected curves; showing an axis shows all of its connected curves.

Deleting an axis deletes all of its curves. Deleting the last axis resets the whole plot.

Default behavior is that when a PV is added, it will create a new axis with the axis label matching the PV name; but if the PV has units, it will be moved onto an axis with that unit as its label, creating one if such an axis does not exist.

::: trace.mixins.axis_table