from typing import Any

from django.conf import settings

from docutils.io import StringOutput

from pathlib import Path

from sphinx.environment.adapters.toctree import TocTree
from sphinx.util.template import SphinxRenderer
from sphinxcontrib.serializinghtml import JSONHTMLBuilder


class SphinxViewBuilder(JSONHTMLBuilder):
    name = "json"  # Overriding the default

    def get_doc_context(self, docname: str, body: str, metatags: str) -> dict[str, Any]:
        context = super().get_doc_context(docname, body, metatags)
        if hasattr(self.env, "django_code_snippets"):
            context["django_views"] = list(self.env.django_code_snippets.get(docname, {}).keys())
        return context

    def add_sidebars(self, pagename: str, context: dict) -> None:
        super().add_sidebars(pagename, context)
        self_toctree = TocTree(self.env).get_toctree_for(pagename, self, True)
        context["toctree"] = lambda **kwargs: self.render_partial(self_toctree)["fragment"]
        context["config"] = self.get_app_context()

    def get_app_context(self) -> dict[str, Any]:
        return {
            "author": self.config.author,
            "copyright": self.config.copyright,
            "project": self.config.project,
            "release": self.config.release,
        }

    def write_doc(self, docname, doctree):
        title_node = self.env.longtitles.get(docname)
        title = self.render_partial(title_node)["title"] if title_node else ""
        self.index_page(docname, doctree, title)

        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.fignumbers = self.env.toc_fignumbers.get(docname, {})
        self.imgpath = settings.STATIC_URL + "sphinx-view/_images"
        self.dlpath = settings.STATIC_URL + "sphinx-view/_downloads"
        self.current_docname = docname
        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts["fragment"]
        metatags = self.docwriter.clean_meta

        context = self.get_doc_context(docname, body, metatags)
        self.handle_page(docname, context, event_arg=doctree)


def purge_django_views(app, env, docname):
    if hasattr(env, "django_doc_views"):
        env.django_doc_views.pop(docname, None)


def process_django_views(app, env, *args):
    if not (hasattr(env, "django_code_snippets") and hasattr(env, "django_urlpatterns")):
        return
    for module, code_snippets in env.django_code_snippets.items():
        with open(Path(app.outdir) / f"{module}.py", "w") as fh:
            for python in code_snippets.values():
                fh.write(python)
    context = {
        "modules": env.django_code_snippets.keys(),
        "urlpatterns": env.django_urlpatterns,
    }
    templates_path = [Path(app.confdir) / t for t in app.config.templates_path]
    templates_path.append(Path(__file__).parent / 'templates/sphinx_view')
    python = SphinxRenderer(templates_path).render("urls.py.jinja2", context)
    with open(Path(app.outdir) / "urls.py", "w") as fh:
        fh.write(python)
