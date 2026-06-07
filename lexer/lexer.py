"""
Módulo: Analizador Léxico para Python
Descripción: Implementa el análisis léxico completo de código Python simplificado.
             Reconoce tokens, genera tabla de símbolos y detecta errores léxicos.
Autor: ProyectoCompilador UMG
"""

import re
import time


# ─────────────────────────────────────────────────────────────────────────────
# Definición de categorías de tokens
# ─────────────────────────────────────────────────────────────────────────────
class TokenType:
    KEYWORD     = 'PALABRA_RESERVADA'
    IDENTIFIER  = 'IDENTIFICADOR'
    INTEGER     = 'ENTERO'
    DECIMAL     = 'DECIMAL'
    STRING      = 'CADENA'
    OPERATOR    = 'OPERADOR'
    DELIMITER   = 'DELIMITADOR'
    NEWLINE     = 'NUEVA_LINEA'
    INDENT      = 'INDENTACION'
    EOF         = 'FIN_ARCHIVO'
    ERROR       = 'ERROR'


# ─────────────────────────────────────────────────────────────────────────────
# Palabras reservadas del subconjunto de Python
# ─────────────────────────────────────────────────────────────────────────────
KEYWORDS = {
    'if', 'else', 'for', 'while', 'def', 'return',
    'class', 'import', 'from', 'print', 'True', 'False',
    'None', 'and', 'or', 'not', 'in', 'is', 'elif',
    'break', 'continue', 'pass', 'try', 'except', 'finally',
    'with', 'as', 'lambda', 'yield', 'del', 'raise', 'global',
    'nonlocal', 'assert'
}

# ─────────────────────────────────────────────────────────────────────────────
# Patrones léxicos (orden importa: más específico primero)
# ─────────────────────────────────────────────────────────────────────────────
TOKEN_PATTERNS = [
    # Cadenas de texto (comillas dobles o simples)
    ('STRING_D',   r'"[^"\n]*"'),
    ('STRING_S',   r"'[^'\n]*'"),
    # Comentarios (ignorados)
    ('COMMENT',    r'#[^\n]*'),
    # Números: decimal antes que entero
    ('DECIMAL',    r'\d+\.\d+'),
    ('INTEGER',    r'\d+'),
    # Operadores de dos caracteres antes que uno
    ('OP2',        r'==|!=|<=|>=|<<|>>|\*\*|//|->'),
    # Operadores de un carácter
    ('OP1',        r'[+\-*/=%<>!&|^~]'),
    # Delimitadores
    ('DELIMITER',  r'[(){}\[\]:,.]'),
    # Identificadores y palabras reservadas
    ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    # Espacios en blanco (ignorados excepto nuevas líneas)
    ('NEWLINE',    r'\n'),
    ('WHITESPACE', r'[ \t\r]+'),
    # Cualquier otro carácter → error
    ('UNKNOWN',    r'.'),
]

# Compilar patrón maestro
MASTER_PATTERN = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS)
)


# ─────────────────────────────────────────────────────────────────────────────
# Clase Token
# ─────────────────────────────────────────────────────────────────────────────
class Token:
    """Representa un token individual con su información completa."""

    def __init__(self, number, line, column, lexeme, token_type, category):
        self.number    = number      # Número secuencial del token
        self.line      = line        # Línea en el código fuente
        self.column    = column      # Columna en la línea
        self.lexeme    = lexeme      # Valor literal
        self.token_type = token_type # Tipo de token (e.g. 'IDENTIFICADOR')
        self.category  = category   # Categoría (e.g. 'OPERADOR')

    def to_dict(self):
        """Serializa el token a diccionario para JSON."""
        return {
            'numero':    self.number,
            'linea':     self.line,
            'columna':   self.column,
            'lexema':    self.lexeme,
            'token':     self.token_type,
            'categoria': self.category,
        }

    def __repr__(self):
        return f'Token({self.token_type}, {self.lexeme!r}, L{self.line}:C{self.column})'


# ─────────────────────────────────────────────────────────────────────────────
# Clase Error Léxico
# ─────────────────────────────────────────────────────────────────────────────
class LexicalError:
    """Almacena información sobre un error léxico detectado."""

    def __init__(self, error_type, line, column, description, symbol):
        self.error_type  = error_type
        self.line        = line
        self.column      = column
        self.description = description
        self.symbol      = symbol

    def to_dict(self):
        return {
            'tipo':        self.error_type,
            'linea':       self.line,
            'columna':     self.column,
            'descripcion': self.description,
            'simbolo':     self.symbol,
        }

    def __str__(self):
        return (f"Error Léxico: {self.description}. "
                f"Símbolo '{self.symbol}' Línea {self.line}, Columna {self.column}.")


# ─────────────────────────────────────────────────────────────────────────────
# Clase Símbolo (para tabla de símbolos)
# ─────────────────────────────────────────────────────────────────────────────
class Symbol:
    """Entrada en la tabla de símbolos."""

    def __init__(self, name, symbol_type, line, value=None):
        self.name        = name
        self.symbol_type = symbol_type  # 'variable', 'funcion', 'clase', etc.
        self.line        = line
        self.value       = value
        self.references  = [line]       # Líneas donde aparece

    def add_reference(self, line):
        if line not in self.references:
            self.references.append(line)

    def to_dict(self):
        return {
            'nombre':       self.name,
            'tipo':         self.symbol_type,
            'linea':        self.line,
            'valor':        self.value if self.value else '-',
            'referencias':  ', '.join(str(r) for r in sorted(self.references)),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal: Analizador Léxico
# ─────────────────────────────────────────────────────────────────────────────
class PythonLexer:
    """
    Analizador léxico para un subconjunto de Python.

    Uso:
        lexer = PythonLexer()
        result = lexer.tokenize(code_string)
    """

    def __init__(self):
        self.tokens         = []
        self.symbol_table   = {}   # nombre → Symbol
        self.errors         = []
        self.lines          = 0
        self._token_counter = 0
        self._last_keyword  = None  # Para inferir tipo en tabla de símbolos

    # ──────────────────────────────────────────
    # Método público principal
    # ──────────────────────────────────────────
    def tokenize(self, code: str) -> dict:
        """
        Tokeniza el código fuente dado.

        Args:
            code: String con código Python a analizar.

        Returns:
            Diccionario con tokens, tabla de símbolos, errores y estadísticas.
        """
        # Reiniciar estado
        self.tokens       = []
        self.symbol_table = {}
        self.errors       = []
        self._token_counter = 0
        self._last_keyword  = None

        start_time = time.time()
        self.lines = code.count('\n') + 1

        line_num   = 1
        line_start = 0

        for match in MASTER_PATTERN.finditer(code):
            kind  = match.lastgroup
            value = match.group()
            col   = match.start() - line_start + 1

            # ── Ignorar espacios y comentarios ──
            if kind in ('WHITESPACE', 'COMMENT'):
                continue

            # ── Nueva línea ──
            elif kind == 'NEWLINE':
                line_num  += 1
                line_start = match.end()
                continue

            # ── Carácter desconocido → error ──
            elif kind == 'UNKNOWN':
                self.errors.append(LexicalError(
                    error_type  = 'Símbolo no reconocido',
                    line        = line_num,
                    column      = col,
                    description = f"Símbolo '{value}' no reconocido",
                    symbol      = value,
                ))
                continue

            # ── Procesar token válido ──
            token = self._classify_token(kind, value, line_num, col)
            if token:
                self._token_counter += 1
                token.number = self._token_counter
                self.tokens.append(token)
                # Actualizar tabla de símbolos si aplica
                self._update_symbol_table(token)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            'tokens':        [t.to_dict() for t in self.tokens],
            'symbol_table':  [s.to_dict() for s in self.symbol_table.values()],
            'errors':        [e.to_dict() for e in self.errors],
            'stats': {
                'lineas':        self.lines,
                'total_tokens':  self._token_counter,
                'identificadores': sum(
                    1 for t in self.tokens if t.category == TokenType.IDENTIFIER
                ),
                'errores':       len(self.errors),
                'tiempo_ms':     elapsed_ms,
            }
        }

    # ──────────────────────────────────────────
    # Clasificar token según su kind
    # ──────────────────────────────────────────
    def _classify_token(self, kind: str, value: str, line: int, col: int) -> Token:
        """Crea y retorna un objeto Token según el kind detectado."""

        if kind == 'IDENTIFIER':
            if value in KEYWORDS:
                self._last_keyword = value
                return Token(0, line, col, value, value.upper(), TokenType.KEYWORD)
            else:
                return Token(0, line, col, value, 'IDENTIFICADOR', TokenType.IDENTIFIER)

        elif kind == 'DECIMAL':
            return Token(0, line, col, value, 'DECIMAL', TokenType.DECIMAL)

        elif kind == 'INTEGER':
            return Token(0, line, col, value, 'ENTERO', TokenType.INTEGER)

        elif kind in ('STRING_D', 'STRING_S'):
            return Token(0, line, col, value, 'CADENA', TokenType.STRING)

        elif kind == 'OP2':
            names = {
                '==': 'IGUAL_IGUAL', '!=': 'DIFERENTE',
                '<=': 'MENOR_IGUAL', '>=': 'MAYOR_IGUAL',
                '<<': 'SHIFT_IZQ',   '>>': 'SHIFT_DER',
                '**': 'POTENCIA',    '//': 'DIV_ENTERA',
                '->': 'FLECHA',
            }
            return Token(0, line, col, value, names.get(value, 'OPERADOR'), TokenType.OPERATOR)

        elif kind == 'OP1':
            names = {
                '+': 'SUMA', '-': 'RESTA', '*': 'MULTIPLICACION',
                '/': 'DIVISION', '=': 'ASIGNACION', '%': 'MODULO',
                '<': 'MENOR_QUE', '>': 'MAYOR_QUE', '!': 'NOT',
                '&': 'AND_BIT', '|': 'OR_BIT', '^': 'XOR', '~': 'COMPLEMENT',
            }
            return Token(0, line, col, value, names.get(value, 'OPERADOR'), TokenType.OPERATOR)

        elif kind == 'DELIMITER':
            names = {
                '(': 'PAREN_ABRE', ')': 'PAREN_CIERRA',
                '{': 'LLAVE_ABRE', '}': 'LLAVE_CIERRA',
                '[': 'CORCHETE_ABRE', ']': 'CORCHETE_CIERRA',
                ':': 'DOS_PUNTOS', ',': 'COMA', '.': 'PUNTO',
            }
            return Token(0, line, col, value, names.get(value, 'DELIMITADOR'), TokenType.DELIMITER)

        return None

    # ──────────────────────────────────────────
    # Actualizar tabla de símbolos
    # ──────────────────────────────────────────
    def _update_symbol_table(self, token: Token):
        """Agrega o actualiza entradas en la tabla de símbolos."""

        if token.category != TokenType.IDENTIFIER:
            return

        name = token.lexeme

        # Inferir tipo según la palabra clave previa
        sym_type = 'variable'
        if self._last_keyword == 'def':
            sym_type = 'funcion'
        elif self._last_keyword == 'class':
            sym_type = 'clase'
        elif self._last_keyword == 'import':
            sym_type = 'modulo'
        elif self._last_keyword in ('for', 'with'):
            sym_type = 'variable_control'

        if name in self.symbol_table:
            self.symbol_table[name].add_reference(token.line)
        else:
            self.symbol_table[name] = Symbol(
                name        = name,
                symbol_type = sym_type,
                line        = token.line,
            )

        # Reiniciar contexto de keyword solo si fue consumida
        if self._last_keyword in ('def', 'class', 'import'):
            self._last_keyword = None
