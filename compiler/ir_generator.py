from .ast_nodes import *
from .tac import *


class IRGenerator:
    """
    Phase 5 – Intermediate Code (TAC) Generator.

    Translates the optimized AST into Three-Address Code (TAC):
    a flat sequence of simple instructions, each with at most
    three addresses (result, operand1, operand2).

    Naming convention
    -----------------
    Temporaries : _t0, _t1, _t2, ...
    Labels      : L0, L1, L2, ...
    """

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self._temp_count = 0
        self._label_count = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _new_temp(self) -> str:
        name = f"_t{self._temp_count}"
        self._temp_count += 1
        return name

    def _new_label(self) -> str:
        name = f"L{self._label_count}"
        self._label_count += 1
        return name

    def emit(self, instr: TACInstruction):
        self.instructions.append(instr)

    def get_code(self) -> str:
        return "\n".join(str(i) for i in self.instructions)

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------

    def generate(self, node: ASTNode) -> List[TACInstruction]:
        self.gen_stmt(node)
        return self.instructions

    # ------------------------------------------------------------------
    # Statement dispatch
    # ------------------------------------------------------------------

    def gen_stmt(self, node: ASTNode):
        method = f"_stmt_{node.__class__.__name__}"
        handler = getattr(self, method, None)
        if handler:
            handler(node)
        else:
            self.gen_expr(node)

    def _stmt_Program(self, node):
        for stmt in node.statements:
            self.gen_stmt(stmt)

    def _stmt_VarDecl(self, node):
        place = self.gen_expr(node.value)
        self.emit(TACCopy(node.name, place))

    def _stmt_Assign(self, node):
        place = self.gen_expr(node.value)
        self.emit(TACCopy(node.name, place))

    def _stmt_ShowStmt(self, node):
        place = self.gen_expr(node.expr)
        self.emit(TACPrint(place))

    def _stmt_AskStmt(self, node):
        self.emit(TACInput(node.var))

    def _stmt_ReturnStmt(self, node):
        place = self.gen_expr(node.expr)
        self.emit(TACReturn(place))

    def _stmt_FuncDef(self, node):
        self.emit(TACFuncBegin(node.name, node.params))
        for stmt in node.block:
            self.gen_stmt(stmt)
        self.emit(TACFuncEnd(node.name))

    def _stmt_FuncCall(self, node):
        for arg in node.args:
            place = self.gen_expr(arg)
            self.emit(TACParam(place))
        self.emit(TACCall(node.name, len(node.args), result=None))

    def _stmt_IfStmt(self, node):
        end_label = self._new_label()

        # Main condition
        cond_place = self.gen_expr(node.condition)
        skip_label = self._new_label()
        self.emit(TACIfFalseGoto(cond_place, skip_label))
        for stmt in node.then_block:
            self.gen_stmt(stmt)
        self.emit(TACGoto(end_label))
        self.emit(TACLabel(skip_label))

        # else-if chain
        for cond, block in node.else_if_stmts:
            elif_place = self.gen_expr(cond)
            elif_skip = self._new_label()
            self.emit(TACIfFalseGoto(elif_place, elif_skip))
            for stmt in block:
                self.gen_stmt(stmt)
            self.emit(TACGoto(end_label))
            self.emit(TACLabel(elif_skip))

        # else block
        if node.else_block:
            for stmt in node.else_block:
                self.gen_stmt(stmt)

        self.emit(TACLabel(end_label))

    def _stmt_WhileStmt(self, node):
        start_label = self._new_label()
        end_label = self._new_label()
        self.emit(TACLabel(start_label))
        cond_place = self.gen_expr(node.condition)
        self.emit(TACIfFalseGoto(cond_place, end_label))
        for stmt in node.block:
            self.gen_stmt(stmt)
        self.emit(TACGoto(start_label))
        self.emit(TACLabel(end_label))

    def _stmt_RepeatStmt(self, node):
        counter = self._new_temp()
        count_place = self.gen_expr(node.count)
        start_label = self._new_label()
        end_label = self._new_label()
        self.emit(TACCopy(counter, "0"))
        self.emit(TACLabel(start_label))
        cond_temp = self._new_temp()
        self.emit(TACBinOp(cond_temp, counter, "<", count_place))
        self.emit(TACIfFalseGoto(cond_temp, end_label))
        for stmt in node.block:
            self.gen_stmt(stmt)
        inc_temp = self._new_temp()
        self.emit(TACBinOp(inc_temp, counter, "+", "1"))
        self.emit(TACCopy(counter, inc_temp))
        self.emit(TACGoto(start_label))
        self.emit(TACLabel(end_label))

    def _stmt_ForEachStmt(self, node):
        idx = self._new_temp()
        length_temp = self._new_temp()
        start_label = self._new_label()
        end_label = self._new_label()
        self.emit(TACLengthOf(length_temp, node.collection))
        self.emit(TACCopy(idx, "0"))
        self.emit(TACLabel(start_label))
        cond_temp = self._new_temp()
        self.emit(TACBinOp(cond_temp, idx, "<", length_temp))
        self.emit(TACIfFalseGoto(cond_temp, end_label))
        self.emit(TACIndexAccess(node.item, node.collection, idx))
        for stmt in node.block:
            self.gen_stmt(stmt)
        inc_temp = self._new_temp()
        self.emit(TACBinOp(inc_temp, idx, "+", "1"))
        self.emit(TACCopy(idx, inc_temp))
        self.emit(TACGoto(start_label))
        self.emit(TACLabel(end_label))

    def _stmt_ForRangeStmt(self, node):
        start_place = self.gen_expr(node.start)
        end_place = self.gen_expr(node.end)
        start_label = self._new_label()
        end_label = self._new_label()
        self.emit(TACCopy(node.var, start_place))
        self.emit(TACLabel(start_label))
        cond_temp = self._new_temp()
        self.emit(TACBinOp(cond_temp, node.var, "<=", end_place))
        self.emit(TACIfFalseGoto(cond_temp, end_label))
        for stmt in node.block:
            self.gen_stmt(stmt)
        inc_temp = self._new_temp()
        self.emit(TACBinOp(inc_temp, node.var, "+", "1"))
        self.emit(TACCopy(node.var, inc_temp))
        self.emit(TACGoto(start_label))
        self.emit(TACLabel(end_label))

    def _stmt_AddStmt(self, node):
        place = self.gen_expr(node.item)
        self.emit(TACListAppend(node.collection, place))

    def _stmt_RemoveStmt(self, node):
        place = self.gen_expr(node.item)
        self.emit(TACListRemove(node.collection, place))

    def _stmt_PropertyAssign(self, node):
        place = self.gen_expr(node.value)
        self.emit(TACPropertyAssign(node.obj, node.prop, place))

    def _stmt_TryStmt(self, node):
        self.emit(TACTryBegin())
        for stmt in node.try_block:
            self.gen_stmt(stmt)
        self.emit(TACTryEnd())
        self.emit(TACCatchBegin())
        for stmt in node.error_block:
            self.gen_stmt(stmt)
        self.emit(TACCatchEnd())

    def _stmt_RecordDef(self, node):
        self.emit(TACFuncBegin(f"record:{node.name}", node.fields))
        self.emit(TACFuncEnd(f"record:{node.name}"))

    # ------------------------------------------------------------------
    # Expression dispatch  →  returns a "place" (temp name or literal)
    # ------------------------------------------------------------------

    def gen_expr(self, node: ASTNode) -> str:
        method = f"_expr_{node.__class__.__name__}"
        handler = getattr(self, method, None)
        if handler:
            return handler(node)
        raise NotImplementedError(f"No expression handler for {node.__class__.__name__}")

    def _expr_NumberLit(self, node) -> str:
        return str(node.value)

    def _expr_StringLit(self, node) -> str:
        return f'"{node.value}"'

    def _expr_BoolLit(self, node) -> str:
        return "true" if node.value else "false"

    def _expr_NullLit(self, node) -> str:
        return "null"

    def _expr_Identifier(self, node) -> str:
        return node.name

    def _expr_BinOp(self, node) -> str:
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        result = self._new_temp()
        self.emit(TACBinOp(result, left, node.op, right))
        return result

    def _expr_UnaryOp(self, node) -> str:
        operand = self.gen_expr(node.right)
        result = self._new_temp()
        self.emit(TACUnaryOp(result, node.op, operand))
        return result

    def _expr_Compare(self, node) -> str:
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        result = self._new_temp()
        self.emit(TACBinOp(result, left, node.op, right))
        return result

    def _expr_LogicalOp(self, node) -> str:
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        result = self._new_temp()
        self.emit(TACBinOp(result, left, node.op, right))
        return result

    def _expr_JoinedWith(self, node) -> str:
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        result = self._new_temp()
        self.emit(TACConcat(result, left, right))
        return result

    def _expr_IsBetween(self, node) -> str:
        value = self.gen_expr(node.value)
        low = self.gen_expr(node.low)
        high = self.gen_expr(node.high)
        result = self._new_temp()
        self.emit(TACIsBetween(result, value, low, high))
        return result

    def _expr_FirstItem(self, node) -> str:
        result = self._new_temp()
        self.emit(TACIndexAccess(result, node.collection, "0"))
        return result

    def _expr_LastItem(self, node) -> str:
        result = self._new_temp()
        self.emit(TACIndexAccess(result, node.collection, "-1"))
        return result

    def _expr_LengthOf(self, node) -> str:
        result = self._new_temp()
        self.emit(TACLengthOf(result, node.collection))
        return result

    def _expr_FuncCall(self, node) -> str:
        for arg in node.args:
            place = self.gen_expr(arg)
            self.emit(TACParam(place))
        result = self._new_temp()
        self.emit(TACCall(node.name, len(node.args), result=result))
        return result

    def _expr_PropertyAccess(self, node) -> str:
        result = self._new_temp()
        self.emit(TACPropertyAccess(result, node.obj, node.prop))
        return result

    def _expr_ListLit(self, node) -> str:
        elements = [self.gen_expr(e) for e in node.elements]
        result = self._new_temp()
        self.emit(TACListCreate(result, elements))
        return result
