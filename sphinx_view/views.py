from io import StringIO
import json
from pathlib import Path

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404
from django.middleware.csrf import rotate_token
from django.template import Context, Template
from django.urls import reverse, resolve
from django.utils.safestring import mark_safe
from django.utils.html import strip_spaces_between_tags
from django.views.generic.base import TemplateView


class DocumentationView(TemplateView):
    base_template_name = "base.html"
    json_build_dir = Path(getattr(settings, 'SPHINX_BUILD_DIR', settings.BASE_DIR / 'docs/build')) / 'json'
    is_index = is_search = False

    def get_template_names(self):
        if self.is_search:
            return ["sphinx_view/search.html"]
        return ["sphinx_view/page.html"]

    def get_doc_json(self):
        path: str = self.kwargs.get("path", "/")
        if not path.endswith("/"):
            raise Http404
        path = path.rstrip('/')
        base = Path(self.json_build_dir)
        if self.is_index:
            candidate = base / "index.fjson"
        elif self.is_search:
            candidate = base / "search.fjson"
        else:
            candidate = base / f"{path}.fjson"
        if candidate.exists():
            with candidate.open("r") as f:
                return json.load(f)
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_template_name"] = self.base_template_name
        context["doc"] = self.get_doc_json()

        if self.is_search:
            with open(self.json_build_dir / 'searchindex.json', 'r') as fh:
                context["search_index"] = mark_safe(fh.read())
            return context

        render_ctx = {}
        current_page_name = context["doc"]["current_page_name"]
        for django_view in context["doc"]["django_views"]:
            request = WSGIRequest({
                "REQUEST_METHOD": "GET",
                "PATH_INFO": reverse(f"sphinx-view:{current_page_name}.{django_view}"),
                "wsgi.input": StringIO()
            })
            request.COOKIES = self.request.COOKIES.copy()
            if "CSRF_COOKIE" not in self.request.META:
                rotate_token(self.request)
            request.META["CSRF_COOKIE"] = self.request.META["CSRF_COOKIE"]
            resolver = resolve(request.path)
            response = resolver.func(request)
            response.render()
            rendered_view = strip_spaces_between_tags(response.content.decode('utf-8'))
            render_ctx[f"content_{django_view}"] = mark_safe(rendered_view)

        body = context["doc"]["body"]
        template = Template(f"{{% verbatim %}}{body}{{% endverbatim %}}")
        context["doc"]["body"] = template.render(Context(render_ctx))
        return context
