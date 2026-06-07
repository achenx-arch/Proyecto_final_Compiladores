"""
Modulo: Calculo de Conjuntos FIRST y FOLLOW
Epsilon se representa con la cadena 'e'
Autor: ProyectoCompilador UMG
"""

EPS = 'e'  # simbolo epsilon

class FirstFollowCalculator:
    """
    Calcula FIRST y FOLLOW para una gramatica libre de contexto.
    La gramatica es un dict: { 'NT': [['sym1', ...], ...] }
    'e' representa epsilon.  '$' representa fin de entrada.
    """

    def __init__(self, grammar):
        self.grammar = grammar
        self.non_terminals = set(grammar.keys())
        self.start_symbol = list(grammar.keys())[0]
        self._first = {}
        self._follow = {}

    def compute_first(self):
        """Calcula FIRST para todos los no-terminales."""
        self._first = {nt: set() for nt in self.non_terminals}
        changed = True
        while changed:
            changed = False
            for nt, productions in self.grammar.items():
                for production in productions:
                    new_syms = self._first_of_string(production)
                    before = len(self._first[nt])
                    self._first[nt].update(new_syms)
                    if len(self._first[nt]) > before:
                        changed = True
        return dict(self._first)

    def _first_of_symbol(self, symbol):
        if symbol == EPS:
            return {EPS}
        if symbol not in self.non_terminals:
            return {symbol}
        return set(self._first.get(symbol, set()))

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

    def compute_follow(self):
        """Calcula FOLLOW para todos los no-terminales."""
        if not self._first:
            self.compute_first()
        self._follow = {nt: set() for nt in self.non_terminals}
        self._follow[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            for nt, productions in self.grammar.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        if symbol not in self.non_terminals:
                            continue
                        beta = production[i + 1:]
                        before = len(self._follow[symbol])
                        if beta:
                            first_beta = self._first_of_string(beta)
                            self._follow[symbol].update(first_beta - {EPS})
                            if EPS in first_beta:
                                self._follow[symbol].update(self._follow[nt])
                        else:
                            self._follow[symbol].update(self._follow[nt])
                        if len(self._follow[symbol]) > before:
                            changed = True
        return dict(self._follow)
