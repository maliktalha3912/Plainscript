from dataclasses import dataclass, field
from typing import Optional, List


class TACInstruction:
    """Base class for all TAC instructions."""
    pass


@dataclass
class TACBinOp(TACInstruction):
    """result = left op right"""
    result: str
    left: str
    op: str
    right: str
    def __str__(self):
        return f"    {self.result} = {self.left} {self.op} {self.right}"


@dataclass
class TACUnaryOp(TACInstruction):
    """result = op operand"""
    result: str
    op: str
    operand: str
    def __str__(self):
        return f"    {self.result} = {self.op} {self.operand}"


@dataclass
class TACCopy(TACInstruction):
    """result = operand"""
    result: str
    operand: str
    def __str__(self):
        return f"    {self.result} = {self.operand}"


@dataclass
class TACLabel(TACInstruction):
    """label:"""
    name: str
    def __str__(self):
        return f"{self.name}:"


@dataclass
class TACGoto(TACInstruction):
    """goto label"""
    label: str
    def __str__(self):
        return f"    goto {self.label}"


@dataclass
class TACIfGoto(TACInstruction):
    """if condition goto label"""
    condition: str
    label: str
    def __str__(self):
        return f"    if {self.condition} goto {self.label}"


@dataclass
class TACIfFalseGoto(TACInstruction):
    """iffalse condition goto label"""
    condition: str
    label: str
    def __str__(self):
        return f"    iffalse {self.condition} goto {self.label}"


@dataclass
class TACPrint(TACInstruction):
    """print value"""
    value: str
    def __str__(self):
        return f"    print {self.value}"


@dataclass
class TACInput(TACInstruction):
    """result = input()"""
    result: str
    def __str__(self):
        return f"    {self.result} = input()"


@dataclass
class TACParam(TACInstruction):
    """param value  (push argument for upcoming call)"""
    value: str
    def __str__(self):
        return f"    param {self.value}"


@dataclass
class TACCall(TACInstruction):
    """[result =] call func, n"""
    func: str
    num_params: int
    result: Optional[str] = None
    def __str__(self):
        call_str = f"call {self.func}, {self.num_params}"
        if self.result:
            return f"    {self.result} = {call_str}"
        return f"    {call_str}"


@dataclass
class TACReturn(TACInstruction):
    """return [value]"""
    value: Optional[str] = None
    def __str__(self):
        return f"    return {self.value}" if self.value else "    return"


@dataclass
class TACFuncBegin(TACInstruction):
    """begin_func name(params)"""
    name: str
    params: List[str]
    def __str__(self):
        return f"begin_func {self.name}({', '.join(self.params)})"


@dataclass
class TACFuncEnd(TACInstruction):
    """end_func name"""
    name: str
    def __str__(self):
        return f"end_func {self.name}"


@dataclass
class TACListCreate(TACInstruction):
    """result = [elements...]"""
    result: str
    elements: List[str]
    def __str__(self):
        return f"    {self.result} = [{', '.join(self.elements)}]"


@dataclass
class TACListAppend(TACInstruction):
    """collection.append(value)"""
    collection: str
    value: str
    def __str__(self):
        return f"    {self.collection}.append({self.value})"


@dataclass
class TACListRemove(TACInstruction):
    """collection.remove(value)"""
    collection: str
    value: str
    def __str__(self):
        return f"    {self.collection}.remove({self.value})"


@dataclass
class TACIndexAccess(TACInstruction):
    """result = collection[index]"""
    result: str
    collection: str
    index: str
    def __str__(self):
        return f"    {self.result} = {self.collection}[{self.index}]"


@dataclass
class TACLengthOf(TACInstruction):
    """result = length(collection)"""
    result: str
    collection: str
    def __str__(self):
        return f"    {self.result} = length({self.collection})"


@dataclass
class TACPropertyAccess(TACInstruction):
    """result = obj.prop"""
    result: str
    obj: str
    prop: str
    def __str__(self):
        return f"    {self.result} = {self.obj}.{self.prop}"


@dataclass
class TACPropertyAssign(TACInstruction):
    """obj.prop = value"""
    obj: str
    prop: str
    value: str
    def __str__(self):
        return f"    {self.obj}.{self.prop} = {self.value}"


@dataclass
class TACConcat(TACInstruction):
    """result = str(left) ++ str(right)"""
    result: str
    left: str
    right: str
    def __str__(self):
        return f"    {self.result} = str({self.left}) ++ str({self.right})"


@dataclass
class TACIsBetween(TACInstruction):
    """result = (low <= value <= high)"""
    result: str
    value: str
    low: str
    high: str
    def __str__(self):
        return f"    {self.result} = ({self.low} <= {self.value} <= {self.high})"


@dataclass
class TACTryBegin(TACInstruction):
    def __str__(self): return "    try_begin"

@dataclass
class TACTryEnd(TACInstruction):
    def __str__(self): return "    try_end"

@dataclass
class TACCatchBegin(TACInstruction):
    def __str__(self): return "    catch_begin"

@dataclass
class TACCatchEnd(TACInstruction):
    def __str__(self): return "    catch_end"
