import os
import sys
import logging
import random
from enum import Enum

import tempfile
import importlib

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from pycaliper.jginterface import jasperclient as jgc
from pycaliper.jginterface.jgoracle import setjwd

from pydantic import BaseModel

from .per.per import Module

logger = logging.getLogger(__name__)


class PYCTask(Enum):
    SVAGEN = 0
    VERIF1T = 1
    VERIF2T = 2
    VERIFBMC = 3
    CTRLSYNTH = 4
    PERSYNTH = 5
    FULLSYNTH = 6


class PYCArgs(BaseModel):
    path: str
    mock: bool = False
    params: str = ""
    sdir: str = ""
    port: int = 8080
    onetrace: bool = False
    bmc: bool = False


class PYConfig(BaseModel):
    """PyCaliper configuration class"""

    # Is this a mock run (without Jasper access)?
    mock: bool = False

    # Working directory
    # wdir : str = ""
    # Saving directory
    sdir: str = ""

    # Jasper directory (relative to pycaliper dir)
    jdir: str = ""
    # Script to load in Jasper (relative to Jasper dir)
    script: str = ""
    # Verification context to use in Jasper
    context: str = ""
    # PyCaliper SVA filepath to use (relative to pycaliper dir)
    pycfile: str = ""

    # Specification location
    pycspec: str = ""
    # bound to use for the k-inductive proof
    k: int = 1
    # Use only one trace for verification
    onetrace: bool = False

    # Directory of pre-provided traces
    tdir: str = ""
    # What is the property to generate traces?
    tgprop: str = ""
    # VCD trace configuration elements
    # Clock signal name
    clk: str = ""
    # Simulation top level module in overall hierarchy
    ctx: str = ""


class PYCManager:
    def __init__(self, pyconfig: PYConfig):
        self.pycspec: str = pyconfig.pycspec
        # Previous VCD traces directory

        self.pyconfig = pyconfig
        self.sdir = pyconfig.sdir

        # Create a temporary directory for the run, grab the name, and clean it up
        wdir = tempfile.TemporaryDirectory(prefix="pyc_wdir_")
        self.wdir = wdir.name
        wdir.cleanup()

        logger.info(f"Working directory: {self.wdir}")
        self.tracedir = f"{self.wdir}/traces"
        self.specdir = f"{self.wdir}/specs"

        # Create the directories
        os.makedirs(self.tracedir, exist_ok=True)
        os.makedirs(self.specdir, exist_ok=True)

        self.num_vcd_files = 0
        self.traces = {}

        self.num_spec_files = 0
        self.specs = {}

        if pyconfig.tdir != "":
            self.gather_all_traces(pyconfig.tdir)

    def gather_all_traces(self, tdir):
        # Collect all vcd files in the directory (non-subdirs) at wdir
        for f in os.listdir(tdir):
            if f.endswith(".vcd"):
                # Copy the trace to tracedir
                os.system(f"cp {tdir}/{f} {self.tracedir}")
                self.traces[self.num_vcd_files] = f"{self.tracedir}/{f}"
                self.num_vcd_files += 1

    def create_vcd_path(self):
        path = f"{self.tracedir}/trace{self.num_vcd_files}.vcd"
        self.traces[self.num_vcd_files] = path
        self.num_vcd_files += 1
        return path

    def get_vcd_path(self, idx):
        return self.traces[idx]

    def get_vcd_path_random(self):
        if self.num_vcd_files == 0:
            logger.warn(f"No VCD files found in directory {self.tracedir}.")
            return None
        return self.traces[random.randint(0, self.num_vcd_files - 1)]

    def save_spec(self, module: Module):
        # Create path
        path = f"{self.specdir}/{self.pycspec}.spec{self.num_spec_files}.py"
        self.specs[self.num_spec_files] = path
        self.num_spec_files += 1

        with open(path, "x") as f:
            f.write(module.full_repr())

        logger.info(f"Specification written to {path}.")

    def save(self):
        if self.sdir != "":
            # Copy wdir to sdir
            os.system(f"cp -r {self.wdir}/. {self.sdir}/")

    def close(self):
        # Close the socket
        self.save()
        if not self.pyconfig.mock:
            jgc.close_tcp()
        logger.info("PyCaliper run completed, socket closed.")


CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "jasper": {
            "type": "object",
            "properties": {
                # The Jasper working directory relative to the pycaliper directory
                "jdir": {"type": "string"},
                # The TCL script relative to the Jasper working directory
                "script": {"type": "string"},
                # Location of the generated SVA file relative to the Jasper working directory
                "pycfile": {"type": "string"},
                # Proof node context
                "context": {"type": "string"},
            },
            "required": ["jdir", "script", "pycfile", "context"],
        },
        "spec": {
            "type": "object",
            "properties": {
                # Location of the specification file
                "pycspec": {"type": "string"},
                # k-induction
                "k": {"type": "integer"},
                "params": {"type": "object"},
            },
            "required": ["pycspec", "k"],
            "additionalProperties": False,
        },
        "trace": {
            "type": "object",
            "properties": {
                # Where should traces be stored
                "tdir": {"type": "string"},
                # What is the property used for trace generation
                "tgprop": {"type": "string"},
                # Clock signal name
                "clk": {"type": "string"},
                # What is the hierarchical top module
                "topmod": {"type": "string"},
            },
            "required": ["tdir", "tgprop", "topmod"],
        },
    },
    "required": ["jasper", "spec"],
}


def create_module(specc, args):
    """Dynamically import the spec module and create an instance of it."""
    specmod: str = specc["pycspec"]
    params = specc.get("params", {})

    parsed_conf = {}
    for pair in args.params:
        key, value = pair.split("=")
        parsed_conf[key] = int(value)

    params.update(parsed_conf)

    if "/" in specmod:
        # Split the module name into the module name and the parent package
        module_path, module_name = specmod.rsplit("/", 1)

        # Check if the path exists
        if not os.path.isdir(module_path):
            logger.error(f"Path '{module_path}' does not exist.")
            exit(1)
        # Add the module path to sys.path
        sys.path.append(module_path)

        try:
            if "." in module_name:
                module_name, class_name = module_name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                logger.debug(
                    f"Successfully imported module: {module_name} from {module_path}"
                )
                return getattr(module, class_name)(**params)
            else:
                # Import the module using importlib
                module = importlib.import_module(module_name)
                logger.debug(
                    f"Successfully imported module: {module_name} from {module_path}"
                )
                return getattr(module, module_name)(**params)
        except ImportError as e:
            logger.error(
                f"Error importing module {module_name} from {module_path}: {e}"
            )
            return None
        finally:
            # Clean up: remove the path from sys.path to avoid potential side effects
            sys.path.remove(module_path)

    else:
        mod = importlib.import_module(f"specs.{specmod}")
        return getattr(mod, specmod)(**params)


def mock_or_connect(pyconfig: PYConfig, port: int) -> bool:
    if pyconfig.mock:
        logger.info("Running in mock mode.")
        return False
    else:
        jgc.connect_tcp("localhost", port)
        setjwd(pyconfig.jdir)
        return True


def get_pyconfig(config, args: PYCArgs) -> PYConfig:
    jasperc = config.get("jasper")
    specc = config.get("spec")
    tracec = config.get("trace", {})

    return PYConfig(
        # Is this a mock run
        mock=args.mock,
        # Working directory
        # wdir=wdir.name,
        sdir=args.sdir,
        # Jasper configuration
        jdir=jasperc["jdir"],
        script=jasperc["script"],
        context=jasperc["context"],
        pycfile=f'{jasperc["jdir"]}/{jasperc["pycfile"]}',
        # Spec config
        pycspec=specc["pycspec"],
        k=specc["k"],
        onetrace=args.onetrace,
        # Tracing configuration
        # Location where traces are provided
        tdir=tracec.get("tdir", ""),
        tgprop=tracec.get("tgprop", ""),
        clk=tracec.get("clk", ""),
        ctx=tracec.get("topmod", ""),
    )


def start(task: PYCTask, args: PYCArgs) -> tuple[PYConfig, PYCManager, Module]:

    with open(args.path, "r") as f:
        config = json.load(f)

    try:
        validate(instance=config, schema=CONFIG_SCHEMA)
    except ValidationError as e:
        logger.error(f"Config schema validation failed: {e.message}")
        logger.error(
            f"Please check schema:\n{json.dumps(CONFIG_SCHEMA, indent=4, sort_keys=True, separators=(',', ': '))}"
        )
        sys.exit(1)

    pyconfig = get_pyconfig(config, args)

    tmgr = PYCManager(pyconfig)

    module = create_module(config.get("spec"), args)
    assert module is not None, f"Module {config.get('spec')['pycspec']} not found."

    is_connected = mock_or_connect(pyconfig, args.port)

    match task:
        case PYCTask.VERIF1T | PYCTask.VERIF2T | PYCTask.PERSYNTH | PYCTask.CTRLSYNTH:
            if not is_connected:
                logger.error(
                    f"Task {task} requires Jasper sockets, cannot be run in mock mode."
                )
                sys.exit(1)
        case _:
            pass

    return pyconfig, tmgr, module
