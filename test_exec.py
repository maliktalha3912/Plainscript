from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.codegen import CodeGenerator
from runtime.executor import Executor

code = 'show "hello world"'
tokens = Lexer(code).tokenize()
ast = Parser(tokens, code).parse()
py = CodeGenerator().generate(ast)
print("Generated Python:\n" + py)

executor = Executor()
result = executor.run(py)
print("Execution Result:", result)
