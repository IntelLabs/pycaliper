

from pycaliper.per import *
from pycaliper.per.per import unroll


from random import randint

class adder(Module):

    def __init__(self, **kwargs):
        super().__init__()
        # default width is 8
        self.width = kwargs.get("width", 8)

        self.rst_ni = Logic(1)

        self.a_i = Logic(self.width)
        self.b_i = Logic(self.width)
        self.sum_o = Logic(self.width)

        self.probe_inputs = [randint(0, 2**self.width - 1) for _ in range(2)]


    def get_reset_seq(self, i: int) -> None:
        if i == 0:
            self.pycassume(~self.rst_ni)
        else:
            self.pycassume(self.rst_ni)

    @unroll(3)
    def simstep(self, i: int = 0) -> None:
        if i == 1:
            self.pycassume(self.a_i == Const(self.probe_inputs[0], self.width))
            self.pycassume(self.b_i == Const(self.probe_inputs[1], self.width))
        elif i == 2:
            self.pycassert(self.sum_o == Const((self.probe_inputs[0] + self.probe_inputs[1]) % (2**self.width), self.width))

        self.get_reset_seq(i)
        