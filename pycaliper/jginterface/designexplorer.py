
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
    "_pycinternal__output_inv",
    "clk",
    ""
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

    def get_mi_maps(self) -> tuple[dict[str, list[str]], dict[str, tuple[str, str]]]:

        self.load()

        cmd = f"get_design_info -list module"
        res: str = jgc.eval(cmd)
        # Space separated list of modules
        modules = res.split()

        instancemap : dict[str, list[str]] = {}
        modulemap : dict[str, tuple[str, str]] = {}

        for module in modules:
            cmd = f"get_design_info -module {module} -list instance"
            res: str = jgc.eval(cmd)
            instancemap[module] = res.split()
            for instance in res.split():
                cmd = f"get_design_info -instance {instance} -list module_name_no_param"
                modulename: str = jgc.eval(cmd)
                # TODO: support multiple instances of the same module with different parameters
                # cmd = f"get_design_info -instance {instance} -list "
                params : dict[str, str] = {}
                paramlist : list = []
                for param in params:
                    paramlist.append(f"{param}_{params[param]}")
                modulemap[instance] = (modulename, "__".join(paramlist))

        return instancemap, modulemap
    
    def get_signals(self, instancename: str) -> dict[str, list[str]]:
        self.load()
        cmd = f"get_design_info -instance {instancename} -list signal"
        res: str = jgc.eval(cmd)

        instance_signals : dict[str, list[str]] = {}

        all_signals = [signal for signal in res.split() if signal not in PYCINTERNAL_RESERVED]
        # Only maintain local signals
        if self.topmod == instancename:
            # Top module name is same as instance name
            instance_signals[instancename] = [signal for signal in all_signals if '.' not in signal]
        
        for signal in all_signals:
            if '.' in signal:
                inst, signame = signal.rsplit('.', 1)
                if inst not in instance_signals:
                    instance_signals[inst] = []
                instance_signals[inst].append(signame)

        return instance_signals

    def get_instances(self, instancename: str) -> dict[str, list[str]]: 
        self.load()
        cmd = f"get_design_info -instance {instancename} -list instance"
        res: str = jgc.eval(cmd)
        

        all_instances = [a for a in res.split()]

        instance_instances : dict[str, list[str]] = {a: [] for a in all_instances}
        
        # Top modules is a special case
        if self.topmod == instancename:
            instance_instances[instancename] = [a for a in all_instances if '.' not in a and a != self.topmod]

        for instance in all_instances:
            if '.' in instance:
                inst, instname = instance.rsplit('.', 1)
                instance_instances[inst].append(instname)

        return instance_instances


    def mk_signal(self, instancename: str, signalname: str):
        
        logger.debug(f"Constructing pycaliper signal: {signalname} from instance {instancename}")

        if instancename != self.topmod:
            signalqueryname = f"{instancename}.{signalname}"
        else:
            signalqueryname = signalname
            
        cmd = f"get_signal_info -indexes {signalqueryname}"
        res: str = jgc.eval(cmd)

        fields = res.split()
        if fields[0] == "1D_Array":
            # Logic signal: fields[1], fields[2]
            width = abs(int(fields[1])-int(fields[2]))+1
            return Logic(width, signalname)
        elif fields[0] == "Bit":
            # Logic signal: fields[1]
            return Logic(width=1, name=signalname)
        elif fields[0] == "ND_Array":
            # LogicArray signal: fields[1], fields[2], fields[3]
            typ = int(fields[3])-int(fields[4])+1
            base = min(fields[2], fields[1])
            size = max(fields[1], fields[2]) - base + 1
            return LogicArray(lambda: Logic(typ), size, base, name=signalname)
        else:
            logger.error(f"Unknown signal type: {fields[0]}")
            return None



    def generate_skeleton(self, rootinstance: str = "") -> Module:

        # Load the Jasper script
        self.load()
        # Get the instances and module map
        instancemap, modulemap = self.get_mi_maps()

        # Get the top module by default
        if rootinstance == "":
            rootmodule = self.topmod
            rootinstance = instancemap[rootmodule][0]
        else:
            rootmodule, rootparams = modulemap[rootinstance]
        
        # Get the signals in the top module
        all_signals = self.get_signals(rootinstance)
        logger.debug(f"Signals in the top module: {all_signals}")

        # Get the instances in the top module
        all_instances = self.get_instances(rootinstance)
        logger.debug(f"Instances in the top module: {all_instances}")

        # Modules constructed so far (keyed by the name of the module)
        done_modules : dict[str, Module] = {}

        def gs_helper(_instname: str) -> Module:

            # Get the module name and parameters
            _modname, _modparams = modulemap[_instname]
            if _modname in done_modules:
                return done_modules[_modname]
            
            # Create a module
            moduleclass = ModuleFactory(_modname, [])
            module : Module = moduleclass()
            
            # Add submodules
            inst_instances = all_instances[_instname]
            for subinstance in inst_instances:
                logger.debug(f"Adding subinstance: {_instname}..{subinstance}")
                if _instname == self.topmod:
                    module._submodules[subinstance] = gs_helper(subinstance)
                else:
                    module._submodules[subinstance] = gs_helper(f"{_instname}.{subinstance}")

            # Get signals in the module
            inst_signals = all_signals[_instname]
            
            for signal_basename in inst_signals:
                logger.debug(f"Adding signal: {signal_basename} to instance {_instname} of module {_modname}")
                module._signals[signal_basename] = self.mk_signal(_instname, signal_basename)
                

            done_modules[_modname] = module
            return module

        return gs_helper(rootinstance)
