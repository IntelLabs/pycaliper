"""
    Synthesis for equality invariants using Jasper FV Interface
"""

import logging

from ..pycmanager import PYConfig

from ..per import Module, PERHole, Context

from pycaliper.svagen import SVAGen
from pycaliper.jginterface.jgoracle import (
    prove,
    prove_out_2t,
    enable_assm_2t,
    is_pass,
    enable_assm,
    disable_assm,
    loadscript,
)


logger = logging.getLogger(__name__)


class SynthesisTree:

    counter = 0
    MAXFUEL = 3

    def __init__(self, asrts=[], assms=[], parent=None, inherits=None):
        self.children: dict[str, SynthesisTree] = {}
        self.parent = parent
        self.inherits = inherits
        self.secondaries = []

        self.asrts: list[str] = list(asrts)
        self.assms: list[str] = assms + ([inherits] if inherits is not None else [])

        self.fuel = SynthesisTree.MAXFUEL - len(self.assms) + len(self.asrts)

        self.id = SynthesisTree.counter
        SynthesisTree.counter += 1

        self.checked = False

    def add_child(self, cand):
        self.children[cand] = SynthesisTree(self.asrts, self.assms, self, cand)

    def add_asrt(self, asrt):
        self.asrts.append(asrt)
        self.fuel += 1

    def add_secondary_assm(self, assm):
        if assm not in self.assms:
            self.assms.append(assm)
            self.fuel -= 1
            self.secondaries.append(assm)
            return True
        return False

    def is_self_inductive(self):
        return set(self.assms) == set(self.asrts)

    def __str__(self) -> str:
        return f"synnode::{self.id}(fuel={self.fuel})"


class PERSynthesizer:
    def __init__(self, psconf: PYConfig) -> None:
        self.psc = psconf
        self.svagen = None
        self.candidates: dict[str, PERHole] = {}

        self.depth = 0
        self.minfuel = SynthesisTree.MAXFUEL

        self.synstate: SynthesisTree = SynthesisTree()

    def _saturate(self):
        added = True
        while added:
            added = False
            for cand in self.candidates:
                if cand not in self.synstate.asrts:
                    if is_pass(prove(self.psc.context, cand)):
                        added = True
                        self.synstate.add_asrt(cand)
                        if self.synstate.add_secondary_assm(cand):
                            enable_assm(self.psc.context, cand)
                        logger.debug(f"Added assertion {cand} to synthesis node")
                        break

    def _dive(self, cand):
        self.synstate.add_child(cand)
        self.synstate = self.synstate.children[cand]
        logger.debug(f"Dived to new state: {self.synstate} on candidate: {cand}")
        self.depth += 1
        enable_assm(self.psc.context, cand)
        logger.debug(
            f"Saturating curr. synstate: {self.synstate}, with assms: {self.synstate.assms}"
        )
        self._saturate()
        self.minfuel = min(self.minfuel, self.synstate.fuel)
        logger.debug(
            f"Saturated curr. synstate: {self.synstate}, new assrts: {self.synstate.asrts}"
        )

    def _backtrack(self):
        if self.synstate.parent is not None:
            cand = self.synstate.inherits
            secondaries = self.synstate.secondaries
            self.synstate = self.synstate.parent
            logger.debug(
                f"Backtracked to state: {self.synstate} on "
                + f"inheritance: {cand}, and secondaries: {secondaries}"
            )
            for c in [cand] + secondaries:
                disable_assm(self.psc.context, c)
            self.depth -= 1
            return True
        else:
            logger.warn(
                f"Cannot backtrack from root state. Synthesis failed: {self.synstate}"
            )
            return False

    def safe(self):
        if not self.synstate.checked:
            self.synstate.checked = True
            return is_pass(prove_out_2t(self.psc.context))
        return False

    def _synthesize(self):
        while True:
            if self.synstate.is_self_inductive():
                if self.safe():
                    # Done
                    logger.debug(
                        f"Synthesis complete. Found invariant: {self.synstate.asrts}"
                    )
                    return self.synstate.asrts
                else:
                    unexplored_cands = [
                        cand
                        for cand in self.candidates
                        if cand not in self.synstate.children
                        and cand not in self.synstate.assms
                    ]
                    if unexplored_cands == []:
                        return None
                    else:
                        cand = unexplored_cands[0]
                        self._dive(cand)
            else:
                unexplored_cands = [
                    cand
                    for cand in self.candidates
                    if cand not in self.synstate.children
                    and cand not in self.synstate.assms
                ]
                # TODO: also use fuel
                if unexplored_cands == []:
                    if not self._backtrack():
                        return None
                else:
                    cand = unexplored_cands[0]
                    self._dive(cand)

    def synthesize(self, topmod: Module) -> Module:
        # Create a new SVA generator
        self.svagen = SVAGen(topmod)
        self.svagen.create_pyc_specfile(k=self.psc.k, filename=self.psc.pycfile)
        self.candidates = self.svagen.holes

        loadscript(self.psc.script)

        # Enable and disable the right assumptions
        for cand in self.candidates:
            disable_assm(self.psc.context, cand)
        enable_assm_2t(self.psc.context)

        invs = self._synthesize()

        if invs is None:
            # Synthesis failed
            logger.warn("Invariant synthesis failed.")

        else:
            logger.info(
                f"Synthesized invariants: {invs} at depth: {self.depth} and minimum fuel: {self.minfuel}"
            )

            # Disable all eq holes
            for c in topmod._perholes:
                c.deactivate()
            for inv in invs:
                topmod._eq(self.candidates[inv], Context.STATE)

        return topmod
