import logging

from ..pycmanager import PYConfig

from .. import svagen
from ..jginterface.jgoracle import (
    prove_out_1t,
    prove_out_2t,
    loadscript,
    is_pass,
    disable_assm,
    enable_assm_1t,
    enable_assm_2t,
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
        enable_assm_1t(self.psc.context)

        res = is_pass(prove_out_1t(self.psc.context))
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
        enable_assm_2t(self.psc.context)

        res = is_pass(prove_out_2t(self.psc.context))
        res_str = "SAFE" if res else "UNSAFE"
        logger.info(f"Two trace verification result: {res_str}")
        return res
