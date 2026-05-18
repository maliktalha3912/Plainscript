from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.codegen import CodeGenerator
from runtime.executor import Executor
from compiler.semantic import SemanticAnalyzer

code = """
// Calculator
define action add with a and b
    return a plus b
end

define action multiply with a and b
    return a times b
end

set sum to call add with 10 and 5
show "Sum: " joined with sum

set product to call multiply with 4 and 3
show "Product: " joined with product
"""
try:
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens, code).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    py = CodeGenerator().generate(ast)
    print("Generated Python:\n" + py)

    executor = Executor()
    result = executor.run(py)
    print("Execution Result:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
