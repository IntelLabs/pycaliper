import logging

from ..pycmanager import PYConfig

from .. import svagen
from ..jginterface.jgoracle import (
    prove_out_induction_1t,
    prove_out_induction_2t,
    prove_out_bmc,
    loadscript,
    is_pass,
    disable_assm,
    set_assm_induction_1t,
    set_assm_induction_2t,
    set_assm_bmc
)

from .invverifier import InvVerifier

logger = logging.getLogger(__name__)


class JGVerifier1Trace(InvVerifier):
    """One trace property verifier"""

    def __init__(self, pyconfig: PYConfig) -> None:
        super().__init__(pyconfig)
        self.svagen = None

    def verify(self, module) -> bool:
        """Verify one trace properties for the given module

        Args:
            module (Module): Module to verify

        Returns:
            bool: True if the module is safe, False otherwise
        """

        self.svagen = svagen.SVAGen(module)
        self.svagen.create_pyc_specfile(filename=self.psc.pycfile, k=self.psc.k)
        self.candidates = self.svagen.holes

        loadscript(self.psc.script)
        # Disable all holes in the specification
        for cand in self.candidates:
            disable_assm(self.psc.context, cand)
        # Enable the assumptions for 1 trace verification
        set_assm_induction_1t(self.psc.context, self.psc.k)

        res = is_pass(prove_out_induction_1t(self.psc.context))
        res_str = "SAFE" if res else "UNSAFE"
        logger.info(f"One trace verification result: {res_str}")
        return res


class JGVerifier2Trace(InvVerifier):
    """Two trace property verifier"""

    def __init__(self, pyconfig: PYConfig) -> None:
        super().__init__(pyconfig)
        self.svagen = None

    def verify(self, module):
        """Verify two trace properties for the given module

        Args:
            module (Module): Module to verify

        Returns:
            bool: True if the module is safe, False otherwise
        """
        self.svagen = svagen.SVAGen(module)
        self.svagen.create_pyc_specfile(filename=self.psc.pycfile, k=self.psc.k)
        self.candidates = self.svagen.holes

        loadscript(self.psc.script)
        # Disable all holes in the specification
        for cand in self.candidates:
            disable_assm(self.psc.context, cand)
        # Enable the assumptions for 2 trace verification
        set_assm_induction_2t(self.psc.context, self.psc.k)

        res = is_pass(prove_out_induction_2t(self.psc.context))
        res_str = "SAFE" if res else "UNSAFE"
        logger.info(f"Two trace verification result: {res_str}")
        return res

class JGVerifier1TraceBMC(InvVerifier):
    """One trace property verifier with BMC"""

    def __init__(self, pyconfig: PYConfig) -> None:
        super().__init__(pyconfig)
        self.svagen = None

    def verify(self, module):
        """Verify one trace properties for the given module

        Args:
            module (Module): Module to verify

        Returns:
            bool: True if the module is safe, False otherwise
        """

        self.svagen = svagen.SVAGen(module)
        self.svagen.create_pyc_specfile(filename=self.psc.pycfile, k=self.psc.k)
        self.candidates = self.svagen.holes

        loadscript(self.psc.script)
        # Disable all holes in the specification
        for cand in self.candidates:
            disable_assm(self.psc.context, cand)
        # Enable the assumptions for 1 trace verification
        set_assm_bmc(self.psc.context, self.psc.k)

        results = [is_pass(r) for r in prove_out_bmc(self.psc.context, self.psc.k)]
        results_str = '\n\t'.join(
            [f"Step {i}: SAFE" if res else f"Step {i}: UNSAFE" for (i, res) in enumerate(results)])
        logger.info(f"One trace verification result:\n\t{results_str}")
        return results
