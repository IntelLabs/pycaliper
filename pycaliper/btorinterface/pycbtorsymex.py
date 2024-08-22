"""
    pycaliper:

    PyCaliperSymex:
        Symbolic execution engine performing PER verification on BTOR
"""

import sys
import logging

from btoropt import program as prg
from pycaliper.per import Expr
from btor2ex import BTORSolver
from btor2ex import BTOR2Ex

logger = logging.getLogger(__name__)


class PYCBTORSymex(BTOR2Ex):
    """
    Symbolically execute a BTOR program: the barebones
    """

    def __init__(
        self,
        solver: BTORSolver,
        prog: list[prg.Instruction],
        cpy1: str = "A",
        cpy2: str = "B",
    ):
        super().__init__(solver, prog)

        self.cpy1 = cpy1
        self.cpy2 = cpy2
        self.eq_assms: list = []
        self.condeq_assms: list[tuple[Expr, Expr]] = []
        self.eq_assrts: list = []
        self.condeq_assrts: list[tuple[Expr, Expr]] = []

        self.holes = []

    def add_eq_assms(self, assms: list[Expr]):
        # TODO: ignore slices for now
        self.eq_assms.extend(assms)

    def add_condeq_assms(self, condeq_assms: list[tuple[Expr, Expr]]):
        self.condeq_assms.extend(condeq_assms)

    def add_eq_assrts(self, assrts: list[Expr]):
        # TODO: ignore slices for now
        self.eq_assrts.extend(assrts)

    def add_condeq_assrts(self, condeq_assrts: list[tuple[Expr, Expr]]):
        self.condeq_assrts.extend(condeq_assrts)

    def add_hole_constraints(self, holes: list[Expr]):
        """Add constraints for holes"""
        self.holes.extend(holes)

    def get_lid_pair(self, pth: Expr):
        path1 = f"{self.cpy1}.{pth}"
        path2 = f"{self.cpy2}.{pth}"
        if path1 not in self.names:
            logger.error("Path %s not found", path1)
            sys.exit(1)
        if path2 not in self.names:
            logger.error("Path %s not found", path2)
            sys.exit(1)
        lid1 = self.names[path1]
        lid2 = self.names[path2]
        return (lid1, lid2)

    def get_assm_constraints(self, frame):
        """
        Get the constraints for the assumptions
        """
        cons = []
        # Equality assumptions
        for assm_pth in self.eq_assms:
            lid1, lid2 = self.get_lid_pair(assm_pth)
            cons.append(self.slv.eq_(frame[lid1], frame[lid2]))

        # Conditional equality assumptions
        for cond_assm in self.condeq_assms:
            pre_lid1, pre_lid2 = self.get_lid_pair(cond_assm[0])
            post_lid1, post_lid2 = self.get_lid_pair(cond_assm[1])
            cons.append(
                self.slv.implies_(
                    self.slv.and_(frame[pre_lid1], frame[pre_lid2]),
                    self.slv.eq_(frame[post_lid1], frame[post_lid2]),
                )
            )
        return cons

    def get_assrt_constraints(self, frame):
        """
        Get the constraints for the assumptions
        """
        # TODO: this will panic if constraint is on output
        cons = []
        for assrt_pth in self.eq_assrts:
            lid1, lid2 = self.get_lid_pair(assrt_pth)
            # Add negation of constraint
            cons.append(self.slv.neq_(frame[lid1], frame[lid2]))
        # Conditional equality assumptions
        for cond_assrt in self.condeq_assrts:
            pre_lid1, pre_lid2 = self.get_lid_pair(cond_assrt[0])
            post_lid1, post_lid2 = self.get_lid_pair(cond_assrt[1])
            cons.append(
                self.slv.and_(
                    self.slv.and_(frame[pre_lid1], frame[pre_lid2]),
                    self.slv.neq_(frame[post_lid1], frame[post_lid2]),
                )
            )
        return cons

    def get_hole_constraints(self, preframe, postframe):
        """Get constraints for holes"""
        precons = []
        postcons = []
        for hole in self.holes:
            lid1, lid2 = self.get_lid_pair(hole)
            precons.append(self.slv.eq_(preframe[lid1], postframe[lid2]))
            postcons.append(self.slv.neq_(postframe[lid1], preframe[lid2]))
        return precons, postcons

    def inductive_two_safety(self) -> bool:
        """Verifier for inductive two-safety property

        Returns:
            bool: is SAFE?
        """
        # Unroll twice
        self.execute()
        # Check
        self.execute()

        pre_state = self.state[0]
        post_state = self.state[1]

        logger.debug("Pre state: %s", pre_state)
        logger.debug("Post state: %s", post_state)

        assms = self.get_assm_constraints(pre_state)
        assrts = self.get_assrt_constraints(post_state)

        logger.debug("Assms: %s", assms)
        logger.debug("Assrts: %s", assrts)

        for assrt in assrts:
            for assm in assms:
                self.slv.mk_assume(assm)
            # Apply all internal assumptions
            for assmdict in self.assms:
                for _, assmi in assmdict.items():
                    self.slv.mk_assume(assmi)
            self.slv.mk_assert(assrt)
            result = self.slv.check_sat()
            logger.debug(
                "For assertion %s, result %s", assrt, "BUG" if result else "SAFE"
            )
            if result:
                logger.debug("Found a bug")
                model = self.slv.get_model()
                logger.debug("Model:\n%s", model)
                return False

        logger.debug("No bug found, inductive proof complete")
        # Safe
        return True

    def inductive_two_safety_syn(self) -> bool:
        """Synthesizer for inductive two-safety property

        Returns:
            bool: synthesis result
        """
        # Unroll twice
        self.execute()
        # Check
        self.execute()

        pre_state = self.state[0]
        post_state = self.state[1]

        logger.debug("Pre state: %s", pre_state)
        logger.debug("Post state: %s", post_state)

        assms = self.get_assm_constraints(pre_state)
        assrts = self.get_assrt_constraints(post_state)

        hole_assms, hole_assrts = self.get_hole_constraints(pre_state, post_state)

        logger.debug("Assms: %s", assms)
        logger.debug("Assrts: %s", assrts)
        logger.debug("Hole Assms: %s", hole_assms)
        logger.debug("Hole Assrts: %s", hole_assrts)

        while hole_assms:

            failed = False
            for assrt in assrts + hole_assrts:
                for assm in assms + hole_assms:
                    self.slv.mk_assume(assm)
                # Apply all internal assumptions
                for assmdict in self.assms:
                    for _, assmi in assmdict.items():
                        self.slv.mk_assume(assmi)
                self.slv.mk_assert(assrt)
                result = self.slv.check_sat()
                logger.debug(
                    "For assertion %s, result %s", assrt, "BUG" if result else "SAFE"
                )
                if result:
                    logger.debug("Found a bug")
                    model = self.slv.get_model()
                    logger.debug("Model:\n%s", model)
                    failed = True
                    break
            if failed:
                hole_assms = hole_assms[:-1]
                hole_assrts = hole_assrts[:-1]
            else:
                logger.debug("Self-inductive fp found, synthesis complete.")
                return self.holes[: len(hole_assms)]

        logger.debug("No synthesis solution found, synthesis failed.")
        return []
