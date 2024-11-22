"""
    Namespace for properties
"""

# Properties for top module
TOP_INPUT_2T_PROP = "input"
TOP_STATE_2T_PROP = "state"
TOP_OUTPUT_2T_PROP = "output"

TOP_INPUT_1T_PROP = "input_inv"
TOP_STATE_1T_PROP = "state_inv"
TOP_OUTPUT_1T_PROP = "output_inv"

STEP_PROP = "step"
def TOP_STEP_PROP(k: int) -> str:
    """Get the property name for a given step"""
    return f"{STEP_PROP}_{k}"

def get_as_assm(prop: str) -> str:
    """Get the assumption name for a given property"""
    return f"A_{prop}"

def get_as_prop(prop: str) -> str:
    """Get the assertion name for a given property"""
    return f"P_{prop}"
