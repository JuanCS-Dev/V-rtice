"""
VScript Parser - Lexer & AST Builder

Simple recursive descent parser for VScript DSL.

Grammar (simplified):
    program     → statement*
    statement   → assignment | if_stmt | for_loop | expr_stmt | comment
    assignment  → IDENTIFIER '=' expression
    if_stmt     → 'if' expression ':' block ('elif' expression ':' block)* ('else' ':' block)?
    for_loop    → 'for' IDENTIFIER 'in' expression ':' block
    expr_stmt   → expression
    expression  → logical_or
    logical_or  → logical_and ('or' logical_and)*
    logical_and → equality ('and' equality)*
    equality    → comparison (('==' | '!=') comparison)*
    comparison  → term (('>' | '<' | '>=' | '<=') term)*
    term        → factor (('+' | '-') factor)*
    factor      → unary (('*' | '/') unary)*
    unary       → ('not' | '-') unary | primary
    primary     → literal | variable | function_call | '(' expression ')'
"""

import re
from typing import List, Optional, Union, Any
from dataclasses import dataclass

from .models import *


# ========================================
# Token Types
# ========================================

@dataclass
class Token:
    """Lexical token."""

    type: str
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """
    Tokenize VScript source code.

    Example:
        lexer = Lexer("x = 5\\nprint(x)")
        tokens = lexer.tokenize()
    """

    # Token patterns (order matters!)
    PATTERNS = [
        ("COMMENT", r"#[^\n]*"),
        ("FSTRING", r'f"(?:[^"\\\\]|\\\\.)*"'),
        ("FSTRING_SINGLE", r"f'(?:[^'\\\\]|\\\\.)*'"),
        ("STRING", r'"(?:[^"\\\\]|\\\\.)*"'),
        ("STRING_SINGLE", r"'(?:[^'\\\\]|\\\\.)*'"),
        ("FLOAT", r"\d+\.\d+"),
        ("INTEGER", r"\d+"),
        ("KEYWORD", r"\b(if|elif|else|for|in|while|break|continue|return|and|or|not|True|False|None)\b"),
        ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("EQ", r"=="),
        ("NE", r"!="),
        ("LE", r"<="),
        ("GE", r">="),
        ("ASSIGN", r"="),
        ("LT", r"<"),
        ("GT", r">"),
        ("PLUS", r"\+"),
        ("MINUS", r"-"),
        ("STAR", r"\*"),
        ("SLASH", r"/"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACKET", r"\["),
        ("RBRACKET", r"\]"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("COMMA", r","),
        ("COLON", r":"),
        ("DOT", r"\."),
        ("NEWLINE", r"\n"),
        ("WHITESPACE", r"[ \t]+"),
    ]

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        """Tokenize source code."""
        position = 0

        while position < len(self.source):
            matched = False

            for token_type, pattern in self.PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.source, position)

                if match:
                    value = match.group(0)

                    # Skip whitespace (but track it for column counting)
                    if token_type == "WHITESPACE":
                        self.column += len(value)
                        position = match.end()
                        matched = True
                        break

                    # Handle newlines
                    if token_type == "NEWLINE":
                        self.tokens.append(Token(token_type, value, self.line, self.column))
                        self.line += 1
                        self.column = 1
                        position = match.end()
                        matched = True
                        break

                    # Add token
                    self.tokens.append(Token(token_type, value, self.line, self.column))
                    self.column += len(value)
                    position = match.end()
                    matched = True
                    break

            if not matched:
                raise SyntaxError(
                    f"Unexpected character '{self.source[position]}' "
                    f"at line {self.line}, column {self.column}"
                )

        # Add EOF
        self.tokens.append(Token("EOF", None, self.line, self.column))
        return self.tokens


class VScriptParser:
    """
    Parse VScript source into AST.

    Example:
        parser = VScriptParser(source_code)
        program = parser.parse()
    """

    def __init__(self, source: str):
        lexer = Lexer(source)
        self.tokens = lexer.tokenize()
        self.position = 0

    def current_token(self) -> Token:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # EOF

    def peek_token(self, offset: int = 1) -> Token:
        """Peek ahead."""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]

    def advance(self) -> Token:
        """Consume and return current token."""
        token = self.current_token()
        if token.type != "EOF":
            self.position += 1
        return token

    def expect(self, token_type: str) -> Token:
        """Expect specific token type."""
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type}, got {token.type} at line {token.line}"
            )
        return self.advance()

    def skip_newlines(self):
        """Skip any newlines."""
        while self.current_token().type == "NEWLINE":
            self.advance()

    def parse(self) -> Program:
        """Parse entire program."""
        statements = []

        while self.current_token().type != "EOF":
            self.skip_newlines()

            if self.current_token().type == "EOF":
                break

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

            self.skip_newlines()

        return Program(statements=statements)

    def parse_statement(self) -> Optional[Statement]:
        """Parse single statement."""
        token = self.current_token()

        # Comment
        if token.type == "COMMENT":
            comment_token = self.advance()
            return Comment(text=comment_token.value[1:].strip(), line=token.line)

        # Keywords
        if token.type == "KEYWORD":
            if token.value == "if":
                return self.parse_if_statement()
            elif token.value == "for":
                return self.parse_for_loop()
            elif token.value == "while":
                return self.parse_while_loop()
            elif token.value == "return":
                return self.parse_return()
            elif token.value == "break":
                self.advance()
                return Break(line=token.line)
            elif token.value == "continue":
                self.advance()
                return Continue(line=token.line)

        # Assignment or expression
        if token.type == "IDENTIFIER" and self.peek_token().type == "ASSIGN":
            return self.parse_assignment()
        else:
            expr = self.parse_expression()
            return ExpressionStatement(expression=expr, line=token.line)

    def parse_assignment(self) -> Assignment:
        """Parse assignment (x = value)."""
        token = self.current_token()
        name = self.expect("IDENTIFIER").value
        self.expect("ASSIGN")
        value = self.parse_expression()
        return Assignment(target=name, value=value, line=token.line)

    def parse_if_statement(self) -> IfStatement:
        """Parse if/elif/else."""
        token = self.current_token()
        self.expect("KEYWORD")  # 'if'
        condition = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()

        elif_branches = []
        else_body = None

        while self.current_token().type == "KEYWORD" and self.current_token().value == "elif":
            self.advance()
            elif_cond = self.parse_expression()
            self.expect("COLON")
            elif_body = self.parse_block()
            elif_branches.append((elif_cond, elif_body))

        if self.current_token().type == "KEYWORD" and self.current_token().value == "else":
            self.advance()
            self.expect("COLON")
            else_body = self.parse_block()

        return IfStatement(
            condition=condition,
            body=body,
            elif_branches=elif_branches,
            else_body=else_body,
            line=token.line
        )

    def parse_for_loop(self) -> ForLoop:
        """Parse for loop."""
        token = self.current_token()
        self.expect("KEYWORD")  # 'for'
        var_name = self.expect("IDENTIFIER").value
        self.expect("KEYWORD")  # 'in'
        iterable = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()

        return ForLoop(variable=var_name, iterable=iterable, body=body, line=token.line)

    def parse_while_loop(self) -> WhileLoop:
        """Parse while loop."""
        token = self.current_token()
        self.expect("KEYWORD")  # 'while'
        condition = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()

        return WhileLoop(condition=condition, body=body, line=token.line)

    def parse_return(self) -> Return:
        """Parse return statement."""
        token = self.current_token()
        self.advance()  # 'return'

        # Check if there's a value
        if self.current_token().type in ("NEWLINE", "EOF"):
            return Return(line=token.line)

        value = self.parse_expression()
        return Return(value=value, line=token.line)

    def parse_block(self) -> List[Statement]:
        """Parse indented block of statements."""
        statements = []
        self.skip_newlines()

        # Get the indentation level of the first statement in the block
        # (we expect it to be indented relative to the parent)
        if self.current_token().type == "EOF":
            return statements

        base_indent = self.current_token().column

        # Parse statements at this indentation level or deeper
        while self.current_token().type != "EOF":
            # Skip blank lines
            if self.current_token().type == "NEWLINE":
                self.advance()
                continue

            # Check if we've dedented (statement at lower indentation level)
            current_indent = self.current_token().column
            if current_indent < base_indent:
                # Dedent detected - end of block
                break

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

            if self.current_token().type == "NEWLINE":
                self.advance()
            else:
                break

        return statements

    def parse_expression(self) -> Expression:
        """Parse expression."""
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        """Parse logical OR."""
        left = self.parse_logical_and()

        while self.current_token().type == "KEYWORD" and self.current_token().value == "or":
            op_token = self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(left=left, operator="or", right=right, line=op_token.line)

        return left

    def parse_logical_and(self) -> Expression:
        """Parse logical AND."""
        left = self.parse_equality()

        while self.current_token().type == "KEYWORD" and self.current_token().value == "and":
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOp(left=left, operator="and", right=right, line=op_token.line)

        return left

    def parse_equality(self) -> Expression:
        """Parse equality (==, !=)."""
        left = self.parse_comparison()

        while self.current_token().type in ("EQ", "NE"):
            op_token = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line)

        return left

    def parse_comparison(self) -> Expression:
        """Parse comparison (<, >, <=, >=)."""
        left = self.parse_term()

        while self.current_token().type in ("LT", "GT", "LE", "GE"):
            op_token = self.advance()
            right = self.parse_term()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line)

        return left

    def parse_term(self) -> Expression:
        """Parse addition/subtraction."""
        left = self.parse_factor()

        while self.current_token().type in ("PLUS", "MINUS"):
            op_token = self.advance()
            right = self.parse_factor()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line)

        return left

    def parse_factor(self) -> Expression:
        """Parse multiplication/division."""
        left = self.parse_unary()

        while self.current_token().type in ("STAR", "SLASH"):
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line)

        return left

    def parse_unary(self) -> Expression:
        """Parse unary operations."""
        if self.current_token().type == "KEYWORD" and self.current_token().value == "not":
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(operator="not", operand=operand, line=op_token.line)

        if self.current_token().type == "MINUS":
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(operator="-", operand=operand, line=op_token.line)

        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        """Parse postfix expressions (function calls, attribute access)."""
        expr = self.parse_primary()

        while True:
            # Function call
            if self.current_token().type == "LPAREN":
                if isinstance(expr, Variable):
                    expr = self.parse_function_call(expr.name)
                elif isinstance(expr, AttributeAccess):
                    # Method call
                    expr = self.parse_method_call(expr)
                else:
                    raise SyntaxError(f"Cannot call {expr}")

            # Attribute access
            elif self.current_token().type == "DOT":
                self.advance()
                attr_name = self.expect("IDENTIFIER").value
                expr = AttributeAccess(object=expr, attribute=attr_name)

            # List/dict indexing
            elif self.current_token().type == "LBRACKET":
                self.advance()  # [
                index = self.parse_expression()
                self.expect("RBRACKET")
                expr = IndexAccess(object=expr, index=index)

            else:
                break

        return expr

    def parse_function_call(self, name: str) -> FunctionCall:
        """Parse function call."""
        self.expect("LPAREN")

        args = []
        kwargs = {}

        while self.current_token().type != "RPAREN":
            # Check for keyword argument
            if (self.current_token().type == "IDENTIFIER" and
                self.peek_token().type == "ASSIGN"):
                key = self.advance().value
                self.advance()  # =
                value = self.parse_expression()
                kwargs[key] = value
            else:
                args.append(self.parse_expression())

            if self.current_token().type == "COMMA":
                self.advance()
            elif self.current_token().type != "RPAREN":
                raise SyntaxError(f"Expected ',' or ')' in function call")

        self.expect("RPAREN")

        return FunctionCall(name=name, args=args, kwargs=kwargs)

    def parse_method_call(self, obj_access: AttributeAccess) -> MethodCall:
        """Parse method call."""
        self.expect("LPAREN")

        args = []
        kwargs = {}

        while self.current_token().type != "RPAREN":
            if (self.current_token().type == "IDENTIFIER" and
                self.peek_token().type == "ASSIGN"):
                key = self.advance().value
                self.advance()
                value = self.parse_expression()
                kwargs[key] = value
            else:
                args.append(self.parse_expression())

            if self.current_token().type == "COMMA":
                self.advance()

        self.expect("RPAREN")

        return MethodCall(
            object=obj_access.object,
            method=obj_access.attribute,
            args=args,
            kwargs=kwargs
        )

    def parse_primary(self) -> Expression:
        """Parse primary expressions."""
        token = self.current_token()

        # Literals
        if token.type == "INTEGER":
            self.advance()
            return Literal(value=int(token.value), type=VScriptType.INTEGER, line=token.line)

        if token.type == "FLOAT":
            self.advance()
            return Literal(value=float(token.value), type=VScriptType.FLOAT, line=token.line)

        if token.type in ("STRING", "STRING_SINGLE"):
            self.advance()
            # Remove quotes
            value = token.value[1:-1]
            # Handle escape sequences
            value = value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return Literal(value=value, type=VScriptType.STRING, line=token.line)

        if token.type in ("FSTRING", "FSTRING_SINGLE"):
            self.advance()
            return self.parse_fstring(token.value)

        if token.type == "KEYWORD":
            if token.value == "True":
                self.advance()
                return Literal(value=True, type=VScriptType.BOOLEAN, line=token.line)
            if token.value == "False":
                self.advance()
                return Literal(value=False, type=VScriptType.BOOLEAN, line=token.line)
            if token.value == "None":
                self.advance()
                return Literal(value=None, type=VScriptType.NULL, line=token.line)

        # Variable
        if token.type == "IDENTIFIER":
            self.advance()
            return Variable(name=token.value, line=token.line)

        # List literal
        if token.type == "LBRACKET":
            return self.parse_list_literal()

        # Dict literal
        if token.type == "LBRACE":
            return self.parse_dict_literal()

        # Parenthesized expression
        if token.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr

        raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")

    def parse_list_literal(self) -> ListLiteral:
        """Parse list literal [1, 2, 3]."""
        token = self.current_token()
        self.expect("LBRACKET")

        elements = []

        while self.current_token().type != "RBRACKET":
            elements.append(self.parse_expression())

            if self.current_token().type == "COMMA":
                self.advance()
            elif self.current_token().type != "RBRACKET":
                raise SyntaxError("Expected ',' or ']' in list literal")

        self.expect("RBRACKET")

        return ListLiteral(elements=elements, line=token.line)

    def parse_dict_literal(self) -> DictLiteral:
        """Parse dict literal {key: value}."""
        token = self.current_token()
        self.expect("LBRACE")

        pairs = []

        while self.current_token().type != "RBRACE":
            key = self.parse_expression()
            self.expect("COLON")
            value = self.parse_expression()
            pairs.append((key, value))

            if self.current_token().type == "COMMA":
                self.advance()
            elif self.current_token().type != "RBRACE":
                raise SyntaxError("Expected ',' or '}' in dict literal")

        self.expect("RBRACE")

        return DictLiteral(pairs=pairs, line=token.line)

    def parse_fstring(self, fstring_token: str) -> FString:
        """Parse f-string (simplified - just extracts {expressions})."""
        # Remove f" and "
        content = fstring_token[2:-1]

        # Simple extraction of {expression} parts
        # In production would use proper parser
        parts = []
        current = ""
        in_expr = False

        i = 0
        while i < len(content):
            if content[i] == "{" and i + 1 < len(content) and content[i + 1] != "{":
                if current:
                    parts.append(current)
                    current = ""
                in_expr = True
                i += 1
                expr_str = ""
                while i < len(content) and content[i] != "}":
                    expr_str += content[i]
                    i += 1
                # Parse expression
                expr_parser = VScriptParser(expr_str)
                parts.append(expr_parser.parse_expression())
                in_expr = False
            else:
                current += content[i]
            i += 1

        if current:
            parts.append(current)

        return FString(parts=parts)


# Export for compatibility
ASTNode = ASTNode
