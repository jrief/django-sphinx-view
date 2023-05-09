from django.conf import settings
from django.urls import include, path

from sphinx_view import DocumentationView


assert (settings.BASE_DIR / 'docs/build/json/urls.py').is_file(), "You must build the docs before starting Django"

urlpatterns = [
    path("sphinx-view-endpoint/", include("docs.build.json.urls")),
    path("search/",
         DocumentationView.as_view(is_search=True),
         name="search",
    ),
    path("<path:path>",
         DocumentationView.as_view(),
    ),
    path("",
         DocumentationView.as_view(is_index=True),
         name="root",
    ),
]
