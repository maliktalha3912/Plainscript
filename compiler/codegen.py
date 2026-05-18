from .ast_nodes import *

class CodeGenerator:
    """Generates Python 3 source code from Plainscript AST."""

    def __init__(self):
        self.indent_level = 0

    def generate(self, node):
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name)
        return visitor(node)

    def indent(self):
        return "    " * self.indent_level

    def visit_Program(self, node):
        lines = []
        # Import dataclasses if records are defined
        has_records = any(isinstance(s, RecordDef) for s in node.statements)
        if has_records:
            lines.append("from dataclasses import dataclass")
            lines.append("")
            
        for stmt in node.statements:
            lines.append(self.generate(stmt))
        return "\n".join(lines)

    def visit_VarDecl(self, node):
        return f"{self.indent()}{node.name} = {self.generate(node.value)}"

    def visit_Assign(self, node):
        return f"{self.indent()}{node.name} = {self.generate(node.value)}"

    def visit_IfStmt(self, node):
        res = f"{self.indent()}if {self.generate(node.condition)}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.then_block)
        self.indent_level -= 1
        
        for cond, block in node.else_if_stmts:
            res += f"\n{self.indent()}elif {self.generate(cond)}:\n"
            self.indent_level += 1
            res += "\n".join(self.generate(s) for s in block)
            self.indent_level -= 1
            
        if node.else_block:
            res += f"\n{self.indent()}else:\n"
            self.indent_level += 1
            res += "\n".join(self.generate(s) for s in node.else_block)
            self.indent_level -= 1
        return res

    def visit_WhileStmt(self, node):
        res = f"{self.indent()}while {self.generate(node.condition)}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.block)
        self.indent_level -= 1
        return res

    def visit_RepeatStmt(self, node):
        # Use a unique iterator name to avoid collisions
        iter_name = f"_i{self.indent_level}"
        res = f"{self.indent()}for {iter_name} in range({self.generate(node.count)}):\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.block)
        self.indent_level -= 1
        return res

    def visit_ForEachStmt(self, node):
        res = f"{self.indent()}for {node.item} in {node.collection}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.block)
        self.indent_level -= 1
        return res

    def visit_ForRangeStmt(self, node):
        res = f"{self.indent()}for {node.var} in range({self.generate(node.start)}, {self.generate(node.end)} + 1):\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.block)
        self.indent_level -= 1
        return res

    def visit_FuncDef(self, node):
        params = ", ".join(node.params)
        res = f"{self.indent()}def {node.name}({params}):\n"
        self.indent_level += 1
        if not node.block:
            res += f"{self.indent()}pass"
        else:
            res += "\n".join(self.generate(s) for s in node.block)
        self.indent_level -= 1
        return res

    def visit_FuncCall(self, node):
        args = ", ".join(self.generate(a) for a in node.args)
        return f"{node.name}({args})"

    def visit_ShowStmt(self, node):
        return f"{self.indent()}print({self.generate(node.expr)})"

    def visit_AskStmt(self, node):
        return f"{self.indent()}{node.var} = input()"

    def visit_ReturnStmt(self, node):
        return f"{self.indent()}return {self.generate(node.expr)}"

    def visit_TryStmt(self, node):
        res = f"{self.indent()}try:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.try_block)
        self.indent_level -= 1
        res += f"\n{self.indent()}except Exception:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(s) for s in node.error_block)
        self.indent_level -= 1
        return res

    def visit_RecordDef(self, node):
        res = f"{self.indent()}@dataclass\n{self.indent()}class {node.name}:\n"
        self.indent_level += 1
        for field in node.fields:
            res += f"{self.indent()}{field}: object = None\n"
        if not node.fields:
            res += f"{self.indent()}pass\n"
        self.indent_level -= 1
        return res

    def visit_AddStmt(self, node):
        return f"{self.indent()}{node.collection}.append({self.generate(node.item)})"

    def visit_RemoveStmt(self, node):
        return f"{self.indent()}{node.collection}.remove({self.generate(node.item)})"

    def visit_BinOp(self, node):
        return f"({self.generate(node.left)} {node.op} {self.generate(node.right)})"

    def visit_UnaryOp(self, node):
        return f"({node.op} {self.generate(node.right)})"

    def visit_Compare(self, node):
        return f"({self.generate(node.left)} {node.op} {self.generate(node.right)})"

    def visit_LogicalOp(self, node):
        return f"({self.generate(node.left)} {node.op} {self.generate(node.right)})"

    def visit_Identifier(self, node):
        return node.name

    def visit_NumberLit(self, node):
        return str(node.value)

    def visit_StringLit(self, node):
        return f'"{node.value}"'

    def visit_BoolLit(self, node):
        return "True" if node.value else "False"

    def visit_NullLit(self, node):
        return "None"

    def visit_ListLit(self, node):
        elements = ", ".join(self.generate(e) for e in node.elements)
        return f"[{elements}]"

    def visit_PropertyAccess(self, node):
        return f"{node.obj}.{node.prop}"

    def visit_PropertyAssign(self, node):
        return f"{self.indent()}{node.obj}.{node.prop} = {self.generate(node.value)}"

    def visit_JoinedWith(self, node):
        return f"(str({self.generate(node.left)}) + str({self.generate(node.right)}))"

    def visit_IsBetween(self, node):
        val = self.generate(node.value)
        low = self.generate(node.low)
        high = self.generate(node.high)
        return f"({val} >= {low} and {val} <= {high})"

    def visit_FirstItem(self, node):
        return f"{node.collection}[0]"

    def visit_LastItem(self, node):
        return f"{node.collection}[-1]"

    def visit_LengthOf(self, node):
        return f"len({node.collection})"
