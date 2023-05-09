"""Serve your Sphinx docs with Django."""
from .builders import SphinxViewBuilder, process_django_views, purge_django_views
from .directive import DjangoViewDirective, DjangoReferredViewDirective
from .views import DocumentationView

__version__ = '23.dev0'

__all__ = [
    "__version__",
    "DocumentationView",
    "DjangoViewDirective",
    "SphinxViewBuilder",
]


def setup(app):
    app.add_builder(SphinxViewBuilder, override=True)
    app.add_directive("django-view", DjangoViewDirective)
    app.add_directive("django-referred-view", DjangoReferredViewDirective)
    app.connect("env-updated", process_django_views)
    app.connect("env-purge-doc", purge_django_views)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
