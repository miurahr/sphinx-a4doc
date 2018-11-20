from dataclasses import dataclass, field
from enum import Enum

from sphinx_a4doc.contrib.configurator import Namespace

from typing import *


class InternalAlignment(Enum):
    """
    Controls how to align nodes within a single railroad.
    See `DiagramSettings.internal_alignment` for documentation on elements.

    """

    CENTER = 'CENTER'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    AUTO_LEFT = 'AUTO_LEFT'
    AUTO_RIGHT = 'AUTO_RIGHT'


class EndClass(Enum):
    """
    Controls how diagram start and end look like.
    See `DiagramSettings.end_class` for documentation on elements.

    """

    SIMPLE = 'SIMPLE'
    COMPLEX = 'COMPLEX'


class GrammarType(Enum):
    """
    Antlr4 grammar types.

    """

    MIXED = 'MIXED'
    LEXER = 'LEXER'
    PARSER = 'PARSER'


class OrderSettings(Enum):
    """
    Controls how autodoc orders rules that are extracted from sources.

    """

    BY_SOURCE = 'BY_SOURCE'
    """
    Order by position in source file.
    
    """

    BY_NAME = 'BY_NAME'
    """
    Order by human-readable name.
    
    """


class GroupingSettings(Enum):
    """
    Controls how autodoc groups rules that are extracted from sources.

    """

    MIXED = 'MIXED'
    """
    Rules are not ordered.
    
    """

    LEXER_FIRST = 'LEXER_FIRST'
    """
    Lexer rules go first.
    
    """

    PARSER_FIRST = 'PARSER_FIRST'
    """
    Parser rules go first.
    
    """


@dataclass(frozen=True)
class DiagramSettings:
    """
    Settings for diagram directive.

    """

    padding: Tuple[int, int, int, int] = (1, 1, 1, 1)
    """
    Array of four positive integers denoting top, right, bottom and left
    padding between the diagram and its container. By default, there is 1px
    of padding on each side.
    
    """

    vertical_separation: int = 8
    """
    Vertical space between diagram lines.
    
    """

    horizontal_separation: int = 10
    """
    Horizontal space between items within a sequence.
    
    """

    arc_radius: int = 10
    """
    Arc radius of railroads. 10px by default.
    
    """

    diagram_class: str = 'railroad-diagram'
    """
    CSS class for the SVG node in which the diagram will be rendered.
    
    """

    translate_half_pixel: bool = False
    """
    If enabled, the diagram will be translated half-pixel in both directions.
    May be used to deal with anti-aliasing issues when using odd stroke widths.
    
    """

    internal_alignment: InternalAlignment = InternalAlignment.AUTO_LEFT
    """
    Determines how nodes aligned within a single diagram line. Available
    options are:

    - ``center`` -- nodes are centered.

      .. parser-rule-diagram:: (A B | C D E) (',' (A B | C D E))*
         :internal-alignment: CENTER

    - ``left`` -- nodes are flushed to left in all cases.

      .. parser-rule-diagram:: (A B | C D E) (',' (A B | C D E))*
         :internal-alignment: LEFT

    - ``right`` -- nodes are flushed to right in all cases.

      .. parser-rule-diagram:: (A B | C D E) (',' (A B | C D E))*
         :internal-alignment: RIGHT

    - ``auto_left`` -- nodes in choice groups are flushed left,
      all other nodes are centered.

      .. parser-rule-diagram:: (A B | C D E) (',' (A B | C D E))*
         :internal-alignment: AUTO_LEFT

    - ``auto_right`` -- nodes in choice groups are flushed right,
      all other nodes are centered.

      .. parser-rule-diagram:: (A B | C D E) (',' (A B | C D E))*
         :internal-alignment: AUTO_RIGHT
    
    """

    character_advance: float = 8.4
    """
    Average length of one character in the used font. Since SVG elements
    cannot expand and shrink dynamically, length of text nodes is calculated
    as number of symbols multiplied by this constant.
    
    """

    end_class: EndClass = EndClass.SIMPLE
    """
    Controls how diagram start and end look like. Available options are:

    - ``simple`` -- a simple ``T``-shaped ending.

      .. parser-rule-diagram:: X
         :end-class: SIMPLE

    - ``complex`` -- a ``T``-shaped ending with vertical line doubled.

      .. parser-rule-diagram:: X
         :end-class: COMPLEX
    
    """

    max_width: int = 500
    """
    Max width after which a sequence will be wrapped. This option is used to
    automatically convert sequences to stacks. Note that this is a suggestive
    option, there is no guarantee that the diagram will
    fit to its ``max_width``.
    
    """


@dataclass(frozen=True)
class GrammarSettings:
    """
    Settings for grammar directive.

    """

    name: Optional[str] = field(default=None, metadata=dict(no_global=True))
    """
    Specifies a human-readable name for the grammar.

    If given, the human-readable name will be rendered instead of the primary
    grammar name. It will also replace the primary name in all cross references.

    For example this code:

    .. code-block:: rst

       .. a4:grammar:: PrimaryName
          :name: Human-readable name

    will render the next grammar description:

    .. highlights::

       .. a4:grammar:: PrimaryName
          :noindex:
          :name: Human-readable name
    
    """

    type: GrammarType = field(default=GrammarType.MIXED, metadata=dict(no_global=True))
    """
    Specifies a grammar type. The type will be displayed in the grammar
    signature.

    For example these three grammars:

    .. code-block:: rst

       .. a4:grammar:: Grammar1

       .. a4:grammar:: Grammar2
          :type: lexer

       .. a4:grammar:: Grammar3
          :type: parser

    will be rendered differently:

    .. highlights::

       .. a4:grammar:: Grammar1
          :noindex:

       .. a4:grammar:: Grammar2
          :noindex:
          :type: lexer

       .. a4:grammar:: Grammar3
          :noindex:
          :type: parser
    
    """

    imports: List[str] = field(default_factory=list, metadata=dict(no_global=True))
    """
    Specifies a list of imported grammars.

    This option affects name resolution process for rule cross-references.
    That is, if there is a reference to ``grammar.rule`` and there is no
    ``rule`` found in the ``grammar``, the imported grammars will be searched
    as well.
    
    """


@dataclass(frozen=True)
class RuleSettings:
    """
    Settings for rule directive.

    """

    name: Optional[str] = field(default=None, metadata=dict(no_global=True))
    """
    Specifies a human-readable name for this rule. Refer to the corresponding
    :rst:dir:`a4:grammar`'s option for more info.
    
    """


@dataclass(frozen=True)
class AutodocSettings:
    """
    Settings for autodoc directives.

    """

    only_reachable_from: Optional[str] = field(default=None, metadata=dict(no_global=True, rebuild=True))
    """
    If given, only document items that are reachable from rule with this path.
    
    """

    name: Optional[str] = field(default=None, metadata=dict(no_global=True, rebuild=True))
    """
    Human-readable name. Displayed instead of the default name.
    
    """

    lexer_rules: bool = field(default=True, metadata=dict(rebuild=True))
    """
    Controls whether lexer rules should appear in documentation.
    
    """

    parser_rules: bool = field(default=True, metadata=dict(rebuild=True))
    """
    Controls whether parser rules should appear in documentation.
    
    """

    fragments: bool = field(default=False, metadata=dict(rebuild=True))
    """
    Controls whether fragments should appear in documentation.
    
    """

    undocumented: bool = field(default=False, metadata=dict(rebuild=True))
    """
    Controls whether undocumented rules should appear in documentation.
    
    """

    ordering: OrderSettings = field(default=OrderSettings.BY_SOURCE, metadata=dict(rebuild=True))
    """
    Controls how autodoc orders rules that are extracted from sources.
    
    """

    grouping: GroupingSettings = field(default=GroupingSettings.MIXED, metadata=dict(rebuild=True))
    """
    Controls how autodoc groups rules that are extracted from sources.

    """


@dataclass(frozen=True)
class GlobalSettings:
    """
    Global A4Doc settings. Each member of this dataclass will be added
    to the global sphinx settings registry with prefix ``a4_``.

    """

    base_path: str = field(default='.', metadata=dict(rebuild=True))
    """
    Path which autodoc searches for grammar files.
    
    """


diagram_namespace = Namespace('a4_diagram', DiagramSettings)
grammar_namespace = Namespace('a4_grammar', GrammarSettings)
rule_namespace = Namespace('a4_rule', RuleSettings)
autodoc_namespace = Namespace('a4_autodoc', AutodocSettings)
global_namespace = Namespace('a4', GlobalSettings)


def register_settings(app):
    diagram_namespace.register_settings(app)
    grammar_namespace.register_settings(app)
    rule_namespace.register_settings(app)
    autodoc_namespace.register_settings(app)
    global_namespace.register_settings(app)