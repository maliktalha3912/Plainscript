import pytest
from plainscript.compiler.lexer import Lexer
from plainscript.compiler.parser import Parser

def test_parser_basic():
    code = 'set x to 10'
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code)
    ast = parser.parse()
    assert len(ast.statements) == 1
    assert ast.statements[0].name == 'x'

def test_parser_if():
    code = "if true then\n    show 1\nend"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code)
    ast = parser.parse()
    assert ast.statements[0].__class__.__name__ == 'IfStmt'
