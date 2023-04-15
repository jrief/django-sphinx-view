from pathlib import Path

from django.conf import settings
from django.urls import include, path

from sphinx_view import DocumentationView


urlpatterns = [
    path('sphinx-view-demo/', include('docs.build.json.urls')),
    path('search/',
         DocumentationView.as_view(is_search=True),
         name="search",
    ),
    path('<path:path>',
         DocumentationView.as_view(),
    ),
    path('',
         DocumentationView.as_view(is_index=True),
         name="root",
    ),
]
