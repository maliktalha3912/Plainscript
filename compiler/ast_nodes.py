from dataclasses import dataclass, field
from typing import List, Any, Optional, Union

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

@dataclass
class VarDecl(ASTNode):
    name: str
    value: ASTNode

@dataclass
class Assign(ASTNode):
    name: str
    value: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    else_if_stmts: List[tuple] = field(default_factory=list) # (condition, block)
    else_block: Optional[List[ASTNode]] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    block: List[ASTNode]

@dataclass
class RepeatStmt(ASTNode):
    count: ASTNode
    block: List[ASTNode]

@dataclass
class ForEachStmt(ASTNode):
    item: str
    collection: str
    block: List[ASTNode]

@dataclass
class ForRangeStmt(ASTNode):
    var: str
    start: ASTNode
    end: ASTNode
    block: List[ASTNode]

@dataclass
class FuncDef(ASTNode):
    name: str
    params: List[str]
    block: List[ASTNode]

@dataclass
class FuncCall(ASTNode):
    name: str
    args: List[ASTNode]

@dataclass
class ShowStmt(ASTNode):
    expr: ASTNode

@dataclass
class AskStmt(ASTNode):
    var: str

@dataclass
class ReturnStmt(ASTNode):
    expr: ASTNode

@dataclass
class TryStmt(ASTNode):
    try_block: List[ASTNode]
    error_block: List[ASTNode]

@dataclass
class RecordDef(ASTNode):
    name: str
    fields: List[str]

@dataclass
class AddStmt(ASTNode):
    item: ASTNode
    collection: str

@dataclass
class RemoveStmt(ASTNode):
    item: ASTNode
    collection: str

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    right: ASTNode

@dataclass
class Compare(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class LogicalOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class NumberLit(ASTNode):
    value: Union[int, float]

@dataclass
class StringLit(ASTNode):
    value: str

@dataclass
class BoolLit(ASTNode):
    value: bool

@dataclass
class NullLit(ASTNode):
    value: Any = None

@dataclass
class ListLit(ASTNode):
    elements: List[ASTNode]

@dataclass
class PropertyAccess(ASTNode):
    obj: str
    prop: str

@dataclass
class PropertyAssign(ASTNode):
    obj: str
    prop: str
    value: ASTNode

@dataclass
class JoinedWith(ASTNode):
    left: ASTNode
    right: ASTNode

@dataclass
class IsBetween(ASTNode):
    value: ASTNode
    low: ASTNode
    high: ASTNode

@dataclass
class FirstItem(ASTNode):
    collection: str

@dataclass
class LastItem(ASTNode):
    collection: str

@dataclass
class LengthOf(ASTNode):
    collection: str
