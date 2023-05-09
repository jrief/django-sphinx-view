import ast

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.directives.code import CodeBlock
from sphinx.errors import DocumentError
from sphinx.util.docutils import SphinxDirective


class DjangoViewDirective(CodeBlock):
    required_arguments = 1
    optional_arguments = 0
    option_spec = CodeBlock.option_spec
    option_spec.update({
        'view-function': directives.unchanged_required,
        'hide-code': directives.flag,
        'swap-code': directives.flag,
        'hide-view': directives.flag,
    })

    def __init__(self, name, arguments, options, content, *args):
        if not options.get('view-function'):
            raise DocumentError("Directive '.. django-view::' requires mandatory option :view-function:")
        if 'hide-code' in options and 'swap-code' in options:
            raise DocumentError("Directive '.. django-view::' can not specify both :hide-code: and :swap-code:")
        try:
            ast.parse('\n'.join(content))
        except SyntaxError as exception:
            raise DocumentError("Syntax error in '.. django-view::'", exception)
        self.django_view_name = arguments[0]
        arguments = ['python']
        super().__init__(name, arguments, options, content, *args)

    def run(self):
        literals = super().run()
        if not hasattr(self.env, 'django_all_views'):
            self.env.django_all_views = {}
        if not hasattr(self.env, 'django_doc_views'):
            self.env.django_doc_views = {}
        if not hasattr(self.env, 'django_urlpatterns'):
            self.env.django_urlpatterns = {}
        self.env.django_all_views[self.django_view_name] = '\n'.join(self.content)
        self.env.django_doc_views.setdefault(self.env.docname, [])
        self.env.django_doc_views[self.env.docname].append(self.django_view_name)
        self.env.django_urlpatterns[self.django_view_name] = self.options['view-function']
        attributes = {'format': 'html'}
        raw_node = nodes.raw(
            '',
            f'{{% endverbatim %}}{{{{ content_{self.django_view_name} }}}}{{% verbatim %}}', **attributes
        )
        if 'hide-view' not in self.options:
            if 'hide-code' in self.options:
                literals = [raw_node]
            elif 'swap-code' in self.options:
                literals.insert(0, raw_node)
            else:
                literals.append(raw_node)
        return literals


class DjangoReferredViewDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0

    def __init__(self, name, arguments, options, content, *args):
        self.django_view_name = arguments[0]
        super().__init__(name, arguments, options, content, *args)

    def run(self):
        if not hasattr(self.env, 'django_all_views') or self.django_view_name not in self.env.django_all_views:
            raise DocumentError(f"No document contains a directive '.. django-view:: {self.django_view_name}'")
        attributes = {'format': 'html'}
        raw_node = nodes.raw('', f'{{% endverbatim %}}{{{{ content_{self.django_view_name} }}}}{{% verbatim %}}', **attributes)
        return [raw_node]
