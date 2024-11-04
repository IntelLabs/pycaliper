# auxmod.py

from pycaliper.per import *
from pycaliper.per.per import TypedElem


class parity(AuxModule):
    def __init__(self, portmapping: dict[str, TypedElem], name="", **kwargs) -> None:
        super().__init__(portmapping, name, **kwargs)
        self.clk = AuxPort(1, "clk")
        self.rst = AuxPort(1, "rst")
        self.counter = AuxPort(8, "counter")
        self.parity = Logic(1, "parity")


class counter(Module):
    def __init__(self, name="", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.clk = Logic(1, "clk")
        self.rst = Logic(1, "rst")
        self.counter = Logic(8, "counter")

        self.parity = parity(
            {
                "clk": self.clk,
                "rst": self.rst,
                "counter": self.counter,
            },
            name="monitor",
        )

    def input(self) -> None:
        pass

    def state(self) -> None:
        self.inv(self.counter(0) == self.parity.parity)

    def output(self) -> None:
        pass
