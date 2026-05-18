from .ast_nodes import (
    ASTNode, Program, VarDecl, Assign, IfStmt, WhileStmt, RepeatStmt,
    ForEachStmt, ForRangeStmt, FuncDef, FuncCall, ShowStmt, AskStmt,
    ReturnStmt, TryStmt, RecordDef, AddStmt, RemoveStmt, BinOp, UnaryOp,
    Compare, LogicalOp, Identifier, NumberLit, StringLit, BoolLit,
    NullLit, ListLit, PropertyAccess, PropertyAssign, JoinedWith,
    IsBetween, FirstItem, LastItem, LengthOf
)


class OptimizationReport:
    """Tracks what the optimizer changed."""

    def __init__(self):
        self.changes = []

    def record(self, technique, before, after):
        self.changes.append({
            "technique": technique,
            "before": before,
            "after": after,
        })

    def summary(self):
        if not self.changes:
            return "No optimizations applied."
        lines = [f"  [{c['technique']}] {c['before']}  =>  {c['after']}"
                 for c in self.changes]
        return f"{len(self.changes)} optimization(s) applied:\n" + "\n".join(lines)

    def to_list(self):
        return self.changes


class ASTOptimizer:
    """
    Phase 3.5 – AST Optimization.

    Performs source-level optimizations on the Plainscript AST before
    code generation.  All passes are purely structural: program semantics
    are never altered.

    Techniques implemented
    ----------------------
    1. Constant Folding      – evaluate arithmetic/string ops on literals.
    2. Boolean Simplification– simplify 'not true', 'not false'.
    3. Algebraic Simplification
                             – x + 0 → x,  x * 1 → x,  x * 0 → 0, etc.
    4. If-Constant Pruning   – replace 'if true/false ...' with the live branch.
    5. Dead Code Elimination – drop statements that follow a return in a block.
    6. IsBetween Folding     – evaluate 'N is between A and B' on literals.
    """

    def __init__(self):
        self.report = OptimizationReport()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def optimize(self, node):
        """Optimize a node and return the (possibly replaced) node."""
        method = f"_opt_{node.__class__.__name__}"
        handler = getattr(self, method, self._opt_generic)
        return handler(node)

    # ------------------------------------------------------------------
    # Program / block helpers
    # ------------------------------------------------------------------

    def _opt_generic(self, node):
        """Recursively optimize any node whose class has no specific handler."""
        if hasattr(node, "__dataclass_fields__"):
            for field_name in node.__dataclass_fields__:
                child = getattr(node, field_name)
                if isinstance(child, ASTNode):
                    setattr(node, field_name, self.optimize(child))
                elif isinstance(child, list):
                    setattr(node, field_name,
                            [self.optimize(item) if isinstance(item, ASTNode)
                             else item for item in child])
        return node

    def _optimize_block(self, stmts):
        """Optimize a list of statements and apply dead code elimination."""
        optimized = []
        for stmt in stmts:
            optimized.append(self.optimize(stmt))
            # Dead Code Elimination: nothing after a return matters.
            if isinstance(stmt, ReturnStmt):
                remaining = stmts[stmts.index(stmt) + 1:]
                if remaining:
                    self.report.record(
                        "Dead Code Elimination",
                        f"{len(remaining)} statement(s) after 'return'",
                        "removed"
                    )
                break
        return optimized

    def _opt_Program(self, node):
        node.statements = self._optimize_block(node.statements)
        return node

    def _opt_FuncDef(self, node):
        node.block = self._optimize_block(node.block)
        return node

    def _opt_WhileStmt(self, node):
        node.condition = self.optimize(node.condition)
        node.block = self._optimize_block(node.block)
        return node

    def _opt_RepeatStmt(self, node):
        node.count = self.optimize(node.count)
        node.block = self._optimize_block(node.block)
        return node

    def _opt_ForEachStmt(self, node):
        node.block = self._optimize_block(node.block)
        return node

    def _opt_ForRangeStmt(self, node):
        node.start = self.optimize(node.start)
        node.end = self.optimize(node.end)
        node.block = self._optimize_block(node.block)
        return node

    def _opt_TryStmt(self, node):
        node.try_block = self._optimize_block(node.try_block)
        node.error_block = self._optimize_block(node.error_block)
        return node

    def _opt_VarDecl(self, node):
        node.value = self.optimize(node.value)
        return node

    def _opt_Assign(self, node):
        node.value = self.optimize(node.value)
        return node

    def _opt_ShowStmt(self, node):
        node.expr = self.optimize(node.expr)
        return node

    def _opt_ReturnStmt(self, node):
        node.expr = self.optimize(node.expr)
        return node

    def _opt_AddStmt(self, node):
        node.item = self.optimize(node.item)
        return node

    def _opt_RemoveStmt(self, node):
        node.item = self.optimize(node.item)
        return node

    def _opt_PropertyAssign(self, node):
        node.value = self.optimize(node.value)
        return node

    def _opt_FuncCall(self, node):
        node.args = [self.optimize(a) for a in node.args]
        return node

    # ------------------------------------------------------------------
    # Technique 1 & 3: Constant Folding + Algebraic Simplification (BinOp)
    # ------------------------------------------------------------------

    def _opt_BinOp(self, node):
        left = self.optimize(node.left)
        right = self.optimize(node.right)
        node.left = left
        node.right = right

        # --- Constant Folding: both operands are number literals ---
        if isinstance(left, NumberLit) and isinstance(right, NumberLit):
            lv, rv = left.value, right.value
            result = None
            try:
                if node.op == "+":
                    result = lv + rv
                elif node.op == "-":
                    result = lv - rv
                elif node.op == "*":
                    result = lv * rv
                elif node.op == "/" and rv != 0:
                    result = lv / rv
                elif node.op == "%" and rv != 0:
                    result = lv % rv
                elif node.op == "**":
                    result = lv ** rv
            except Exception:
                pass

            if result is not None:
                before = f"({lv} {node.op} {rv})"
                self.report.record("Constant Folding", before, str(result))
                return NumberLit(result)

        # --- Algebraic Simplification ---
        # x + 0 or 0 + x  =>  x
        if node.op == "+":
            if isinstance(right, NumberLit) and right.value == 0:
                self.report.record("Algebraic Simplification", f"expr + 0", "expr")
                return left
            if isinstance(left, NumberLit) and left.value == 0:
                self.report.record("Algebraic Simplification", "0 + expr", "expr")
                return right

        # x - 0  =>  x
        if node.op == "-" and isinstance(right, NumberLit) and right.value == 0:
            self.report.record("Algebraic Simplification", "expr - 0", "expr")
            return left

        # x * 1 or 1 * x  =>  x
        if node.op == "*":
            if isinstance(right, NumberLit) and right.value == 1:
                self.report.record("Algebraic Simplification", "expr * 1", "expr")
                return left
            if isinstance(left, NumberLit) and left.value == 1:
                self.report.record("Algebraic Simplification", "1 * expr", "expr")
                return right
            # x * 0 or 0 * x  =>  0
            if (isinstance(right, NumberLit) and right.value == 0) or \
               (isinstance(left, NumberLit) and left.value == 0):
                self.report.record("Algebraic Simplification", "expr * 0", "0")
                return NumberLit(0)

        # x ** 1  =>  x
        if node.op == "**" and isinstance(right, NumberLit) and right.value == 1:
            self.report.record("Algebraic Simplification", "expr ** 1", "expr")
            return left

        # x ** 0  =>  1
        if node.op == "**" and isinstance(right, NumberLit) and right.value == 0:
            self.report.record("Algebraic Simplification", "expr ** 0", "1")
            return NumberLit(1)

        return node

    # ------------------------------------------------------------------
    # Technique 1: Constant Folding (JoinedWith / string concatenation)
    # ------------------------------------------------------------------

    def _opt_JoinedWith(self, node):
        left = self.optimize(node.left)
        right = self.optimize(node.right)
        node.left = left
        node.right = right

        if isinstance(left, StringLit) and isinstance(right, StringLit):
            result = left.value + right.value
            self.report.record(
                "Constant Folding (String)",
                f'"{left.value}" joined with "{right.value}"',
                f'"{result}"'
            )
            return StringLit(result)

        return node

    # ------------------------------------------------------------------
    # Technique 6: IsBetween Folding
    # ------------------------------------------------------------------

    def _opt_IsBetween(self, node):
        value = self.optimize(node.value)
        low = self.optimize(node.low)
        high = self.optimize(node.high)
        node.value = value
        node.low = low
        node.high = high

        if isinstance(value, NumberLit) and isinstance(low, NumberLit) and isinstance(high, NumberLit):
            result = low.value <= value.value <= high.value
            self.report.record(
                "IsBetween Folding",
                f"{value.value} is between {low.value} and {high.value}",
                str(result).lower()
            )
            return BoolLit(result)

        return node

    # ------------------------------------------------------------------
    # Technique 2: Boolean Simplification (UnaryOp not)
    # ------------------------------------------------------------------

    def _opt_UnaryOp(self, node):
        right = self.optimize(node.right)
        node.right = right

        if node.op == "not" and isinstance(right, BoolLit):
            result = not right.value
            self.report.record(
                "Boolean Simplification",
                f"not {right.value}",
                str(result).lower()
            )
            return BoolLit(result)

        return node

    # ------------------------------------------------------------------
    # Constant Folding: Compare on literals
    # ------------------------------------------------------------------

    def _opt_Compare(self, node):
        left = self.optimize(node.left)
        right = self.optimize(node.right)
        node.left = left
        node.right = right

        if isinstance(left, NumberLit) and isinstance(right, NumberLit):
            lv, rv = left.value, right.value
            ops = {
                "==": lv == rv,
                "!=": lv != rv,
                ">":  lv > rv,
                "<":  lv < rv,
                ">=": lv >= rv,
                "<=": lv <= rv,
            }
            if node.op in ops:
                result = ops[node.op]
                self.report.record(
                    "Constant Folding (Compare)",
                    f"{lv} {node.op} {rv}",
                    str(result).lower()
                )
                return BoolLit(result)

        return node

    # ------------------------------------------------------------------
    # Constant Folding: LogicalOp on literals
    # ------------------------------------------------------------------

    def _opt_LogicalOp(self, node):
        left = self.optimize(node.left)
        right = self.optimize(node.right)
        node.left = left
        node.right = right

        if isinstance(left, BoolLit) and isinstance(right, BoolLit):
            lv, rv = left.value, right.value
            result = (lv and rv) if node.op == "and" else (lv or rv)
            self.report.record(
                "Constant Folding (Logical)",
                f"{lv} {node.op} {rv}",
                str(result).lower()
            )
            return BoolLit(result)

        # Short-circuit: false and X => false,  true or X => true
        if node.op == "and" and isinstance(left, BoolLit) and not left.value:
            self.report.record("Short-Circuit Elimination", "false and expr", "false")
            return BoolLit(False)
        if node.op == "or" and isinstance(left, BoolLit) and left.value:
            self.report.record("Short-Circuit Elimination", "true or expr", "true")
            return BoolLit(True)

        return node

    # ------------------------------------------------------------------
    # Technique 4: If-Constant Pruning
    # ------------------------------------------------------------------

    def _opt_IfStmt(self, node):
        node.condition = self.optimize(node.condition)
        # Optimize sub-blocks regardless
        node.then_block = self._optimize_block(node.then_block)
        node.else_if_stmts = [
            (self.optimize(cond), self._optimize_block(blk))
            for cond, blk in node.else_if_stmts
        ]
        if node.else_block is not None:
            node.else_block = self._optimize_block(node.else_block)

        if isinstance(node.condition, BoolLit):
            if node.condition.value:
                # 'if true' — keep only the then-block
                self.report.record(
                    "If-Constant Pruning",
                    "if true ... (else branches)",
                    "then-block only"
                )
                # Return a Program-like wrapper; caller gets a list merged in
                return _InlinedBlock(node.then_block)
            else:
                # 'if false' — drop then-block, use else-if chain or else
                self.report.record(
                    "If-Constant Pruning",
                    "if false ... then-block",
                    "else-block / removed"
                )
                if node.else_block:
                    return _InlinedBlock(node.else_block)
                # No else: remove the whole if
                return _InlinedBlock([])

        return node


# ---------------------------------------------------------------------------
# Internal sentinel used when If-Constant Pruning inlines a block in place
# of an IfStmt.  _optimize_block flattens these automatically.
# ---------------------------------------------------------------------------

class _InlinedBlock(ASTNode):
    """Sentinel: a list of statements to be spliced into the parent block."""
    def __init__(self, stmts):
        self.stmts = stmts


# Patch _optimize_block to handle _InlinedBlock sentinels
_original_opt_block = ASTOptimizer._optimize_block


def _patched_optimize_block(self, stmts):
    result = []
    hit_return = False
    for stmt in stmts:
        if hit_return:
            break
        opt = self.optimize(stmt)
        if isinstance(opt, _InlinedBlock):
            result.extend(opt.stmts)
        else:
            result.append(opt)
        if isinstance(stmt, ReturnStmt):
            remaining_idx = stmts.index(stmt) + 1
            remaining = stmts[remaining_idx:]
            if remaining:
                self.report.record(
                    "Dead Code Elimination",
                    f"{len(remaining)} statement(s) after 'return'",
                    "removed"
                )
            hit_return = True
    return result


ASTOptimizer._optimize_block = _patched_optimize_block
