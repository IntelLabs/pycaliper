

# pycaliper: Specification, Verification, Synthesis for RTL

## Overview

PyCaliper provides infrastructure for verifying and synthesizing specifications for RTL designs based on the Caliper specification language.



## Requirements and Basic Setup

PyCaliper has been developed and tested with Python 3.11. We recommend using a [virtual-environment](https://github.com/pyenv/pyenv). PyCaliper currently requires access to the Jasper FV tool for utilizing its full featureset. However, we are working towards extending full support with open-source tools.

PyCaliper requires a minimal setup.

0. Clone this repository:

```
git clone https://github.com/IntelLabs/pycaliper
```

1. Install all `pip` packages using the `requirements.txt`

```
pip install -r requirements.txt
```
in your venv or
```
python3 -m pip install -r requirements.txt
```
in a non-virtual-environment setup.

2. Update submodules:

```
git submodule update --init --recursive
```

3. (optional) Make sure all tests pass

```
python3 -m unittest tests/test.py
```


## Basic Use


#### Set up the Jasper FV Backend

Launch Jasper with the `jasperserver.tcl` server script
```
include jasperserver.tcl
```
and start the Jasper server (on port 8080)
```
jg_start_server 8080
```

#### PyCaliper Script and Options

Run the `pycmain.py` script:

```
 $ python3 pycmain.py -h
usage: pycmain.py [-h] [-m] [--params PARAMS [PARAMS ...]]
                  [-s SDIR]
                  {verif,persynth,svagen,alignsynth,fullsynth}
                  ... path

Invariant verification and synthesis using Jasper.

positional arguments:
  {verif,persynth,svagen,alignsynth,fullsynth}
    verif               Verify invariants.
    persynth            Synthesize invariants.
    svagen              Generate SVA spec file.
    alignsynth          Synthesize counter alignment.
    fullsynth           Synthesize 1t invariants followed
                        by (cond)equality ones.
  path                  Path to the JSON config file

options:
  -h, --help            show this help message and exit
  -m, --mock            Run in mock mode (without Jasper access)
  --params PARAMS [PARAMS ...]
                        Parameters for the spec module:
                        (<key>=<intvalue>)+
  -s SDIR, --sdir SDIR  Directory to save results to.
```

For example,

```
python3 pycmain.py -m svagen designs/regblock/config.json
```

#### The `config.json` file

The `config.json` file identifies configuration paths and options for backends (e.g., Jasper) and the design. It also identifies the specification file. More details on the specification file below.

## PyCaliper Specifications

PyCaliper specifications are Python classes inheriting from the abstract `Module` class. See examples in `specs/regblock.py`. The class declares signals in its `__init__` function. Further the `input`, `output` and `state` functions define input assumptions, output assertions and state invariants respectively.






## Contributing

The PyCaliper project welcomes external contributions through pull requests to the main branch.

We use pre-commit, so before contributing, please ensure that you run pre-commit and make sure all checks pass with
```
pre-commit install
pre-commit run --all-files
```

Please also run the provided tests and add further tests targetting newly contributed features.

## Feedback

We encourage feedback and suggestions via [GitHub Issues](https://github.com/adwait/pycaliper/issues).
