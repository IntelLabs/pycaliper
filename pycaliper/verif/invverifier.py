from ..pycmanager import PYConfig


class InvVerifier:
    def __init__(self, pyconfig: PYConfig) -> None:
        self.psc = pyconfig

    def verify(self, module) -> bool:
        raise NotImplementedError("Method not implemented")
