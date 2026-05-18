import sys
import io
import contextlib
import threading
import time

class Executor:
    """Safely executes generated Python code."""

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.allowed_builtins = {
            'print': print,
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'abs': abs,
            'max': max,
            'min': min,
            'sum': sum,
            'round': round,
            'Exception': Exception,
            'TypeError': TypeError,
            'ValueError': ValueError,
            'IndexError': IndexError,
            'KeyError': KeyError,
        }

    def run(self, code, inputs=None):
        """Run the code and capture output."""
        if inputs is None:
            inputs = []
            
        output_buffer = io.StringIO()
        error_msg = None
        
        # Prepare input queue
        input_queue = list(inputs)
        
        def custom_input(prompt=""):
            if input_queue:
                value = str(input_queue.pop(0))
                # Echo the input to output so user sees it
                print(value)
                return value
            return ""
            
        # Prepare globals with blocked builtins
        # We need to manually add print to ensure it's captured by redirect_stdout
        # since redirect_stdout only affects sys.stdout
        safe_globals = {
            '__builtins__': self.allowed_builtins.copy(),
            'input': custom_input,
            'print': print, # This will be captured by redirect_stdout
        }
        
        def target():
            nonlocal error_msg
            try:
                with contextlib.redirect_stdout(output_buffer):
                    exec(code, safe_globals)
            except Exception as e:
                error_msg = f"RuntimeError: {str(e)}"

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(self.timeout)
        
        if thread.is_alive():
            # This is tricky in Python to kill a thread, but we can report it
            error_msg = f"TimeoutError: Code execution exceeded {self.timeout} seconds."
            return {"output": output_buffer.getvalue(), "error": error_msg}

        return {
            "output": output_buffer.getvalue(),
            "error": error_msg
        }
