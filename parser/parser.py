"""
Modulo: Analizador Sintactico LL(1) para Python (subconjunto)
Gramatica factorizada por izquierda para evitar conflictos LL(1).
Autor: ProyectoCompilador UMG

GRAMATICA:
  PROGRAMA              -> LISTA_SENTENCIAS
  LISTA_SENTENCIAS      -> SENTENCIA LISTA_SENTENCIAS_REST
  LISTA_SENTENCIAS_REST -> SENTENCIA LISTA_SENTENCIAS_REST | e
  SENTENCIA             -> ID SENTENCIA_ID | IF_KW EXPRESION DOS_PUNTOS
                         | WHILE_KW EXPRESION DOS_PUNTOS
                         | FOR_KW ID IN_KW EXPRESION DOS_PUNTOS
                         | DEF_KW ID PAREN_ABRE PARAMS PAREN_CIERRA DOS_PUNTOS
                         | RETURN_KW EXPRESION
  SENTENCIA_ID          -> IGUAL EXPRESION | PAREN_ABRE ARGS PAREN_CIERRA
  ARGS                  -> EXPRESION ARGS_REST | e
  ARGS_REST             -> COMA EXPRESION ARGS_REST | e
  PARAMS                -> ID PARAMS_REST | e
  PARAMS_REST           -> COMA ID PARAMS_REST | e
  EXPRESION             -> TERMINO EXPRESION_REST
  EXPRESION_REST        -> OPERADOR TERMINO | e
  TERMINO               -> ID | ENTERO | DECIMAL | CADENA | PAREN_ABRE EXPRESION PAREN_CIERRA
"""

from utils.first_follow import FirstFollowCalculator
from utils.ll1 import LL1TableBuilder

GRAMMAR = {
    'PROGRAMA':              [['LISTA_SENTENCIAS']],
    'LISTA_SENTENCIAS':      [['SENTENCIA', 'LISTA_SENTENCIAS_REST']],
    'LISTA_SENTENCIAS_REST': [['SENTENCIA', 'LISTA_SENTENCIAS_REST'], ['e']],
    'SENTENCIA': [
        ['ID',       'SENTENCIA_ID'],
        ['IF_KW',    'EXPRESION', 'DOS_PUNTOS'],
        ['WHILE_KW', 'EXPRESION', 'DOS_PUNTOS'],
        ['FOR_KW',   'ID', 'IN_KW', 'EXPRESION', 'DOS_PUNTOS'],
        ['DEF_KW',   'ID', 'PAREN_ABRE', 'PARAMS', 'PAREN_CIERRA', 'DOS_PUNTOS'],
        ['RETURN_KW','EXPRESION'],
    ],
    'SENTENCIA_ID': [
        ['IGUAL',      'EXPRESION'],
        ['PAREN_ABRE', 'ARGS', 'PAREN_CIERRA'],
    ],
    'ARGS':      [['EXPRESION', 'ARGS_REST'], ['e']],
    'ARGS_REST': [['COMA', 'EXPRESION', 'ARGS_REST'], ['e']],
    'PARAMS':      [['ID', 'PARAMS_REST'], ['e']],
    'PARAMS_REST': [['COMA', 'ID', 'PARAMS_REST'], ['e']],
    'EXPRESION':      [['TERMINO', 'EXPRESION_REST']],
    'EXPRESION_REST': [['OPERADOR', 'TERMINO'], ['e']],
    'TERMINO': [
        ['ID'], ['ENTERO'], ['DECIMAL'], ['CADENA'],
        ['PAREN_ABRE', 'EXPRESION', 'PAREN_CIERRA'],
    ],
}

TERMINAL_MAP = {
    'IF': 'IF_KW', 'WHILE': 'WHILE_KW', 'FOR': 'FOR_KW',
    'DEF': 'DEF_KW', 'RETURN': 'RETURN_KW', 'IN': 'IN_KW',
    'IDENTIFICADOR': 'ID',
    'ENTERO': 'ENTERO', 'DECIMAL': 'DECIMAL', 'CADENA': 'CADENA',
    'ASIGNACION': 'IGUAL',
    'DOS_PUNTOS': 'DOS_PUNTOS', 'COMA': 'COMA',
    'PAREN_ABRE': 'PAREN_ABRE', 'PAREN_CIERRA': 'PAREN_CIERRA',
    'PRINT': 'ID', 'CLASS': 'ID', 'IMPORT': 'ID', 'FROM': 'ID',
    'TRUE': 'ID', 'FALSE': 'ID', 'NONE': 'ID',
    'SUMA': 'OPERADOR', 'RESTA': 'OPERADOR', 'MULTIPLICACION': 'OPERADOR',
    'DIVISION': 'OPERADOR', 'MODULO': 'OPERADOR',
    'IGUAL_IGUAL': 'OPERADOR', 'DIFERENTE': 'OPERADOR',
    'MENOR_QUE': 'OPERADOR', 'MAYOR_QUE': 'OPERADOR',
    'MENOR_IGUAL': 'OPERADOR', 'MAYOR_IGUAL': 'OPERADOR',
}

NON_TERMINALS = set(GRAMMAR.keys())


class TreeNode:
    _counter = 0

    def __init__(self, label, is_terminal=False, value=None):
        TreeNode._counter += 1
        self.id = 'n' + str(TreeNode._counter)
        self.label = label
        self.is_terminal = is_terminal
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        return child

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'is_terminal': self.is_terminal,
            'value': self.value,
            'children': [c.to_dict() for c in self.children],
        }


class LL1Parser:
    """Parser predictivo LL(1) con tabla construida automaticamente."""

    def __init__(self):
        TreeNode._counter = 0
        self.ff_calc = FirstFollowCalculator(GRAMMAR)
        self.first = self.ff_calc.compute_first()
        self.follow = self.ff_calc.compute_follow()
        self.ll1_builder = LL1TableBuilder(GRAMMAR, self.first, self.follow)
        self.ll1_table = self.ll1_builder.build_table()
        self.errors = []
        self.derivations = []

    def parse(self, tokens):
        """Ejecuta el analisis sintactico LL(1)."""
        TreeNode._counter = 0
        self.errors = []
        self.derivations = []

        terminal_stream = self._tokens_to_terminals(tokens)
        terminal_stream.append({'terminal': '$', 'lexema': '$', 'linea': 0})

        root = TreeNode('PROGRAMA', is_terminal=False)
        stack = [('$', None), ('PROGRAMA', root)]
        idx = 0
        success = True

        while stack:
            top_symbol, top_node = stack[-1]
            cur = terminal_stream[idx] if idx < len(terminal_stream) else {'terminal': '$', 'lexema': '$', 'linea': 0}
            cur_t = cur['terminal']

            if top_symbol == '$' and cur_t == '$':
                self.derivations.append({'pila': '$', 'entrada': '$', 'produccion': 'ACEPTAR'})
                break

            if top_symbol == '$':
                self._add_error('Tokens inesperados despues del final', cur)
                break

            if top_symbol not in NON_TERMINALS:
                if top_symbol == cur_t:
                    if top_node:
                        top_node.is_terminal = True
                        top_node.value = cur['lexema']
                    stack.pop()
                    self.derivations.append({
                        'pila': self._stack_str(stack),
                        'entrada': self._input_str(terminal_stream, idx + 1),
                        'produccion': 'Emparejar: ' + top_symbol + ' = "' + str(cur['lexema']) + '"',
                    })
                    idx += 1
                else:
                    self._add_error('Se esperaba "' + top_symbol + '" pero se encontro "' + cur_t + '"', cur)
                    stack.pop()
                    success = False
            else:
                production = self.ll1_table.get((top_symbol, cur_t))

                if production is None:
                    follow_set = self.follow.get(top_symbol, set())
                    if cur_t in follow_set:
                        stack.pop()
                        self.derivations.append({
                            'pila': self._stack_str(stack),
                            'entrada': self._input_str(terminal_stream, idx),
                            'produccion': top_symbol + ' -> e (por FOLLOW)',
                        })
                        continue
                    self._add_error('No hay produccion para (' + top_symbol + ', ' + cur_t + ')', cur)
                    stack.pop()
                    success = False
                    continue

                stack.pop()
                body = production
                child_nodes = []
                if body != ['e']:
                    for sym in body:
                        child = top_node.add_child(TreeNode(sym)) if top_node else TreeNode(sym)
                        child_nodes.append((sym, child))
                    for sym, node in reversed(child_nodes):
                        stack.append((sym, node))

                self.derivations.append({
                    'pila': self._stack_str(stack),
                    'entrada': self._input_str(terminal_stream, idx),
                    'produccion': top_symbol + ' -> ' + ' '.join(body),
                })

        first_ser = {k: sorted(list(v)) for k, v in self.first.items()}
        follow_ser = {k: sorted(list(v)) for k, v in self.follow.items()}
        ll1_ser = {}
        for (nt, t), prod in self.ll1_table.items():
            if nt not in ll1_ser:
                ll1_ser[nt] = {}
            ll1_ser[nt][t] = ' '.join(prod)

        return {
            'success': success and len(self.errors) == 0,
            'tree': root.to_dict(),
            'derivations': self.derivations[:200],
            'errors': self.errors,
            'first': first_ser,
            'follow': follow_ser,
            'll1_table': ll1_ser,
            'grammar': {nt: [' '.join(p) for p in prods] for nt, prods in GRAMMAR.items()},
        }

    def _tokens_to_terminals(self, tokens):
        result = []
        for t in tokens:
            tok_type = t.get('token', '')
            terminal = TERMINAL_MAP.get(tok_type, tok_type)
            result.append({'terminal': terminal, 'lexema': t.get('lexema', ''), 'linea': t.get('linea', 0)})
        return result

    def _add_error(self, message, token):
        self.errors.append({
            'tipo': 'Error Sintactico',
            'descripcion': message,
            'linea': token.get('linea', 0),
            'lexema': token.get('lexema', ''),
        })

    def _stack_str(self, stack):
        return ' '.join(s for s, _ in reversed(stack) if s) or '$'

    def _input_str(self, stream, idx):
        remaining = [t['terminal'] for t in stream[idx:idx+5]]
        suffix = '...' if idx + 5 < len(stream) else ''
        return ' '.join(remaining) + suffix
