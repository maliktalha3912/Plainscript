import argparse
import sys
import os
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.codegen import CodeGenerator
from runtime.executor import Executor
from compiler.errors import PlainscriptError

def run_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    with open(file_path, 'r') as f:
        code = f.read()

    try:
        print("=== PHASE 1: LEXICAL ANALYSIS (Lexer) ===")
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        for t in tokens:
            print(t)
        
        print("\n=== PHASE 2: SYNTAX ANALYSIS ===")
        parser = Parser(tokens, code)
        ast = parser.parse()
        import pprint
        pprint.pprint(ast)
        
        print("\n=== PHASE 3: SEMANTIC ANALYSIS ===")
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("Semantic analysis completed successfully.")
        print("Global scope symbols defined:", list(analyzer.global_scope.symbols.keys()))
        
        print("\n=== PHASE 4: CODE GENERATION & EXECUTION ===")
        generator = CodeGenerator()
        python_code = generator.generate(ast)
        
        executor = Executor()
        result = executor.run(python_code)
        
        if result["error"]:
            print("\nExecution Error:\n" + result["error"])
        else:
            print("\nExecution Output:\n" + result["output"])
            
    except PlainscriptError as e:
        print(str(e))
    except Exception as e:
        print(f"Internal Error: {str(e)}")

def start_server():
    from web.app import app
    print("=" * 50)
    print("PLAINSCRIPT IDE - READY")
    print("URL: http://localhost:5000")
    print("=" * 50)
    app.run(port=5000)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plainscript Compiler & IDE")
    parser.add_argument("--file", help="Path to a .ps file to execute")
    args = parser.parse_args()

    if args.file:
        run_file(args.file)
    else:
        start_server()
