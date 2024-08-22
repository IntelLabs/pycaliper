import logging

from pysmt.shortcuts import Symbol, Implies, Equals, NotEquals, Not, And, Or, BV, Solver
from pysmt.typing import BVType, BOOL


from .. import per as p


logger = logging.getLogger(__name__)


class LUTSynthProgram:
    def __init__(self):
        pass

    def add_values(self):
        pass

    def solve(self):
        pass

    def get_inv(self):
        pass


class ZDDLUTSynthProgram:

    MAX_DEPTH = 10

    def __init__(self, ctr: p.Logic, out: p.Logic):

        self.ctr = ctr
        self.out = out
        self.ctr_width = ctr.width
        self.out_width = out.width
        self.depth = 1

        self.val_symbs = [
            Symbol(f"val_{i}", BVType(self.ctr_width)) for i in range(1, 2)
        ]
        self.ndt_symbs = [Symbol(f"ndt_{i}", BOOL) for i in range(1, 2)]
        self.out_symbs = [Symbol(f"out_{i}", BVType(self.out_width)) for i in range(2)]

        self.cons: dict[int, list] = {i: [] for i in range(2)}

        self.solution = None

    def _increment_depth(self):
        self.depth += 1
        new_vs = Symbol(f"val_{self.depth}", BVType(self.ctr_width))
        self.val_symbs.append(new_vs)
        new_ns = Symbol(f"ndt_{self.depth}", BOOL)
        self.ndt_symbs.append(new_ns)
        new_os = Symbol(f"out_{self.depth}", BVType(self.out_width))
        self.out_symbs.append(new_os)

        self.cons[self.depth] = []
        for cv, ov, cc in self.cons[self.depth - 1]:
            ctr_val_bv = BV(cv, self.ctr_width)
            out_val_bv = BV(ov, self.out_width)
            branch = Equals(new_vs, ctr_val_bv)
            taken = Implies(branch, Implies(Not(new_ns), Equals(new_os, out_val_bv)))
            nottaken = Implies(Not(branch), cc)
            self.cons[self.depth].append((cv, ov, And(taken, nottaken)))

    def _add_entry(self, ctr_value, out_value):
        ctr_val_bv = BV(ctr_value, self.ctr_width)
        out_val_bv = BV(out_value, self.out_width)

        def add_entry_helper(i):
            if i == 0:
                self.cons[0].append(
                    (ctr_value, out_value, Equals(self.out_symbs[0], out_val_bv))
                )
                return Equals(self.out_symbs[i], out_val_bv)
            else:
                subf = add_entry_helper(i - 1)
                branch = Equals(self.val_symbs[i - 1], ctr_val_bv)
                taken = Implies(
                    branch,
                    Implies(
                        Not(self.ndt_symbs[i - 1]),
                        Equals(self.out_symbs[i], out_val_bv),
                    ),
                )
                nottaken = Implies(Not(branch), subf)
                self.cons[i].append((ctr_value, out_value, And(taken, nottaken)))
                return And(taken, nottaken)

        add_entry_helper(self.depth)

    def add_entries(self, ctr_vals: list[int], out_vals: list[int]):
        for c, o in zip(ctr_vals, out_vals):
            self._add_entry(c, o)

    def get_cons(self):
        return self.cons

    def _generate_inv(self, d, nd, v_vals: list, o_vals: list):
        v_vals.reverse()
        o_vals.reverse()

        prevpath = self.ctr == p.Const(v_vals[0], self.ctr_width)
        if nd == 0:
            inv: p.Expr = prevpath & (self.out == p.Const(o_vals[0], self.out_width))
        else:
            inv: p.Expr = prevpath

        for i in range(1, d):
            currbranch = self.ctr == p.Const(v_vals[i], self.ctr_width)
            if i > nd - 1:
                inv = inv | (
                    (
                        ~(prevpath)
                        & currbranch
                        & (self.out == p.Const(o_vals[i], self.out_width))
                    )
                )
            else:
                inv = inv | (~(prevpath) & currbranch)
            prevpath = prevpath | currbranch

        inv = inv | (~(prevpath) & (self.out == p.Const(o_vals[d], self.out_width)))

        self.solution = inv

    def _solve_nondet(self, d, nd=0):

        solver = Solver(logic="QF_BV")

        constraints = [c[2] for c in self.cons[d]]

        solver.add_assertion(And(constraints))
        solver.add_assertion(And([Not(n) for n in self.ndt_symbs[0 : d - nd]]))

        if solver.solve():
            # Solution found
            logger.debug(f"Found a solution with #nondet {nd} and depth {d}.")

            self._generate_inv(
                d,
                nd,
                [solver.get_value(l).bv_unsigned_value() for l in self.val_symbs[:d]],
                [
                    solver.get_value(l).bv_unsigned_value()
                    for l in self.out_symbs[: d + 1]
                ],
            )

            return True

        logger.debug(f"No solution found with #nondet {nd} and depth {d}.")
        return False

    def solve(self, depth=MAX_DEPTH):

        # Try as is, without incrementing
        for d in range(1, depth):
            # If we have not reached the depth, increment
            while self.depth < d:
                self._increment_depth()
            # Try to find a solution (allowing nondet)
            for nd in range(d + 1):
                if self._solve_nondet(d, nd):
                    return True
        return False

    def get_inv(self):
        return self.solution
