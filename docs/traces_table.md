# Traces Table

The Traces Table, the bread and butter of this application. Type in a PV name into the "Channel" column to add a PV.
There are buttons to change the label, color, and other UI features of the curve.

Right clicking on a row will open a conntext menu with 3 options:

PV search - opens a PV search tool which can help you find your PVs easier.
When searching, you can find similar PVs by using "%", ".", "\*", or "?" as 'wildcard' characters. That means
a search of "KLYS:LI22:\*1:KVAC" will find all PVs that have that channel, with any character in the '\*' slot.
Use ctrl + click to toggle separate PVs as selected or not, and shift + click will select a range of PVs. Click "Add PVs" to append them, or drag/drop them anywhere into the viewer. Double clicking a PV will also add that PV

Formula Dialog - opens a formula input box to type or click buttons to create a custom formula using any number of the existing
curves already in the table. This is purely for aesthetics, as you could also just type "f://" with whatever formula you want

CSV Import - this is a work in progress, but currently does nothing

In addition, users can paste multiple PVs at once into the table in one row's channel box, and it will append them as separate PVs, as long as their names are separated by commas or white space.

::: trace.mixins.traces_table