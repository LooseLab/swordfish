"""
Utilities for speaking with MinoTour
"""
from minknow_api.manager import Manager


def print_args(args, logger=None, exclude=None):
    """Print and format all arguments from the command line"""
    if exclude is None:
        exclude = []
    dirs = dir(args)
    for attr in dirs:
        if attr[0] != "_" and attr not in exclude and attr.lower() == attr:
            record = "{a}={b}".format(a=attr, b=getattr(args, attr))
            if logger is not None:
                logger.info(record)
            else:
                print(record)


def get_device(device, **kws):
    """Get gRPC device"""
    manager = Manager(**kws)
    for position in manager.flow_cell_positions():
        if position.name == device:
            return position
    raise RuntimeError(f"Could not find device {device}")
