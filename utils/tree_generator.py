"""
Modulo: Generador de Arbol Sintactico con Graphviz
Autor: ProyectoCompilador UMG
"""
import os, base64

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

KEYWORDS = {'IF', 'WHILE', 'FOR', 'DEF', 'RETURN', 'CLASS',
            'IF_KW', 'WHILE_KW', 'FOR_KW', 'DEF_KW', 'RETURN_KW', 'IN_KW'}

COLORS = {
    'root':       ('#1e3a5f', 'white'),
    'non_term':   ('#2d6a4f', 'white'),
    'keyword':    ('#e63946', 'white'),
    'identifier': ('#457b9d', 'white'),
    'literal':    ('#f4a261', '#1d1d1d'),
    'operator':   ('#6a0572', 'white'),
    'default':    ('#343a40', 'white'),
}


class TreeGenerator:
    def __init__(self, output_dir='static/img'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, tree_dict, filename='syntax_tree'):
        dot_source = self._generate_dot(tree_dict)
        result = {'dot_source': dot_source, 'png_base64': None, 'png_path': None}
        if GRAPHVIZ_AVAILABLE:
            try:
                dot = graphviz.Source(dot_source)
                output_path = os.path.join(self.output_dir, filename)
                rendered = dot.render(filename=output_path, format='png', cleanup=True)
                if os.path.exists(rendered):
                    with open(rendered, 'rb') as f:
                        result['png_base64'] = base64.b64encode(f.read()).decode('utf-8')
                    result['png_path'] = rendered
            except Exception as e:
                result['error'] = str(e)
        return result

    def _safe_label(self, s):
        """Escape string for DOT label."""
        return str(s).replace('\\', '\\\\').replace('"', "'").replace('\n', '\\n')

    def _generate_dot(self, tree_dict):
        lines = [
            'digraph SyntaxTree {',
            '    graph [bgcolor="#1a1a2e" rankdir=TB splines=curved]',
            '    node  [fontname="Helvetica" fontsize=10 style=filled]',
            '    edge  [color="#aaaaaa" arrowsize=0.7]',
        ]
        self._node_to_dot(tree_dict, lines, is_root=True)
        lines.append('}')
        return '\n'.join(lines)

    def _node_to_dot(self, node, lines, is_root=False):
        nid   = node['id']
        label = node['label']
        value = node.get('value')
        is_terminal = node.get('is_terminal', False)

        if is_root:
            fill, font = COLORS['root']
        elif label in KEYWORDS:
            fill, font = COLORS['keyword']
        elif is_terminal:
            if label == 'ID':
                fill, font = COLORS['identifier']
            elif label in ('ENTERO', 'DECIMAL', 'CADENA'):
                fill, font = COLORS['literal']
            elif label == 'OPERADOR':
                fill, font = COLORS['operator']
            else:
                fill, font = COLORS['default']
        else:
            fill, font = COLORS['non_term']

        if is_terminal and value:
            display = self._safe_label(label) + '\\n' + self._safe_label(value)
            shape = 'box'
        else:
            display = self._safe_label(label)
            shape = 'doubleoctagon' if is_root else 'ellipse'

        lines.append(
            '    ' + nid + ' [label="' + display + '" shape=' + shape +
            ' fillcolor="' + fill + '" fontcolor="' + font + '"]'
        )
        for child in node.get('children', []):
            lines.append('    ' + nid + ' -> ' + child['id'])
            self._node_to_dot(child, lines)
