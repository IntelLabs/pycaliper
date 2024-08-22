import enum
import logging
import os

from . import jasperclient as jgc

logger = logging.getLogger(__name__)


class ProofResult(enum.Enum):
    NONE = 0
    CEX = 1
    SAFE = 2
    PROVEN = 3
    MAX_TRACE_LENGTH = 4
    UNKNOWN = 5
    SIM = 6

    def __str__(self):
        return self.name


def prove(taskcon: str, prop: str) -> ProofResult:
    """Prove a property

    Args:
        taskcon (str): proof node the property is defined under
        prop (str): property name

    Returns:
        ProofResult: result of the proof
    """
    prop_wctx = get_as_asrt_name(taskcon, prop)
    logger.debug(f"Proving property: {prop_wctx}")
    cmd = f"prove -property {{ {prop_wctx} }}"
    res: str = jgc.eval(cmd)
    logger.debug(f"Proving property: {prop_wctx} returned {res}")
    return ProofResult[res.upper()]


def is_pass(res: ProofResult) -> bool:
    """Is the result a pass"""
    return res in [ProofResult.SAFE, ProofResult.MAX_TRACE_LENGTH, ProofResult.PROVEN]


def get_as_assm_name(taskcon: str, prop: str) -> str:
    """Get the hierarchical assumption name for a property wire

    Args:
        taskcon (str): proof node name under which the property is defined
        prop (str): property name

    Returns:
        str: hierarchical assumption name
    """
    return f"{taskcon}.A_{prop}"


def get_as_asrt_name(taskcon: str, prop: str) -> str:
    """Get the hierarchical assertion name for a property wire

    Args:
        taskcon (str): proof node name under which the property is defined
        prop (str): property name

    Returns:
        str: hierarchical assertion name
    """
    return f"{taskcon}.P_{prop}"


def disable_assm(taskcon: str, assm: str):
    """Disable an assumption

    Args:
        taskcon (str): proof node name
        assm (str): assumption name

    Returns:
        _type_: result of the JasperGold command
    """
    assm_wctx = get_as_assm_name(taskcon, assm)
    logger.debug(f"Disabling assumption: {assm_wctx}")
    cmd = f"assume -disable {assm_wctx}"
    res = jgc.eval(cmd)
    logger.debug(f"Disabling assumption: {assm_wctx} returned {res}")
    return res


def enable_assm(taskcon: str, assm: str):
    """Enable an assumption

    Args:
        taskcon (str): proof node name
        assm (str): assumption name

    Returns:
        _type_: result of the JasperGold command
    """
    assm_wctx = get_as_assm_name(taskcon, assm)
    logger.debug(f"Enabling assumption: {assm_wctx}")
    cmd = f"assume -enable {assm_wctx}"
    res = jgc.eval(cmd)
    logger.debug(f"Enabling assumption: {assm_wctx} returned {res}")
    return res


def enable_assm_1t(taskcon: str):
    """Enable only 1-trace assumptions (required for 1 trace properties)

    Args:
        taskcon (str): proof node name
    """
    enable_assm(taskcon, "input_inv")
    enable_assm(taskcon, "state_inv")
    disable_assm(taskcon, "input")
    disable_assm(taskcon, "state")


def enable_assm_2t(taskcon: str):
    """Enable all assumptions required for 2 trace properties

    Args:
        taskcon (str): proof node name
    """
    enable_assm(taskcon, "input")
    enable_assm(taskcon, "state")
    enable_assm(taskcon, "input_inv")
    enable_assm(taskcon, "state_inv")


def prove_out_1t(taskcon):
    return prove(taskcon, "output_inv")


def prove_out_2t(taskcon):
    return prove(taskcon, "output")


def loadscript(script):
    # Get pwd
    cmd = f"include {script}"
    logger.info(f"Loading Jasper script: {cmd}")
    res = jgc.eval(cmd)
    return res


def create_vcd_trace(prop, filepath):
    windowcmd = f"visualize -violation -property {prop} -window visualize:trace"
    tracecmd = f"visualize -save -force -vcd {filepath} -window visualize:trace"
    logger.debug(f"Creating VCD trace for property: {prop}")
    windowres = jgc.eval(windowcmd)
    traceres = jgc.eval(tracecmd)
    logger.debug(
        f"Creating VCD trace for property: {prop} returned {windowres}; {traceres}"
    )
    return


def setjwd(jwd):
    # Change the Jasper working directory
    pwd = os.getcwd()
    cmd = f"cd {pwd}/{jwd}"
    res = jgc.eval(cmd)
    logger.debug(f"Changing Jasper working directory to {jwd} returned {res}")
    return res
