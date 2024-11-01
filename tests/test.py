import logging
import sys
import os

import unittest
import json

import btoropt

from argparse import Namespace

from tempfile import NamedTemporaryFile

from pycaliper.pycmanager import get_pyconfig, PYCArgs, PYCTask, start

from pycaliper.frontend.pyclex import lexer
from pycaliper.frontend.pycparse import parser
from pycaliper.frontend.pycgen import PYCGenPass

from pycaliper.verif.jgverifier import JGVerifier2Trace
from pycaliper.svagen import SVAGen
import pycaliper.jginterface.jasperclient as jgc
from pycaliper.btorinterface.pycbtorsymex import PYCBTORSymex
from pycaliper.verif.btorverifier import BTORVerifier2Trace
from pycaliper.verif.jgverifier import JGVerifier1TraceBMC

from btor2ex import BoolectorSolver
from btor2ex.btor2ex.utils import parsewrapper

from specs.regblock import regblock
from specs.array_nonzerobase import array_nonzerobase

# h1 = logging.StreamHandler(sys.stdout)
# h1.setLevel(logging.DEBUG)

# # Info log to stdout

# h1 = logging.FileHandler("debug.log", mode="w+")
# logging.basicConfig(
#     level=logging.DEBUG,
#     handlers=[h1],
#     format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
# )

# logger = logging.getLogger(__name__)

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.INFO)
h1.setFormatter(logging.Formatter("%(levelname)s::%(message)s"))

h2 = logging.FileHandler("test_debug.log", mode="w")
h2.setLevel(logging.DEBUG)
h2.setFormatter(logging.Formatter("%(asctime)s::%(name)s::%(levelname)s::%(message)s"))

# Add filename and line number to log messages
logging.basicConfig(level=logging.DEBUG, handlers=[h1, h2])

logger = logging.getLogger(__name__)


class TestSVAGen(unittest.TestCase):
    def gen_sva(self, mod):
        svagen = SVAGen(mod)
        # Write to temporary file
        with NamedTemporaryFile(
            mode="w+", delete=False, suffix=".sv", dir="tests/out"
        ) as f:
            svagen.create_pyc_specfile(k=2, filename=f.name)
            print(f"Wrote SVA specification to temporary file {f.name}")

    def test_array_nonzerobase(self):
        self.gen_sva(array_nonzerobase())

    def test_regblock(self):
        self.gen_sva(regblock())


class TestVerifier(unittest.TestCase):
    def test_regblock(self):
        jgc.MODE = jgc.ClientMode.SIM

        regb = regblock()

        with open("designs/regblock/config.json", "r") as f:
            config = json.load(f)

        args = Namespace(mock=True, sdir="")
        pyconfig = get_pyconfig(config, args)
        invverif = JGVerifier2Trace(pyconfig)
        invverif.verify(regb)


class TestParser(unittest.TestCase):
    def load_test(self, testname):
        filename = os.path.join("tests/specs", testname)
        with open(filename, "r") as f:
            return f.read()

    def lex_file(self, filename):
        lexer.input(self.load_test(filename))
        # Write tokens to temporary file
        with NamedTemporaryFile(mode="w+", delete=False, dir="tests/out") as f:
            while True:
                tok = lexer.token()
                if not tok:
                    break  # No more input
                f.write(f"{tok}\n")
            print(f"Wrote tokens to temporary file {f.name}")

    def test_lexer1(self):
        self.lex_file("test1.caliper")

    def parse_file(self, filename):
        result = parser.parse(self.load_test(filename))
        pycgenpass = PYCGenPass()
        pycgenpass.run(result)

        # Print to named temporary file
        with NamedTemporaryFile(
            mode="w+", delete=False, dir="tests/out", suffix=".py"
        ) as f:
            f.write(pycgenpass.outstream.getvalue())
            print(f"Wrote PYC specification to temporary file {f.name}")

    def test_pycgen1(self):
        self.parse_file("test1.caliper")


class BTORInterfaceTest(unittest.TestCase):
    def test_btormc_twosafe(self):
        prgm = btoropt.parse(parsewrapper("tests/btor/reg_en.btor"))
        engine = PYCBTORSymex(BoolectorSolver("test"), prgm)
        engine.add_eq_assms(["en", "d", "rst", "q"])
        engine.add_eq_assrts(["q"])
        self.assertTrue(engine.inductive_two_safety())

    def test_btorverifier1(self):
        prgm = btoropt.parse(parsewrapper("tests/btor/regblock.btor"))

        engine = BTORVerifier2Trace(PYCBTORSymex(BoolectorSolver("test"), prgm))
        self.assertTrue(engine.verify(regblock()))

class SymbolicSimulator(unittest.TestCase):
    
    def gen_test(self, path):
        args = PYCArgs(path=path, mock=False, params="", sdir="", port=8080, onetrace=True, bmc=True)
        return start(PYCTask.VERIFBMC, args)

    def test_adder(self):
        (pconfig, tmgr, module) = self.gen_test("designs/adder/config.json")
        
        verifier = JGVerifier1TraceBMC(pconfig)
        logger.debug("Running BMC verification.")

        verifier.verify(module)
    




if __name__ == "__main__":
    unittest.main()
