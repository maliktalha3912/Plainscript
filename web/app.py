from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import dataclasses
import sys
import os

# Add parent directory to sys.path to import compiler/runtime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.optimizer import ASTOptimizer
from compiler.ir_generator import IRGenerator
from compiler.codegen import CodeGenerator
from runtime.executor import Executor
from compiler.errors import PlainscriptError

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/tokenize', methods=['POST'])
def tokenize():
    code = request.json.get('code', '')
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        return jsonify({
            "tokens": [t.to_dict() for t in tokens if t.type != 'TK_EOF']
        })
    except PlainscriptError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"}), 500

@app.route('/parse', methods=['POST'])
def parse():
    code = request.json.get('code', '')
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, code)
        ast = parser.parse()
        return jsonify({"ast": dataclasses.asdict(ast)})
    except PlainscriptError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"}), 500

@app.route('/run', methods=['POST'])
def run():
    code = request.json.get('code', '')
    inputs = request.json.get('inputs', [])
    try:
        # Phase 1: Lexical Analysis
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        tokens_out = "\n".join([str(t) for t in tokens])
        
        # Phase 2: Syntax Analysis
        parser = Parser(tokens, code)
        ast = parser.parse()
        
        import pprint
        import io
        ast_stream = io.StringIO()
        pprint.pprint(ast, stream=ast_stream)
        ast_out = ast_stream.getvalue()
        
        # Phase 3: Semantic Analysis
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        semantic_out = "Semantic analysis completed successfully.\nGlobal scope symbols defined: " + str(list(analyzer.global_scope.symbols.keys()))

        # Phase 4: Optimization (AST-Level)
        optimizer = ASTOptimizer()
        ast = optimizer.optimize(ast)
        optimization_report = optimizer.report.to_list()
        optimization_summary = optimizer.report.summary()

        # Phase 5: Intermediate Code Generation (TAC)
        ir_gen = IRGenerator()
        ir_gen.generate(ast)
        tac_code = ir_gen.get_code()

        # Phase 6: Code Generation & Execution
        generator = CodeGenerator()
        python_code = generator.generate(ast)

        phases_output = (
            f"=== PHASE 1: LEXICAL ANALYSIS (Lexer) ===\n{tokens_out}\n\n"
            f"=== PHASE 2: SYNTAX ANALYSIS (Recursive Descent Parser) ===\n{ast_out}\n\n"
            f"=== PHASE 3: SEMANTIC ANALYSIS ===\n{semantic_out}\n\n"
            f"=== PHASE 4: OPTIMIZATION (AST-Level) ===\n{optimization_summary}\n\n"
            f"=== PHASE 5: INTERMEDIATE CODE GENERATION (TAC) ===\n{tac_code}\n\n"
            f"=== PHASE 6: CODE GENERATION ===\n{python_code}"
        )
        
        phases_dict = {
            "p1": tokens_out,
            "p2": ast_out,
            "p3": semantic_out,
            "p4": optimization_summary,
            "p5": tac_code,
            "p6": python_code
        }

        executor = Executor()
        result = executor.run(python_code, inputs=inputs)
        
        return jsonify({
            "output": result["output"],
            "phases_output": phases_output,
            "phases_dict": phases_dict,
            "error": result["error"],
            "generated_python": python_code,
            "tokens": [t.to_dict() for t in tokens if t.type != 'TK_EOF'],
            "optimization_report": optimization_report,
            "optimization_summary": optimization_summary,
            "tac_code": tac_code,
        })
        
    except PlainscriptError as e:
        return jsonify({
            "output": "",
            "error": str(e),
            "generated_python": ""
        }), 400
    except Exception as e:
        return jsonify({
            "output": "",
            "error": f"Internal Error: {str(e)}",
            "generated_python": ""
        }), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
