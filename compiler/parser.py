from .lexer import Token
from .ast_nodes import *
from .errors import ParseError

class Parser:
    """Recursive descent parser for Plainscript."""

    def __init__(self, tokens, source_code):
        self.tokens = tokens
        self.pos = 0
        self.source_code = source_code
        self.lines = source_code.split('\n')

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return self.tokens[-1]

    def consume(self, expected_type=None):
        token = self.peek()
        if expected_type and token.type != expected_type:
            # Check if we can treat a keyword as an identifier
            if expected_type == 'TK_IDENTIFIER' and token.type.startswith('TK_KW_'):
                self.pos += 1
                return token
            line_text = self.lines[token.line - 1] if token.line <= len(self.lines) else ""
            raise ParseError(f"Expected {expected_type}, got {token.type}", token.line, token.col, line_text)
        self.pos += 1
        return token

    def consume_identifier(self):
        token = self.peek()
        if token.type == 'TK_IDENTIFIER' or token.type.startswith('TK_KW_'):
            self.pos += 1
            # Return a token that looks like an identifier
            return Token('TK_IDENTIFIER', token.value, token.line, token.col)
        line_text = self.lines[token.line - 1] if token.line <= len(self.lines) else ""
        raise ParseError(f"Expected identifier, got {token.type}", token.line, token.col, line_text)

    def match(self, *types):
        if self.peek().type in types:
            return self.consume()
        return None

    def expect(self, expected_type):
        return self.consume(expected_type)

    def parse(self):
        statements = []
        while self.peek().type != 'TK_EOF':
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            # Skip optional newlines between statements
            while self.match('TK_NEWLINE'):
                pass
        return Program(statements)

    def parse_block(self):
        """Shared block parsing logic."""
        self.expect('TK_NEWLINE')
        self.expect('TK_INDENT')
        stmts = []
        while self.peek().type != 'TK_DEDENT' and self.peek().type != 'TK_EOF':
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            while self.match('TK_NEWLINE'):
                pass
        self.expect('TK_DEDENT')
        return stmts

    def parse_statement(self):
        # Skip leading newlines in block
        while self.match('TK_NEWLINE'):
            pass
            
        token = self.peek()
        if token.type == 'TK_EOF' or token.type == 'TK_DEDENT':
            return None
            
        if token.type in ('TK_KW_SET', 'TK_KW_LET', 'TK_KW_DEFINE'):
            return self.parse_var_decl_or_assign()
        elif token.type == 'TK_KW_IF':
            return self.parse_if_stmt()
        elif token.type == 'TK_KW_WHILE':
            return self.parse_while_stmt()
        elif token.type == 'TK_KW_REPEAT':
            return self.parse_repeat_stmt()
        elif token.type == 'TK_KW_FOR_EACH':
            return self.parse_for_each_stmt()
        elif token.type == 'TK_KW_FOR_EVERY':
            return self.parse_for_range_stmt()
        elif token.type == 'TK_KW_DEFINE_ACTION':
            return self.parse_func_def()
        elif token.type == 'TK_KW_DEFINE_RECORD':
            return self.parse_record_def()
        elif token.type == 'TK_KW_SHOW':
            return self.parse_show_stmt()
        elif token.type == 'TK_KW_ASK_FOR':
            return self.parse_ask_stmt()
        elif token.type == 'TK_KW_RETURN':
            return self.parse_return_stmt()
        elif token.type == 'TK_KW_TRY':
            return self.parse_try_stmt()
        elif token.type == 'TK_KW_ADD':
            return self.parse_add_stmt()
        elif token.type == 'TK_KW_REMOVE':
            return self.parse_remove_stmt()
        elif token.type == 'TK_KW_CALL':
            return self.parse_func_call_stmt()
        elif token.type == 'TK_IDENTIFIER' and self.peek(1).type == 'TK_APOSTROPHE_S':
            return self.parse_property_assign()
        else:
            # Might be an expression (like a function call)
            expr = self.parse_expression()
            self.match('TK_NEWLINE')
            return expr

    def parse_var_decl_or_assign(self):
        self.consume() # set/let/define
        name = self.expect('TK_IDENTIFIER').value
        self.expect_any('TK_KW_TO', 'TK_KW_BE', 'TK_KW_AS')
        value = self.parse_expression()
        return VarDecl(name, value)

    def expect_any(self, *types):
        token = self.peek()
        if token.type in types:
            return self.consume()
        line_text = self.lines[token.line - 1]
        raise ParseError(f"Expected one of {types}, got {token.type}", token.line, token.col, line_text)

    def parse_if_stmt(self):
        self.expect('TK_KW_IF')
        condition = self.parse_expression()
        self.match('TK_KW_THEN')
        then_block = self.parse_block()
        
        else_if_stmts = []
        else_block = None
        
        while self.peek().type == 'TK_KW_OTHERWISE_IF':
            self.consume()
            elif_cond = self.parse_expression()
            self.match('TK_KW_THEN')
            elif_block = self.parse_block()
            else_if_stmts.append((elif_cond, elif_block))
            
        if self.peek().type == 'TK_KW_OTHERWISE':
            self.consume()
            else_block = self.parse_block()
            
        self.expect('TK_KW_END')
        return IfStmt(condition, then_block, else_if_stmts, else_block)

    def parse_while_stmt(self):
        self.expect('TK_KW_WHILE')
        condition = self.parse_expression()
        block = self.parse_block()
        self.expect('TK_KW_END')
        return WhileStmt(condition, block)

    def parse_repeat_stmt(self):
        self.expect('TK_KW_REPEAT')
        count = self.parse_expression()
        self.expect('TK_KW_TIMES')
        block = self.parse_block()
        self.expect('TK_KW_END')
        return RepeatStmt(count, block)

    def parse_for_each_stmt(self):
        self.expect('TK_KW_FOR_EACH')
        item = self.expect('TK_IDENTIFIER').value
        self.expect('TK_KW_IN')
        collection = self.expect('TK_IDENTIFIER').value
        block = self.parse_block()
        self.expect('TK_KW_END')
        return ForEachStmt(item, collection, block)

    def parse_for_range_stmt(self):
        self.expect('TK_KW_FOR_EVERY')
        var = self.expect('TK_IDENTIFIER').value
        self.expect('TK_KW_FROM')
        start = self.parse_expression()
        self.expect('TK_KW_TO')
        end = self.parse_expression()
        block = self.parse_block()
        self.expect('TK_KW_END')
        return ForRangeStmt(var, start, end, block)

    def parse_func_def(self):
        self.expect('TK_KW_DEFINE_ACTION')
        name = self.expect('TK_IDENTIFIER').value
        params = []
        if self.match('TK_KW_WITH'):
            params.append(self.expect('TK_IDENTIFIER').value)
            while self.match('TK_KW_AND'):
                params.append(self.expect('TK_IDENTIFIER').value)
        block = self.parse_block()
        self.expect('TK_KW_END')
        return FuncDef(name, params, block)

    def parse_record_def(self):
        self.expect('TK_KW_DEFINE_RECORD')
        name = self.expect('TK_IDENTIFIER').value
        self.expect('TK_NEWLINE')
        self.expect('TK_INDENT')
        fields = []
        while self.peek().type == 'TK_IDENTIFIER':
            fields.append(self.consume().value)
            self.expect('TK_NEWLINE')
        self.expect('TK_DEDENT')
        self.expect('TK_KW_END')
        return RecordDef(name, fields)

    def parse_show_stmt(self):
        self.expect('TK_KW_SHOW')
        expr = self.parse_expression()
        return ShowStmt(expr)

    def parse_ask_stmt(self):
        self.expect('TK_KW_ASK_FOR')
        var = self.expect('TK_IDENTIFIER').value
        return AskStmt(var)

    def parse_return_stmt(self):
        self.expect('TK_KW_RETURN')
        expr = self.parse_expression()
        return ReturnStmt(expr)

    def parse_try_stmt(self):
        self.expect('TK_KW_TRY')
        try_block = self.parse_block()
        self.expect('TK_KW_IF_ERROR')
        error_block = self.parse_block()
        self.expect('TK_KW_END')
        return TryStmt(try_block, error_block)

    def parse_add_stmt(self):
        self.expect('TK_KW_ADD')
        item = self.parse_expression()
        self.expect('TK_KW_TO')
        collection = self.expect('TK_IDENTIFIER').value
        return AddStmt(item, collection)

    def parse_remove_stmt(self):
        self.expect('TK_KW_REMOVE')
        item = self.parse_expression()
        self.expect('TK_KW_FROM')
        collection = self.expect('TK_IDENTIFIER').value
        return RemoveStmt(item, collection)

    def parse_func_call_stmt(self):
        return self.parse_func_call()

    def parse_property_assign(self):
        obj = self.expect('TK_IDENTIFIER').value
        self.expect('TK_APOSTROPHE_S')
        prop = self.expect('TK_IDENTIFIER').value
        self.expect('TK_KW_TO')
        value = self.parse_expression()
        return PropertyAssign(obj, prop, value)

    # Expression parsing (Operator Precedence)
    def parse_expression(self, allow_and=True):
        return self.parse_logical_or(allow_and)

    def parse_logical_or(self, allow_and=True):
        node = self.parse_logical_and(allow_and)
        while self.match('TK_KW_OR'):
            right = self.parse_logical_and(allow_and)
            node = LogicalOp(node, 'or', right)
        return node

    def parse_logical_and(self, allow_and=True):
        node = self.parse_comparison()
        if not allow_and:
            return node
        while self.match('TK_KW_AND'):
            right = self.parse_comparison()
            node = LogicalOp(node, 'and', right)
        return node

    def parse_comparison(self, allow_and=True):
        node = self.parse_arithmetic(allow_and)
        
        # Special case: is between
        if self.match('TK_KW_IS_BETWEEN'):
            low = self.parse_arithmetic(allow_and)
            self.expect('TK_KW_AND')
            high = self.parse_arithmetic(allow_and)
            return IsBetween(node, low, high)
            
        op_token = self.match(
            'TK_KW_IS', 'TK_KW_IS_NOT', 'TK_KW_IS_GREATER_THAN', 
            'TK_KW_IS_LESS_THAN', 'TK_KW_IS_AT_LEAST', 'TK_KW_IS_AT_MOST'
        )
        if op_token:
            right = self.parse_arithmetic(allow_and)
            op_map = {
                'TK_KW_IS': '==',
                'TK_KW_IS_NOT': '!=',
                'TK_KW_IS_GREATER_THAN': '>',
                'TK_KW_IS_LESS_THAN': '<',
                'TK_KW_IS_AT_LEAST': '>=',
                'TK_KW_IS_AT_MOST': '<=',
            }
            return Compare(node, op_map[op_token.type], right)
        return node

    def parse_arithmetic(self, allow_and=True):
        node = self.parse_term(allow_and)
        while True:
            op_token = self.match('TK_KW_PLUS', 'TK_KW_MINUS', 'TK_KW_JOINED_WITH')
            if op_token:
                right = self.parse_term(allow_and)
                if op_token.type == 'TK_KW_JOINED_WITH':
                    node = JoinedWith(node, right)
                else:
                    op = '+' if op_token.type == 'TK_KW_PLUS' else '-'
                    node = BinOp(node, op, right)
            else:
                break
        return node

    def parse_term(self, allow_and=True):
        node = self.parse_factor(allow_and)
        while True:
            op_token = self.match('TK_KW_TIMES', 'TK_KW_DIVIDED_BY', 'TK_KW_MOD', 'TK_KW_TO_THE_POWER_OF')
            if op_token:
                right = self.parse_factor(allow_and)
                op_map = {
                    'TK_KW_TIMES': '*',
                    'TK_KW_DIVIDED_BY': '/',
                    'TK_KW_MOD': '%',
                    'TK_KW_TO_THE_POWER_OF': '**'
                }
                node = BinOp(node, op_map[op_token.type], right)
            else:
                break
        return node

    def parse_factor(self, allow_and=True):
        token = self.peek()
        
        if self.match('TK_KW_NOT'):
            return UnaryOp('not', self.parse_factor(allow_and))
            
        if self.match('TK_KW_CALL'):
            return self.parse_func_call()
            
        if self.match('TK_KW_FIRST_ITEM'):
            self.expect('TK_KW_IN')
            collection = self.expect('TK_IDENTIFIER').value
            return FirstItem(collection)
            
        if self.match('TK_KW_LAST_ITEM'):
            self.expect('TK_KW_IN')
            collection = self.expect('TK_IDENTIFIER').value
            return LastItem(collection)
            
        if self.match('TK_KW_LENGTH_OF'):
            collection = self.expect('TK_IDENTIFIER').value
            return LengthOf(collection)
            
        if token.type == 'TK_NUMBER_INT':
            return NumberLit(int(self.consume().value))
        if token.type == 'TK_NUMBER_FLOAT':
            return NumberLit(float(self.consume().value))
        if token.type == 'TK_STRING':
            return StringLit(self.consume().value)
        if token.type == 'TK_BOOLEAN':
            return BoolLit(self.consume().value)
        if token.type == 'TK_NULL':
            self.consume()
            return NullLit()
            
        if token.type == 'TK_LBRACKET':
            return self.parse_list_literal()
            
        if self.match('TK_LPAREN'):
            expr = self.parse_expression(allow_and=True)
            self.expect('TK_RPAREN')
            return expr
            
        if token.type == 'TK_IDENTIFIER':
            name = self.consume().value
            if self.peek().type == 'TK_APOSTROPHE_S':
                self.consume()
                prop = self.expect('TK_IDENTIFIER').value
                return PropertyAccess(name, prop)
            return Identifier(name)
            
        raise ParseError(f"Unexpected token in expression: {token.type}", token.line, token.col)

    def parse_list_literal(self):
        self.expect('TK_LBRACKET')
        elements = []
        if self.peek().type != 'TK_RBRACKET':
            elements.append(self.parse_expression())
            while self.match('TK_COMMA'):
                elements.append(self.parse_expression())
        self.expect('TK_RBRACKET')
        return ListLit(elements)

    def parse_func_call(self):
        # 'call' is already consumed if coming from parse_factor or parse_statement
        if self.peek().type == 'TK_KW_CALL':
            self.consume()
        name = self.expect('TK_IDENTIFIER').value
        args = []
        if self.match('TK_KW_WITH'):
            args.append(self.parse_expression(allow_and=False))
            while self.match('TK_KW_AND'):
                args.append(self.parse_expression(allow_and=False))
        return FuncCall(name, args)
