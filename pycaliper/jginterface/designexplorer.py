
import logging

from pycaliper.per.per import Module, Logic, LogicArray, ModuleFactory, Path
from pycaliper.pycmanager import PYConfig
from pycaliper.jginterface.jgoracle import loadscript


from . import jasperclient as jgc

logger = logging.getLogger(__name__)

PYCINTERNAL_RESERVED = [
    "_pycinternal__input",
    "_pycinternal__state",
    "_pycinternal__output",
    "_pycinternal__holes",
    "_pycinternal_caholes",
    "_pycinternal__perholes",
    "_pycinternal__input_inv",
    "_pycinternal_state_inv",
    "_pycinternal__output_inv"
]


class DesignExplorer:

    def __init__(self, psconfig: PYConfig) -> None:
        self.psc = psconfig
        self.loaded : bool = False

    def load(self):
        if not self.loaded:
            loadscript(self.psc.script)
            self.loaded = True

    @property
    def topmod(self):
        self.load()
        cmd = f"get_top_module"
        res: str = jgc.eval(cmd)
        return res

    def get_instances(self) -> dict[str, list[str]]:

        self.load()

        cmd = f"get_design_info -list module"
        res: str = jgc.eval(cmd)
        # Space separated list of modules
        modules = res.split()

        modulemap : dict[str, list[str]] = {}

        for module in modules:
            cmd = f"get_design_info -module {module} -list instance"
            res: str = jgc.eval(cmd)
            modulemap[module] = res.split()

        return modulemap
    
    def get_signals(self, module: str):
        self.load()
        cmd = f"get_design_info -module {module} -list signal"
        res: str = jgc.eval(cmd)

        all_signals = res.split()
        # Only maintain local signals
        if self.topmod == module:
            return [signal for signal in all_signals if '.' not in signal]
        else:
            return [signal for signal in all_signals if signal.startswith(f"{module}.")]
    

    def get_modules(self, modname: str) -> list[str]: 
        self.load()
        cmd = f"get_design_info -module {modname} -list module"
        res: str = jgc.eval(cmd)
        
        return [a for a in res.split() if a != modname]

    def generate_skeleton(self, modname: str = "") -> Module:

        # Load the Jasper script
        self.load()
        
        # Get the top module by default
        if modname == "":
            modname = self.topmod
        
        module_instances = self.get_instances()
        # Modules constructed so far
        done_modules : dict[str, Module] = {}

        def gs_helper(_modname: str):
            if _modname in done_modules:
                return done_modules[_modname]
            
            # First complete all submodules
            submodules = self.get_modules(_modname)
            for submodule in submodules:
                gs_helper(submodule)

            # Create a module
            moduleclass = ModuleFactory(_modname, [])
            module : Module = moduleclass()

            # Get signals in the module
            signals = self.get_signals(_modname)
            # Filter out reserved signals
            signals = [signal for signal in signals if signal not in PYCINTERNAL_RESERVED]

            for signal in signals:
                
                # Get signal width 
                cmd = f"get_signal_info -indexes {signal}"
                res: str = jgc.eval(cmd)

                signal_basename = signal.split('.')[-1]

                fields = res.split()
                logger.debug(f"Signal: {signal} has fields: {fields}")
                if fields[0] == "1D_Array":
                    # Logic signal: fields[1], fields[2]
                    width = abs(int(fields[1])-int(fields[2]))+1
                    module._signals[signal_basename] = Logic(width, signal_basename)
                elif fields[0] == "Bit":
                    # Logic signal: fields[1]
                    module._signals[signal_basename] = Logic(width=1, name=signal_basename)
                elif fields[0] == "ND_Array":
                    # LogicArray signal: fields[1], fields[2], fields[3]
                    typ = int(fields[3])-int(fields[4])+1
                    base = min(fields[2], fields[1])
                    size = max(fields[1], fields[2]) - base + 1
                    module._signals[signal_basename] = LogicArray(lambda: Logic(typ), size, base, name=signal_basename)
                else:
                    logger.error(f"Unknown signal type: {fields[0]}")
                    continue

        return module
