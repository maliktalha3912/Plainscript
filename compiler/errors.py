import sys

class PlainscriptError(Exception):
    """Base class for all Plainscript errors."""
    def __init__(self, message, line=None, col=None, source_line=None):
        self.message = message
        self.line = line
        self.col = col
        self.source_line = source_line
        super().__init__(self.message)

    def __str__(self):
        if self.line is not None and self.col is not None:
            prefix = f"{self.__class__.__name__} on line {self.line}, col {self.col}:"
            msg = f"{prefix}\n  {self.message}"
            if self.source_line:
                # Add caret indicator
                msg += f"\n    {self.source_line.strip()}\n    {' ' * (self.col - 1)}^"
            return msg
        return f"{self.__class__.__name__}: {self.message}"

class LexerError(PlainscriptError):
    """Errors during lexical analysis."""
    pass

class ParseError(PlainscriptError):
    """Errors during parsing."""
    pass

class SemanticError(PlainscriptError):
    """Errors during semantic analysis."""
    pass

class RuntimeError(PlainscriptError):
    """Errors during execution."""
    pass
