import logging
import sys
from vcdvcd import VCDVCD

from ..per import Module, CtrAlignHole, Logic, Context

from ..pycmanager import PYConfig
from ..vcdutils import get_subtrace
from ..pycmanager import PYCManager

from ..jginterface.jgoracle import prove, is_pass, create_vcd_trace

from .synthprog import ZDDLUTSynthProgram

logger = logging.getLogger(__name__)


class AlignSynthesizer:
    def __init__(self, tmgr: PYCManager, pyconf: PYConfig) -> None:
        self.pyconf = pyconf
        self.tmgr = tmgr
        # Top module
        self.topmod = None

    def _sample_tracepath(self) -> str:
        """Generate a simulation VCD trace from the design

        Returns:
            str: path to the generated VCD trace
        """
        if self.pyconf.mock or self.pyconf.tgprop == "":
            logger.info(
                "Mock mode enabled/tgprop unspecified, no new traces will be generated, replaying old traces."
            )
            vcd_path = self.tmgr.get_vcd_path_random()
            if vcd_path is None:
                logger.error("No traces found.")
                sys.exit(1)
            return vcd_path

        # Check property
        res = prove(self.pyconf.tgprop)
        if is_pass(res):
            logger.error("Property is SAFE, no traces!")
            sys.exit(1)

        # Grab the trace
        vcd_path = self.tmgr.create_vcd_path()
        res = create_vcd_trace(self.pyconf.tgprop, vcd_path)
        logger.debug(f"Trace generated at {vcd_path}.")

        return vcd_path

    def _inspect_module(self) -> bool:
        """Inspect the module for well-formedness

        Checks whether:
            (a) all signals in holes are single bit logic signals and
            (b) no two holes have common signals.

        Returns:
            bool: True if module is well-formed, False otherwise
        """
        caholes = self.topmod._caholes
        holesigs = [set(h.sigs) for h in caholes]

        for i in range(len(caholes)):
            ch = caholes[i]
            if not all([isinstance(s, Logic) and s.width == 1 for s in ch.sigs]):
                logger.error(f"Non single bit-logic signal found in chole: {ch}.")
                return False

            for j in range(i + 1, len(caholes)):
                if holesigs[i].intersection(holesigs[j]):
                    logger.error(
                        f"Signals in holes {i} and {j} are not disjoint, found \
                        intersection {holesigs[i].intersection(holesigs[j])}"
                    )
                    return False

        return True

    def _synthesize_cahole(self, cahole: CtrAlignHole):
        logger.debug(f"Attempting synthesis for hole {cahole}")

        vcdfile = self._sample_tracepath()
        vcdobj: VCDVCD = VCDVCD(vcdfile)

        intsigs = [cahole.ctr] + cahole.sigs
        # TODO: range should be a parameter
        trace = get_subtrace(vcdobj, intsigs, range(0, 16), self.pyconf)

        for s in cahole.sigs:
            zddsp = ZDDLUTSynthProgram(cahole.ctr, s)

            # Filter out assignments that have X
            filtered = [
                (assn[cahole.ctr].val, assn[s].val)
                for assn in trace
                if not (assn[cahole.ctr].isx or assn[s].isx)
            ]

            logger.debug(
                f"Filtered assignments for ctr {cahole.ctr} and s {s}: {filtered}"
            )

            ctr_vals = [f[0] for f in filtered]
            out_vals = [f[1] for f in filtered]
            zddsp.add_entries(ctr_vals, out_vals)

            if zddsp.solve():
                logger.info(
                    f"Solution found for hole {cahole}. Adding as an invariant."
                )

                # Disable the hole
                cahole.deactivate()

                inv = zddsp.get_inv()
                self.topmod._inv(inv, Context.STATE)
            else:
                logger.info(f"No solution found for hole {cahole}.")

    def synthesize(self, module: Module) -> Module:

        self.topmod = module

        self.topmod.instantiate()
        if not self._inspect_module():
            logger.error(
                "Module holes are not well-formed for AlignSynth, please check log. Exiting."
            )
            sys.exit(1)

        for h in self.topmod._caholes:
            self._synthesize_cahole(h)

        return self.topmod
