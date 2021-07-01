import enum


class Module(enum.Enum):
    csm = 1
    se = 2
    fim = 3
    lids = 4
    sva = 5


class Platform(enum.Enum):
    linux = 1
    windows = 2


class Status(enum.Enum):
    active = 1
    deactivated = 2


class TargetType(enum.Enum):
    server = 1
    csp_account = 2
