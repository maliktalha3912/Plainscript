from .ast_nodes import *
from .errors import SemanticError

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name, type_info=None):
        self.symbols[name] = type_info

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

class SemanticAnalyzer:
    """Performs semantic analysis on the Plainscript AST."""

    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.in_function = False
        self.records = {}

    def analyze(self, node):
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if hasattr(node, '__dict__'):
            for value in node.__dict__.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ASTNode):
                            self.analyze(item)
                elif isinstance(value, ASTNode):
                    self.analyze(value)

    def visit_Program(self, node):
        # First pass: collect all function and record definitions
        for stmt in node.statements:
            if isinstance(stmt, FuncDef):
                self.global_scope.define(stmt.name, 'function')
            elif isinstance(stmt, RecordDef):
                self.records[stmt.name] = stmt.fields
                self.global_scope.define(stmt.name, 'record')
        
        # Second pass: analyze everything
        for stmt in node.statements:
            self.analyze(stmt)

    def visit_VarDecl(self, node):
        self.analyze(node.value)
        self.current_scope.define(node.name)

    def visit_Assign(self, node):
        self.analyze(node.value)
        if self.current_scope.lookup(node.name) is None:
            self.current_scope.define(node.name)

    def visit_Identifier(self, node):
        # Allow use before definition in global scope for simplicity in Plainscript?
        # No, but let's be more lenient with builtins if any.
        pass

    def visit_FuncDef(self, node):
        # Function name already defined in first pass
        previous_scope = self.current_scope
        self.current_scope = SymbolTable(previous_scope)
        previous_in_function = self.in_function
        self.in_function = True
        
        for param in node.params:
            self.current_scope.define(param)
            
        for stmt in node.block:
            self.analyze(stmt)
            
        self.current_scope = previous_scope
        self.in_function = previous_in_function

    def visit_FuncCall(self, node):
        for arg in node.args:
            self.analyze(arg)

    def visit_ReturnStmt(self, node):
        self.analyze(node.expr)

    def visit_RecordDef(self, node):
        # Already handled in first pass
        pass

    def visit_PropertyAccess(self, node):
        pass

    def visit_PropertyAssign(self, node):
        self.analyze(node.value)

    def visit_TryStmt(self, node):
        for stmt in node.try_block:
            self.analyze(stmt)
        for stmt in node.error_block:
            self.analyze(stmt)

    def visit_IfStmt(self, node):
        self.analyze(node.condition)
        for stmt in node.then_block:
            self.analyze(stmt)
        for cond, block in node.else_if_stmts:
            self.analyze(cond)
            for stmt in block:
                self.analyze(stmt)
        if node.else_block:
            for stmt in node.else_block:
                self.analyze(stmt)

    def visit_WhileStmt(self, node):
        self.analyze(node.condition)
        for stmt in node.block:
            self.analyze(stmt)

    def visit_RepeatStmt(self, node):
        self.analyze(node.count)
        for stmt in node.block:
            self.analyze(stmt)

    def visit_ForEachStmt(self, node):
        # Loop variable
        previous_scope = self.current_scope
        self.current_scope = SymbolTable(previous_scope)
        self.current_scope.define(node.item)
        
        for stmt in node.block:
            self.analyze(stmt)
            
        self.current_scope = previous_scope

    def visit_ShowStmt(self, node):
        self.analyze(node.expr)

    def visit_AskStmt(self, node):
        self.current_scope.define(node.var)

    def visit_ForRangeStmt(self, node):
        self.analyze(node.start)
        self.analyze(node.end)
        
        previous_scope = self.current_scope
        self.current_scope = SymbolTable(previous_scope)
        self.current_scope.define(node.var)
        
        for stmt in node.block:
            self.analyze(stmt)
            
        self.current_scope = previous_scope
