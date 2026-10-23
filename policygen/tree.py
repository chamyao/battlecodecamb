"""Policy syntax tree: expressions (Call, Const, Var) and steps."""
from dataclasses import dataclass, field

from .blocks import Block


@dataclass
class Call:
    block: Block
    args: list


@dataclass
class Const:
    type: str  # "Num" or "Bytes"
    value: object


@dataclass
class Var:
    name: str
    type: str


@dataclass
class Do:
    call: Call  # an effect block


@dataclass
class If:
    cond: object
    then: list
    orelse: list = field(default_factory=list)


@dataclass
class Let:
    name: str
    expr: object
    keep: bool = False  # True: persists across turns (computed once)


@dataclass
class EndTurn:
    pass


def type_of(expr):
    if isinstance(expr, Call):
        return expr.block.ret
    return expr.type
