import docutils.parsers.rst
import docutils.nodes
import docutils.utils
import sphinx.addnodes
import sphinx.util.docutils
import sphinx.writers.html
import sphinx.util.logging
import sphinx.environment

import yaml
import yaml.error

from sphinx_a4doc.contrib.configurator import ManagedDirective
from sphinx_a4doc.contrib.railroad_diagrams import Diagram, HrefResolver

from sphinx_a4doc.model.model import ModelCache
from sphinx_a4doc.model.model_renderer import Renderer
from sphinx_a4doc.settings import diagram_namespace, DiagramSettings

from typing import *


logger = sphinx.util.logging.getLogger(__name__)


class DomainResolver(HrefResolver):
    def __init__(self, builder, grammar: str):
        self.builder = builder
        self.grammar = grammar

    def resolve(self, text: str, href: Optional[str], title_is_weak: bool):
        # There can be three alternative situations when resolving rules:
        # - href is not passed. In this case we resolve rule as if a role
        #   without an explicit title was invoked, i.e. we treat text as both
        #   title and target. If rule resolution succeeds, we replace title with
        #   a human-readable name assigned to the rule we've just resolved;
        # - href is passed explicitly. In this case we simulate invocation
        #   of a role with an explicit title, i.e. we use href to resolve rule
        #   and we don't mess with title at all.
        # - title_is_weak is set. This means that title comes from a nodoc rule.
        #   In this case we use title only if rule resolution fails.

        title = text
        if href is None:
            target = text
            explicit_title = False
        else:
            target = href
            explicit_title = not title_is_weak

        builder = self.builder
        env = builder.env
        domain = env.get_domain('a4')
        docname = builder.current_docname

        xref = sphinx.addnodes.pending_xref(
            '',
            reftype='rule',
            refdomain='a4',
            refexplicit=explicit_title
        )
        xref['a4:grammar'] = self.grammar

        try:
            node: docutils.nodes.Element = domain.resolve_xref(
                env,
                docname,
                builder,
                'rule',
                target,
                xref,
                docutils.nodes.literal(
                    '', target.rsplit('.', 1)[-1] if title_is_weak else title)
            )
        except sphinx.environment.NoUri:
            node = None

        if node is None:
            return title, None

        reference = node.next_node(docutils.nodes.reference, include_self=True)
        assert reference is not None
        literal = node.next_node(docutils.nodes.literal, include_self=True)
        assert literal is not None

        if 'refuri' in reference:
            return literal.astext(), reference['refuri']
        else:
            return literal.astext(), '#' + reference['refid']


class RailroadDiagramNode(docutils.nodes.Element, docutils.nodes.General):
    def __init__(self, diagram: dict, options: DiagramSettings, grammar: str):
        super().__init__('', diagram=diagram, options=options, grammar=grammar)

    @staticmethod
    def visit_node_html(self: sphinx.writers.html.HTMLTranslator, node):
        resolver = DomainResolver(self.builder, node['grammar'])
        dia = Diagram(settings=node['options'], href_resolver=resolver)
        try:
            data = dia.load(node['diagram'])
            svg = dia.render(data)
        except Exception as e:
            logger.exception(f'{node.source}:{node.line}: WARNING: {e}')
        else:
            self.body.append('<p class="railroad-diagram-container">')
            self.body.append(svg)
            self.body.append('</p>')

    @staticmethod
    def depart_node(self, node):
        pass


class RailroadDiagram(sphinx.util.docutils.SphinxDirective, ManagedDirective):
    """
    This is the most flexible directive for rendering railroad diagrams.
    Its content should be a valid `YAML <https://en.wikipedia.org/wiki/YAML>`_
    document containing the diagram item description.

    The diagram item description itself has a recursive definition.
    It can be one of the next things:

    - ``None`` (denoted as tilde in YAML) will produce a line without objects:

      .. code-block:: rst

         .. railroad-diagram:: ~

      .. highlights::

         .. railroad-diagram:: ~

    - a string will produce a terminal node:

      .. code-block:: rst

         .. railroad-diagram:: just some string

      .. highlights::

         .. railroad-diagram:: just some string

    - a list of diagram item descriptions will produce these items rendered one
      next to another:

      .. code-block:: rst

         .. railroad-diagram::

            - terminal 1
            - terminal 2

      .. highlights::

         .. railroad-diagram::

            - terminal 1
            - terminal 2

    - a dict with ``stack`` key produces a vertically stacked sequence.

      The main value (i.e. the one that corresponds to the ``stack`` key)
      should contain a list of diagram item descriptions.
      These items will be rendered vertically:

      .. code-block:: rst

         .. railroad-diagram::

            stack:
            - terminal 1
            -
              - terminal 2
              - terminal 3

      .. highlights::

         .. railroad-diagram::

            stack:
            - terminal 1
            -
              - terminal 2
              - terminal 3

    - a dict with ``choice`` key produces an alternative.

      The main value should contain a list of diagram item descriptions:

      .. code-block:: rst

         .. railroad-diagram::

            choice:
            - terminal 1
            -
              - terminal 2
              - terminal 3

      .. highlights::

         .. railroad-diagram::

            choice:
            - terminal 1
            -
              - terminal 2
              - terminal 3

    - a dict with ``optional`` key will produce an optional item.

      The main value should contain a single diagram item description.

      Additionally, the ``skip`` key with a boolean value may be added.
      If equal to true, the element will be rendered off the main line:

      .. code-block:: rst

         .. railroad-diagram::

            optional:
            - terminal 1
            - optional:
              - terminal 2
              skip: true

      .. highlights::

         .. railroad-diagram::

            optional:
            - terminal 1
            - optional:
              - terminal 2
              skip: true

    - a dict with ``one_or_more`` key will produce a loop.

      The ``one_or_more`` element of the dict should contain a single diagram
      item description.

      Additionally, the ``repeat`` key with another diagram item description
      may be added to insert nodes to the inverse connection of the loop.

      .. code-block:: rst

         .. railroad-diagram::

            one_or_more:
            - terminal 1
            - terminal 2
            repeat:
            - terminal 3
            - terminal 4

      .. highlights::

         .. railroad-diagram::

            one_or_more:
            - terminal 1
            - terminal 2
            repeat:
            - terminal 3
            - terminal 4

    - a dict with ``zero_or_more`` key works like ``one_or_more`` except that
      the produced item is optional:

      .. code-block:: rst

         .. railroad-diagram::

            zero_or_more:
            - terminal 1
            - terminal 2
            repeat:
            - terminal 3
            - terminal 4

      .. highlights::

         .. railroad-diagram::

            zero_or_more:
            - terminal 1
            - terminal 2
            repeat:
            - terminal 3
            - terminal 4

    - a dict with ``node`` key produces a textual node of configurable shape.

      The main value should contain text which will be rendered in the node.

      Optional keys include ``href``, ``css_class``, ``radius`` and ``padding``.

      .. code-block:: rst

         .. railroad-diagram::

            node: go to google
            href: https://www.google.com/
            css_class: terminal
            radius: 3
            padding: 50

      .. highlights::

         .. railroad-diagram::

            node: go to google
            href: https://www.google.com/
            css_class: terminal
            radius: 3
            padding: 50

    - a dict with ``terminal`` key produces a terminal node.

      It works exactly like ``node``. The only optional key is ``href``.

    - a dict with ``non_terminal`` key produces a non-terminal node.

      It works exactly like ``node``. The only optional key is ``href``.

    - a dict with ``comment`` key produces a comment node.

      It works exactly like ``node``. The only optional key is ``href``.

    **Example:**

    This example renders a diagram from the :ref:`features <features>` section:

    .. code-block:: rst

       .. railroad-diagram::
          - choice:
            - terminal: 'parser'
            -
            - terminal: 'lexer '
            default: 1
          - terminal: 'grammar'
          - non_terminal: 'identifier'
          - terminal: ';'

    which translates to:

    .. highlights::

       .. railroad-diagram::
          - choice:
            - terminal: 'parser'
            -
            - terminal: 'lexer '
            default: 1
          - terminal: 'grammar'
          - non_terminal: 'identifier'
          - terminal: ';'

    **Customization:**

    See more on how to customize diagram style in the ':ref:`custom_style`'
    section.

    """

    has_content = True

    settings = diagram_namespace.for_directive()

    def run(self):
        grammar = self.env.ref_context.get('a4:grammar', '__default__')

        try:
            content = self.get_content()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    str(e),
                    line=self.lineno
                )
            ]
        return [RailroadDiagramNode(content, self.settings, grammar)]

    def get_content(self):
        return yaml.safe_load('\n'.join(self.content))


class LexerRuleDiagram(RailroadDiagram):
    """
    The body of this directive should contain a valid Antlr4 lexer rule
    description.

    For example

    .. code-block:: rst

       .. lexer-rule-diagram:: ('+' | '-')? [1-9] [0-9]*

    translates to:

    .. highlights::

       .. lexer-rule-diagram:: ('+' | '-')? [1-9] [0-9]*

    **Options:**

    Options are inherited from the :rst:dir:`railroad-diagram` directive.

    """

    def get_content(self):
        raw = "\n".join(self.content)
        content = f'grammar X; ROOT : {raw} ;'
        model = ModelCache.instance().from_text(
            content, (self.state_machine.reporter.source, self.content_offset))
        tree = model.lookup('ROOT')
        if tree is None or tree.content is None:
            raise RuntimeError('cannot parse the rule')
        return Renderer().visit(tree.content)


class ParserRuleDiagram(RailroadDiagram):
    """
    The body of this directive should contain a valid Antlr4 parser rule
    description.

    For example

    .. code-block:: rst

       .. parser-rule-diagram::

          SELECT DISTINCT?
          ('*' | expression (AS row_name)?
                 (',' expression (AS row_name)?)*)

    translates to:

    .. highlights::

       .. parser-rule-diagram::

          SELECT DISTINCT?
          ('*' | expression (AS row_name)?
                 (',' expression (AS row_name)?)*)


    **Options:**

    Options are inherited from the :rst:dir:`railroad-diagram` directive.

    """

    def get_content(self):
        raw = "\n".join(self.content)
        content = f'grammar X; root : {raw} ;'
        model = ModelCache.instance().from_text(
            content, (self.state_machine.reporter.source, self.content_offset))
        tree = model.lookup('root')
        if tree is None or tree.content is None:
            raise RuntimeError('cannot parse the rule')
        return Renderer().visit(tree.content)
