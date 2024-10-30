import sys
import logging

from pycaliper.verif.jgverifier import JGVerifier1Trace, JGVerifier2Trace, JGVerifier1TraceBMC
from pycaliper.synth.persynthesis import PERSynthesizer
from pycaliper.svagen import SVAGen
from pycaliper.synth.alignsynthesis import AlignSynthesizer
from pycaliper.pycmanager import start, PYCTask, PYCArgs

import typer
from typer import Argument, Option
from typing_extensions import Annotated

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.INFO)
h1.setFormatter(logging.Formatter("%(levelname)s::%(message)s"))

h2 = logging.FileHandler("debug.log", mode="w")
h2.setLevel(logging.DEBUG)
h2.setFormatter(logging.Formatter("%(asctime)s::%(name)s::%(levelname)s::%(message)s"))

# Add filename and line number to log messages
logging.basicConfig(level=logging.DEBUG, handlers=[h1, h2])

logger = logging.getLogger(__name__)

DESCRIPTION = "Invariant verification and synthesis using Jasper."
app = typer.Typer(help=DESCRIPTION)


@app.command("verif")
def verif_main(
        path: Annotated[str, Argument(help="Path to the JSON config file")] = "",
        # Allow using -m or --mock
        mock: Annotated[bool, Option("--mock", "-m", help="Run in offline (mock) mode?")] = False,
        # Allow using --params
        params: Annotated[str, Option(help="Parameters for the spec module: (<key>=<intvalue>)+")] = "",
        # Allow using -s or --sdir
        sdir: Annotated[str, Option(help="Directory to save results to.")] = "",
        # Allow using --port
        port: Annotated[int, Option(help="Port number to connect to Jasper server")] = 8080,
        # Allow using --onetrace
        onetrace: Annotated[bool, Option(help="Verify only one-trace properties.")] = False,
        # Allow using --bmc
        bmc: Annotated[bool, Option(help="Perform verification with bounded model checking.")] = False):
    args = PYCArgs(path=path, mock=mock, params=params, sdir=sdir, port=port, onetrace=onetrace, bmc=bmc)
    if not bmc:
        if onetrace:
            pconfig, tmgr, module = start(PYCTask.VERIF1T, args)
            verifier = JGVerifier1Trace(pconfig)
            logger.debug("Running single trace verification.")
        else:
            pconfig, tmgr, module = start(PYCTask.VERIF2T, args)
            verifier = JGVerifier2Trace(pconfig)
            logger.debug("Running two trace verification.")
    else:
        pconfig, tmgr, module = start(PYCTask.VERIFBMC, args)
        verifier = JGVerifier1TraceBMC(pconfig)
        logger.debug("Running BMC verification.")

    verifier.verify(module)

@app.command("persynth")
def persynth_main(
        path: Annotated[str, Argument(help="Path to the JSON config file")] = "",
        # Allow using -m or --mock
        mock: Annotated[bool, Option("--mock", "-m", help="Run in offline (mock) mode?")] = False,
        # Allow using --params
        params: Annotated[str, Option(help="Parameters for the spec module: (<key>=<intvalue>)+")] = "",
        # Allow using -s or --sdir
        sdir: Annotated[str, Option(help="Directory to save results to.")] = "",
        # Allow using --port
        port: Annotated[int, Option(help="Port number to connect to Jasper server")] = 8080):
    
    args = PYCArgs(path=path, mock=mock, params=params, sdir=sdir, port=port)
    pconfig, tmgr, module = start(PYCTask.PERSYNTH, args)

    synthesizer = PERSynthesizer(pconfig)
    finalmod = synthesizer.synthesize(module)

    tmgr.save_spec(finalmod)
    tmgr.save()


@app.command("svagen")
def svagen_main(
        path: Annotated[str, Argument(help="Path to the JSON config file")] = "",
        # Allow using -m or --mock
        mock: Annotated[bool, Option("--mock", "-m", help="Run in offline (mock) mode?")] = False,
        # Allow using --params
        params: Annotated[str, Option(help="Parameters for the spec module: (<key>=<intvalue>)+")] = "",
        # Allow using -s or --sdir
        sdir: Annotated[str, Option(help="Directory to save results to.")] = "",
        # Allow using --port
        port: Annotated[int, Option(help="Port number to connect to Jasper server")] = 8080):
    args = PYCArgs(path=path, mock=mock, params=params, sdir=sdir, port=port)
    pconfig, tmgr, module = start(PYCTask.SVAGEN, args)

    svagen = SVAGen(module)
    svagen.create_pyc_specfile(k=pconfig.k, filename=pconfig.pycfile)


@app.command("alignsynth")
def alignsynth_main(
        path: Annotated[str, Argument(help="Path to the JSON config file")] = "",
        # Allow using -m or --mock
        mock: Annotated[bool, Option("--mock", "-m", help="Run in offline (mock) mode?")] = False,
        # Allow using --params
        params: Annotated[str, Option(help="Parameters for the spec module: (<key>=<intvalue>)+")] = "",
        # Allow using -s or --sdir
        sdir: Annotated[str, Option(help="Directory to save results to.")] = "",
        # Allow using --port
        port: Annotated[int, Option(help="Port number to connect to Jasper server")] = 8080):
    args = PYCArgs(path=path, mock=mock, params=params, sdir=sdir, port=port)

    pconfig, tmgr, module = start(PYCTask.CTRLSYNTH, args)

    synthesizer = AlignSynthesizer(tmgr, pconfig)
    asmod = synthesizer.synthesize(module)

    tmgr.save_spec(asmod)
    tmgr.save()


@app.command("fullsynth")
def fullsynth_main(
        path: Annotated[str, Argument(help="Path to the JSON config file")] = "",
        # Allow using -m or --mock
        mock: Annotated[bool, Option("--mock", "-m", help="Run in offline (mock) mode?")] = False,
        # Allow using --params
        params: Annotated[str, Option(help="Parameters for the spec module: (<key>=<intvalue>)+")] = "",
        # Allow using -s or --sdir
        sdir: Annotated[str, Option(help="Directory to save results to.")] = "",
        # Allow using --port
        port: Annotated[int, Option(help="Port number to connect to Jasper server")] = 8080):
    args = PYCArgs(path=path, mock=mock, params=params, sdir=sdir, port=port)
    pconfig, tmgr, module = start(PYCTask.FULLSYNTH, args)

    # PER Synthesizer
    psynth = PERSynthesizer(pconfig)

    verif = JGVerifier1Trace(pconfig)

    # CA Synthesizer
    asynth = AlignSynthesizer(tmgr, pconfig)
    # Align synthesize module, save it and grab a copy
    asmod = asynth.synthesize(module)
    tmgr.save_spec(asmod)

    # Check that invariants pass
    res = verif.verify(asmod)
    if res:
        logger.info("Single trace verification passed, moving on to PER synthesis!")
    else:
        logger.error("Verification failed for single trace properties, quitting!")
        sys.exit(1)

    # PER Synthesize module
    finalmod = psynth.synthesize(asmod)
    tmgr.save_spec(finalmod)
    tmgr.save()

if __name__ == "__main__":
    app()
