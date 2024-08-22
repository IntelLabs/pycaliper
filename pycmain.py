import sys
import argparse
import json
import logging

from pycaliper.verif.jgverifier import JGVerifier1Trace, JGVerifier2Trace
from pycaliper.synth.persynthesis import PERSynthesizer
from pycaliper.svagen import SVAGen
from pycaliper.synth.alignsynthesis import AlignSynthesizer
from pycaliper.pycmanager import PYCManager, PYConfig, start, PYCTask


h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.INFO)
h1.setFormatter(logging.Formatter("%(levelname)s::%(message)s"))

h2 = logging.FileHandler("debug.log", mode="w")
h2.setLevel(logging.DEBUG)
h2.setFormatter(logging.Formatter("%(asctime)s::%(name)s::%(levelname)s::%(message)s"))

# Add filename and line number to log messages
logging.basicConfig(level=logging.DEBUG, handlers=[h1, h2])

logger = logging.getLogger(__name__)


def verif_main(args):

    if args.onetrace:
        pconfig, tmgr, module = start(PYCTask.VERIF1T, args)
        verifier = JGVerifier1Trace(pconfig)
    else:
        pconfig, tmgr, module = start(PYCTask.VERIF2T, args)
        verifier = JGVerifier2Trace(pconfig)

    verifier.verify(module)


def persynth_main(args):

    pconfig, tmgr, module = start(PYCTask.PERSYNTH, args)

    synthesizer = PERSynthesizer(pconfig)
    finalmod = synthesizer.synthesize(module)

    tmgr.save_spec(finalmod)
    tmgr.save()


def svagen_main(args):
    pconfig, tmgr, module = start(PYCTask.SVAGEN, args)

    svagen = SVAGen(module)
    svagen.create_pyc_specfile(k=pconfig.k, filename=pconfig.pycfile)


def alignsynth_main(args):
    pconfig, tmgr, module = start(PYCTask.CTRLSYNTH, args)

    synthesizer = AlignSynthesizer(tmgr, pconfig)
    asmod = synthesizer.synthesize(module)

    tmgr.save_spec(asmod)
    tmgr.save()


def fullsynth_main(args):
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


def main(args):

    DESCRIPTION = "Invariant verification and synthesis using Jasper."

    argparser = argparse.ArgumentParser(description=DESCRIPTION)

    cmd = argparser.add_subparsers(dest="cmd")

    verif = cmd.add_parser("verif", help="Verify invariants.")
    verif.set_defaults(func=verif_main)
    persynth = cmd.add_parser("persynth", help="Synthesize invariants.")
    persynth.set_defaults(func=persynth_main)
    svagen = cmd.add_parser("svagen", help="Generate SVA spec file.")
    svagen.set_defaults(func=svagen_main)
    alignsynth = cmd.add_parser("alignsynth", help="Synthesize counter alignment.")
    alignsynth.set_defaults(func=alignsynth_main)
    fullsynth = cmd.add_parser(
        "fullsynth", help="Synthesize 1t invariants followed by (cond)equality ones."
    )
    fullsynth.set_defaults(func=fullsynth_main)

    argparser.add_argument("path", type=str, help="Path to the JSON config file")
    argparser.add_argument(
        "-m",
        "--mock",
        help="Run in offline (mock) mode?",
        action="store_true",
        default=False,
    )
    argparser.add_argument(
        "--params",
        nargs="+",
        help="Parameters for the spec module: (<key>=<intvalue>)+",
        default="",
    )
    argparser.add_argument(
        "-s", "--sdir", type=str, help="Directory to save results to.", default=""
    )

    verif.add_argument(
        "--onetrace",
        help="Verify only one-trace properties.",
        action="store_true",
        default=False,
    )

    for c in [verif, persynth, svagen, alignsynth, fullsynth]:
        c.add_argument(
            "--params",
            nargs="+",
            help="Parameters for the spec module: (<key>=<intvalue>)+",
            default="",
        )

    args = argparser.parse_args(args)

    # Run main command
    if args.cmd in ["verif", "persynth", "svagen", "alignsynth", "fullsynth"]:
        args.func(args)
    else:
        argparser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
