# Input Arguments & Macros

Trace supports several optional startup arguments and macros that allow users to customize its behavior at launch. These arguments let you specify input files, define process variables (PVs) to display, apply macro replacements, and access help or version information.

Below, you'll find a detailed overview of each available argument and example usage to help you configure Trace to fit your workflow.


## Config File

`-i INPUT_FILE` or `--input_file INPUT_FILE`

This argument allows users to [import] Trace config files, providing a way to recover a previous state of Trace. To make use of it, users should provide a filepath for the config file they want to use. The path can be either relative or absolute.

  [import]: io.md

``` bash
pydm trace/main.py -i trace/examples/FormulaExample.trc
```


## Startup PVs

`-p PV1 PV2 ...` or `--pvs PV1 PV2 ...`

Users are able to provide a list of PVs to show traces for on startup. Each PV passed here will be represented by a curve on the plot.

``` bash
pydm trace/main.py -p FOO:BAR:CHANNEL SOME:OTHER:CHANNEL
```


## Macros

`-m MACRO` or `--macro MACRO`

Use PyDM's [macro substitution] system as another way of adding PVs or startup files to Trace. Adding PVs via macros is equivalent to adding them as an argument. This setup allows users to add traces from other PyDM widgets, such as the [PyDMRelatedDisplayButton].

  [macro substitution]: https://slaclab.github.io/pydm/tutorials/intro/macros.html
  [PyDMRelatedDisplayButton]: https://slaclab.github.io/pydm/widgets/related_display_button.html

``` bash
pydm trace/main.py -m '{"PVS": ["FOO:BAR:CHANNEL", "SOME:OTHER:CHANNEL"]}'
pydm trace/main.py -m "INPUT_FILE = trace/examples/FormulaExample.trc"
```


## Help Message

`-h` or `--help`

Shows Trace's help message, which outlines the available arguments for users.


## Version Number

`-v` or `--version`

Show Trace's current version/release number.
