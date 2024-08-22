from pycaliper.per import Module, Logic, LogicArray
import math


class array_nonzerobase(Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.DEPTH = kwargs.get("depth", 8)
        self.DEPTHIND = int(math.log2(self.DEPTH) + 1)

        self.WIDTH = kwargs.get("width", 64)

        ELEM_T = lambda: Logic(self.WIDTH)

        self.array_ents = LogicArray(ELEM_T, self.DEPTH, base=1)

    def input(self):
        for i in range(self.DEPTH):
            self.eq(self.array_ents[i])

    def output(self):
        pass

    def state(self):
        pass
