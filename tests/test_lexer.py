import pytest
from plainscript.compiler.lexer import Lexer

def test_basic_tokens():
    code = 'set age to 25'
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    # age, to, 25, EOF (noise words handled, but none here)
    types = [t.type for t in tokens]
    assert 'TK_KW_SET' in types
    assert 'TK_IDENTIFIER' in types
    assert 'TK_KW_TO' in types
    assert 'TK_NUMBER_INT' in types

def test_multi_word_keywords():
    code = 'if x is greater than 10 then'
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert 'TK_KW_IS_GREATER_THAN' in types

def test_noise_words():
    code = 'show the result'
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    values = [t.value for t in tokens]
    assert 'the' not in values
    assert 'result' in values

def test_indentation():
    code = "if true then\n    show 1\nend"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert 'TK_INDENT' in types
    assert 'TK_DEDENT' in types
