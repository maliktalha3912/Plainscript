import re
from .errors import LexerError

class Token:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}, {self.col})"

    def to_dict(self):
        return {
            'type': self.type,
            'value': self.value,
            'line': self.line,
            'col': self.col
        }

class Lexer:
    """Lexical analyzer for Plainscript."""
    
    # Token types and their regex patterns
    # Order matters: multi-word keywords first, then single-word keywords, then others.
    SPEC = [
        ('TK_COMMENT',       r'//.*|--.*|note:.*'),
        ('TK_STRING',        r'"[^"]*"'),
        ('TK_NUMBER_FLOAT',  r'\d+\.\d+'),
        ('TK_NUMBER_INT',    r'\d+'),
        
        # Multi-word Keywords
        ('TK_KW_OTHERWISE_IF',   r'otherwise\s+if'),
        ('TK_KW_DEFINE_ACTION',  r'define\s+action'),
        ('TK_KW_DEFINE_RECORD',  r'define\s+record'),
        ('TK_KW_IF_ERROR',       r'if\s+error\s+occurs'),
        ('TK_KW_IS_BETWEEN',     r'is\s+between'),
        ('TK_KW_IS_GREATER_THAN', r'is\s+greater\s+than'),
        ('TK_KW_IS_LESS_THAN',    r'is\s+less\s+than'),
        ('TK_KW_IS_AT_LEAST',     r'is\s+at\s+least'),
        ('TK_KW_IS_AT_MOST',      r'is\s+at\s+most'),
        ('TK_KW_IS_NOT',          r'is\s+not'),
        ('TK_KW_FOR_EACH',        r'for\s+each'),
        ('TK_KW_FOR_EVERY',       r'for\s+every'),
        ('TK_KW_JOINED_WITH',     r'joined\s+with'),
        ('TK_KW_DIVIDED_BY',      r'divided\s+by'),
        ('TK_KW_TO_THE_POWER_OF', r'to\s+the\s+power\s+of'),
        ('TK_KW_ASK_FOR',         r'ask\s+for'),
        ('TK_KW_A_NEW',           r'a\s+new'),
        ('TK_KW_FIRST_ITEM',      r'first\s+item'),
        ('TK_KW_LAST_ITEM',       r'last\s+item'),
        ('TK_KW_LENGTH_OF',       r'length\s+of'),
        
        # Single-word Keywords
        ('TK_KW_SET',        r'set'),
        ('TK_KW_LET',        r'let'),
        ('TK_KW_BE',         r'be'),
        ('TK_KW_DEFINE',     r'define'),
        ('TK_KW_AS',         r'as'),
        ('TK_KW_TO',         r'to'),
        ('TK_KW_IS',         r'is'),
        ('TK_KW_IF',         r'if'),
        ('TK_KW_THEN',       r'then'),
        ('TK_KW_OTHERWISE',  r'otherwise'),
        ('TK_KW_END',        r'end'),
        ('TK_KW_WHILE',      r'while'),
        ('TK_KW_REPEAT',     r'repeat'),
        ('TK_KW_TIMES',      r'times'),
        ('TK_KW_FROM',       r'from'),
        ('TK_KW_IN',         r'in'),
        ('TK_KW_WITH',       r'with'),
        ('TK_KW_AND',        r'and'),
        ('TK_KW_OR',         r'or'),
        ('TK_KW_NOT',        r'not'),
        ('TK_KW_RETURN',     r'return'),
        ('TK_KW_CALL',       r'call'),
        ('TK_KW_SHOW',       r'show'),
        ('TK_KW_ADD',        r'add'),
        ('TK_KW_REMOVE',     r'remove'),
        ('TK_KW_TRY',        r'try'),
        ('TK_KW_PLUS',       r'plus'),
        ('TK_KW_MINUS',      r'minus'),
        ('TK_KW_MOD',        r'mod'),
        ('TK_KW_OF',         r'of'),
        
        ('TK_BOOLEAN',       r'true|false|yes|no'),
        ('TK_NULL',          r'nothing|null|empty'),
        
        # Symbols
        ('TK_LPAREN',        r'\('),
        ('TK_RPAREN',        r'\)'),
        ('TK_LBRACKET',      r'\['),
        ('TK_RBRACKET',      r'\]'),
        ('TK_COMMA',         r','),
        ('TK_APOSTROPHE_S',  r"\'s"),
        
        ('TK_IDENTIFIER',    r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('TK_NEWLINE',       r'\n'),
        ('TK_WHITESPACE',    r'[ \t]+'),
        ('TK_MISMATCH',      r'.'),            # Any other character
    ]

    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.line = 1
        self.line_start = 0
        self.indent_stack = [0]
        
        # Noise words to discard
        self.noise_words = {'the'}
        
        # Compile master regex
        regex_parts = []
        for name, pattern in self.SPEC:
            # Use word boundaries for identifiers and keywords to avoid partial matches
            if name.startswith('TK_KW_') or name in ('TK_IDENTIFIER', 'TK_BOOLEAN', 'TK_NULL'):
                regex_parts.append(f'(?P<{name}>\\b{pattern}\\b)')
            else:
                regex_parts.append(f'(?P<{name}>{pattern})')
        self.master_regex = re.compile('|'.join(regex_parts), re.IGNORECASE)

    def tokenize(self):
        """Tokenize the source code and return a list of tokens."""
        for match in self.master_regex.finditer(self.source_code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - self.line_start + 1

            if kind == 'TK_WHITESPACE':
                continue
            elif kind == 'TK_NEWLINE':
                self.tokens.append(Token('TK_NEWLINE', '\n', self.line, column))
                self.line += 1
                self.line_start = match.end()
                self.handle_indentation(match.end())
            elif kind == 'TK_COMMENT':
                continue
            elif kind == 'TK_STRING':
                # Remove quotes
                self.tokens.append(Token('TK_STRING', value[1:-1], self.line, column))
            elif kind == 'TK_IDENTIFIER':
                val_lower = value.lower()
                if val_lower in self.noise_words:
                    continue
                self.tokens.append(Token('TK_IDENTIFIER', val_lower, self.line, column))
            elif kind == 'TK_BOOLEAN':
                val_lower = value.lower()
                bool_val = val_lower in ('true', 'yes')
                self.tokens.append(Token('TK_BOOLEAN', bool_val, self.line, column))
            elif kind == 'TK_NULL':
                self.tokens.append(Token('TK_NULL', None, self.line, column))
            elif kind == 'TK_MISMATCH':
                # Get the offending line for the error message
                end_of_line = self.source_code.find('\n', match.start())
                if end_of_line == -1: end_of_line = len(self.source_code)
                source_line = self.source_code[self.line_start:end_of_line]
                raise LexerError(f"Unexpected character: {value!r}", self.line, column, source_line)
            else:
                # Keywords and symbols
                self.tokens.append(Token(kind, value.lower(), self.line, column))

        # Add remaining DEDENT tokens at the end of the file
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token('TK_DEDENT', '', self.line, 1))
        
        self.tokens.append(Token('TK_EOF', '', self.line, 1))
        
        # Clean up tokens: remove consecutive NEWLINEs and ensure correct order
        self.clean_tokens()
        return self.tokens

    def handle_indentation(self, current_pos):
        """Analyze the indentation of the next line and emit INDENT/DEDENT tokens."""
        # Find the indentation of the next non-empty line
        next_line_start = current_pos
        indent_match = re.match(r'[ \t]*', self.source_code[next_line_start:])
        if indent_match:
            indent_str = indent_match.group()
            # If the rest of the line is a comment or empty, ignore it for indentation
            rest_of_line = self.source_code[next_line_start + len(indent_str):]
            if not rest_of_line or rest_of_line.startswith(('\n', '//', '--', 'note:')):
                return
            
            indent_level = len(indent_str.replace('\t', '    '))
            last_indent = self.indent_stack[-1]
            
            if indent_level > last_indent:
                self.indent_stack.append(indent_level)
                self.tokens.append(Token('TK_INDENT', '', self.line, 1))
            elif indent_level < last_indent:
                while indent_level < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    self.tokens.append(Token('TK_DEDENT', '', self.line, 1))
                if indent_level != self.indent_stack[-1]:
                    raise LexerError(f"Inconsistent indentation: {indent_level} spaces (expected {self.indent_stack[-1]})", self.line, 1)

    def clean_tokens(self):
        """Remove redundant tokens and fix specific sequences."""
        # Remove consecutive newlines
        new_tokens = []
        for i, token in enumerate(self.tokens):
            if token.type == 'TK_NEWLINE':
                if i > 0 and self.tokens[i-1].type in ('TK_NEWLINE', 'TK_INDENT', 'TK_DEDENT'):
                    continue
            new_tokens.append(token)
        
        # If the first token is a NEWLINE, remove it
        if new_tokens and new_tokens[0].type == 'TK_NEWLINE':
            new_tokens.pop(0)
            
        self.tokens = new_tokens
