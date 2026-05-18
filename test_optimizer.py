from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.optimizer import ASTOptimizer
from compiler.ir_generator import IRGenerator
from compiler.codegen import CodeGenerator
from runtime.executor import Executor

code = (
    "set x to 2 plus 3\n"
    "show x\n"
    "set y to 10 times 0\n"
    "show y\n"
    'set z to "hello" joined with " world"\n'
    "show z\n"
    "if true then\n"
    "    show \"branch kept\"\n"
    "end\n"
    "define action greet with name\n"
    "    show \"Hi \" joined with name\n"
    "    return 1\n"
    "    show \"dead code\"\n"
    "end\n"
    "call greet with \"Alice\"\n"
)

print("=" * 55)
print("PLAINSCRIPT COMPILER — ALL 6 PHASES")
print("=" * 55)

# Phase 1
print("\n=== PHASE 1: LEXICAL ANALYSIS (Lexer) ===")
lexer = Lexer(code)
tokens = lexer.tokenize()
for t in tokens:
    print(t)

# Phase 2
print("\n=== PHASE 2: SYNTAX ANALYSIS (Recursive Descent Parser) ===")
import pprint, io
parser = Parser(tokens, code)
ast = parser.parse()
buf = io.StringIO()
pprint.pprint(ast, stream=buf)
print(buf.getvalue())

# Phase 3
print("=== PHASE 3: SEMANTIC ANALYSIS ===")
analyzer = SemanticAnalyzer()
analyzer.analyze(ast)
print("Semantic analysis completed successfully.")
print("Symbols:", list(analyzer.global_scope.symbols.keys()))

# Phase 4
print("\n=== PHASE 4: OPTIMIZATION (AST-Level) ===")
optimizer = ASTOptimizer()
ast = optimizer.optimize(ast)
print(optimizer.report.summary())

# Phase 5
print("\n=== PHASE 5: INTERMEDIATE CODE GENERATION (TAC) ===")
ir_gen = IRGenerator()
ir_gen.generate(ast)
print(ir_gen.get_code())

# Phase 6
print("\n=== PHASE 6: CODE GENERATION & EXECUTION ===")
gen = CodeGenerator()
python_code = gen.generate(ast)
print("--- Generated Python ---")
print(python_code)
print("\n--- Execution Output ---")
ex = Executor()
result = ex.run(python_code)
print(result["output"])
if result["error"]:
    print("ERROR:", result["error"])
