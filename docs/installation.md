# Installation

## Prerequisites
- Python 3.12 or newer
- pip (Python package manager)
- (Optional) conda for environment management


## Clone the Repository

``` bash
git clone https://github.com/slaclab/trace.git
```


## Create and Activate a Virtual Environment (Recommended)

Using `venv`:
``` bash
python3 -m venv .venv
source .venv/bin/activate
```

Or using `conda`:
``` bash
conda env create -f environment.yml
conda activate trace
```


## Install Dependencies

If using pip:
``` bash
pip install -r requirements.txt
```

Or with `conda` (if you created the environment above, dependencies are already installed):
``` bash
conda env update -f environment.yml
```


## Running Trace

The main startup file for trace is located at `trace/main.py`.

Trace can be launched using PyDM, and users can pass in additional [arguments and macros].

  [arguments and macros]: arguments.md

``` bash
pydm trace/main.py
```