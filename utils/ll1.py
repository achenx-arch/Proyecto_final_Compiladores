"""
Modulo: Constructor de Tabla Predictiva LL(1)
Autor: ProyectoCompilador UMG
"""

EPS = 'e'

class LL1TableBuilder:
    """
    Construye la tabla LL(1): M[A,a] = produccion
    Para cada A -> alpha:
      1. Para cada a en FIRST(alpha)-{e}: M[A,a] = alpha
      2. Si e en FIRST(alpha): para cada b en FOLLOW(A): M[A,b] = alpha
    """

    def __init__(self, grammar, first, follow):
        self.grammar = grammar
        self.first = first
        self.follow = follow
        self.non_terminals = set(grammar.keys())
        self._table = {}
        self._conflicts = []

    def build_table(self):
        self._table = {}
        self._conflicts = []
        for nt, productions in self.grammar.items():
            for production in productions:
                first_prod = self._first_of_string(production)
                for terminal in first_prod - {EPS}:
                    key = (nt, terminal)
                    if key in self._table:
                        self._conflicts.append({'nt': nt, 't': terminal})
                    else:
                        self._table[key] = production
                if EPS in first_prod:
                    for terminal in self.follow.get(nt, set()):
                        key = (nt, terminal)
                        if key in self._table:
                            self._conflicts.append({'nt': nt, 't': terminal})
                        else:
                            self._table[key] = production
        return self._table

    def get_conflicts(self):
        return self._conflicts

    def _first_of_symbol(self, symbol):
        if symbol == EPS:
            return {EPS}
        if symbol not in self.non_terminals:
            return {symbol}
        return set(self.first.get(symbol, set()))

    def _first_of_string(self, symbols):
        result = set()
        all_nullable = True
        for sym in symbols:
            sym_first = self._first_of_symbol(sym)
            result.update(sym_first - {EPS})
            if EPS not in sym_first:
                all_nullable = False
                break
        if all_nullable:
            result.add(EPS)
        return result

    def to_display_format(self):
        all_terminals = sorted(set(t for _, t in self._table.keys()))
        all_nts = sorted(self.grammar.keys())
        table_display = {}
        for nt in all_nts:
            table_display[nt] = {}
            for t in all_terminals:
                prod = self._table.get((nt, t))
                table_display[nt][t] = ' '.join(prod) if prod else ''
        return {'non_terminals': all_nts, 'terminals': all_terminals,
                'table': table_display, 'conflicts': self._conflicts}
