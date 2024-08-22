"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: vcdutils.py

    Utilities to read VCD files
"""

import sys
import re
import logging
from dataclasses import dataclass
from collections.abc import MutableMapping

from vcdvcd import VCDVCD

from .per.per import Logic
from .pycmanager import PYConfig


logger = logging.getLogger(__name__)


# A value in the simulation can either be a string (for x or z) or a concrete value
@dataclass
class StateValue:
    val: int
    isx: bool = False


XVALUE = StateValue(0, True)


class Assignment(MutableMapping):
    """Assignment map from signals and values in the simulation"""

    def __init__(self, *args, **kwargs):
        self.assignment: dict[Logic, StateValue] = {}
        self.update(dict(*args, **kwargs))

    def __getitem__(self, s: Logic) -> StateValue:
        if s in self.assignment:
            return self.assignment[s]
        else:
            logger.warn("WARN: signal {} not in assignment".format(s.name))
            return StateValue(0, True)

    def __setitem__(self, s: Logic, v: StateValue):
        self.assignment[s] = v

    def __delitem__(self, s: Logic) -> None:
        del self.assignment[s]

    def __len__(self) -> int:
        return len(self.assignment)

    def __iter__(self):
        return iter(self.assignment)

    def __repr__(self) -> str:
        return str({s.name: v for (s, v) in self.assignment.items()})


def signalstr_to_vcdid(sig: str):
    """Convert a signal string to a VCD string

    Args:
        sig (str): signal string

    Returns:
        str: VCD string
    """
    r = r"([^[]+)\[([0-9]+):([0-9]+)\]"
    gs = re.search(r, sig)
    if gs is not None:
        gs = gs.groups()
        # This is a sliced signal
        return (gs[0], int(gs[1]), int(gs[2]))
    else:
        # This is an unsliced signal
        return (sig, -1, -1)


def autodetect_clock(vcdr: VCDVCD, conf: PYConfig) -> str:
    """Find the clock signal in the VCD file

    Args:
        vcdr (VCDVCD): VCDVCD object read from vcd file

    Returns:
        str: clock signal name
    """
    CLKS = ["clk", "clock"]

    if conf.clk == "":
        # Try autodetecting the clock signal
        vcd_signals = vcdr.references_to_ids.keys()
        matches = [s for s in vcd_signals if any([c in s for c in CLKS])]

        if len(matches) == 0:
            logger.error(
                f"No clock signal auto detected in VCD file, using candidates {CLKS},"
                + " please configure manually!"
            )
            sys.exit(1)
        elif len(matches) > 1:
            logger.debug(
                f"Multiple clock signals detected, using the first one: {matches[0]}."
            )
        conf.clk = matches[0]
    else:
        conf.clk = f"{conf.ctx}.{conf.clk}"
    return conf.clk


def autodetect_clockdelta(vcdr: VCDVCD, conf: PYConfig) -> int:
    """Find the clock signal delta in the VCD file

    Args:
        vcdr (VCDVCD): VCDVCD object read from vcd file

    Returns:
        int: clock timedelta
    """

    clk = autodetect_clock(vcdr, conf)

    # Find frequency
    clkref = vcdr.references_to_ids[clk]
    clktv = vcdr.data[clkref].tv
    # A tv looks like this
    # 'tv': [   (0, '1'),
    #           (5, '0'),
    #           (10, '1'), ... ]
    assert len(clktv) > 1, "Clock signal must have at least two transitions"
    assert (clktv[0][1] == "1" and clktv[1][1] == "0") or (
        clktv[0][1] == "0" and clktv[1][1] == "1"
    ), "Clock signal must be binary and transition between 0 and 1"

    return (clktv[1][0] - clktv[0][0]) * 2


def get_subtrace(
    vcdr: VCDVCD, sigs: list[Logic], rng: range, conf: PYConfig
) -> list[Assignment]:
    """Extract the signals from the vcd trace between the start_cyc and end_cyc (both inclusive)
        This is done only for signals that have counterparts in the design (CSIGs and DSIGs)

    Args:
        vcdr (VCDVCD): VCDVCD object read from vcd file
        sigs (list[Logic]): list of Logic signals
        rng (range): range denoting the time steps to be sampled at
        ctx (str, optional): context string (path to top module). Defaults to ''.

    Returns:
        list[Assignment]: a list of Assignment objects, one for each step in rng
    """
    # Taken from `aul` and simplified by dropping maps/unconstrained signals
    timedelta = autodetect_clockdelta(vcdr, conf)

    vcd_signals = vcdr.references_to_ids.keys()

    frames: list[Assignment] = []
    for i in rng:
        itime = i * timedelta
        frame = Assignment()
        for sig in sigs:
            vcdid = signalstr_to_vcdid(sig.get_sva(conf.ctx))
            # Either vcdid exactly VCD signal name or there is an indexing component
            matches = [
                s for s in vcd_signals if ((vcdid[0] + "[" in s) or (vcdid[0] == s))
            ]
            if len(matches) > 1:
                logger.error(f"More than one signal matches {vcdid[0]}")
                logger.debug(f"Matching signals in VCD: {matches}")
                sys.exit(1)
            elif len(matches) == 0:
                logger.error(f"No signal matches {vcdid[0]}")
                sys.exit(1)
            else:
                basename = matches[0]
                if vcdid[1] != -1:
                    val = (vcdr[basename][itime][::-1])[vcdid[2] : (vcdid[1] + 1)][::-1]
                else:
                    val = vcdr[basename][itime]
            frame[sig] = StateValue(int(("0" + val), 2)) if "x" not in val else XVALUE
        frames.append(frame)
    return frames


def get_subtrace_simple(vcdr: VCDVCD, sigs: list[str], rng: range):
    """Extract signal values from the VCD trace directly from the signal names.

    Args:
        vcdr (VCDVCD): VCDVCD object read from vcd file
        sigs (List[str]): list of signal names to read from the vcd file
        rng (range): range denoting the time steps to be sampled at

    Returns:
        List[Dict[str, Union[int, str]]]: a list of dictionaries,
            representing the memory values at each point
    """
    frames = []
    for i in rng:
        frame = {}
        for sig in sigs:
            val = vcdr[sig][i]
            frame[sig] = int(val, 2) if ("x" not in val and "z" not in val) else val
        frames.append(frame)
    return frames
