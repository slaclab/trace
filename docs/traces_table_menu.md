
# Context Menu

Right clicking anywhere on the table (except for the color selector button) will open up the table's menu. This menu has 3 options: Search PV, Formula, and Import CSV.



## Search PV

Opens a PV search tool which can help you find your PVs easier.

When searching, you can find similar PVs by using "%", ".", "\*", or "?" as 'wildcard' characters. That means
a search of `KLYS:LI22:\*1:KVAC` will find all PVs that have that channel, with any character in the "\*" slot.

Use ctrl + click to toggle separate PVs as selected or not, and shift + click will select a range of PVs. Click the "Add PVs" button to append them to the traces table, or drag/drop them anywhere into the viewer. Double clicking a PV will also add that PV.



## Formula

Opens a formula input box to type or click buttons to create a custom [formula trace](traces.md#formula-traces) using any number of the existing curves already in the table. This is for ease of use, as you could also type "f://" followed by your formula to enter enter it as a trace.



## Import CSV

This is a work in progress, but currently does nothing.
