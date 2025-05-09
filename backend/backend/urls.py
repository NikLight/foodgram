from api.views import redirect_to_recipe

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/docs/', TemplateView.as_view(
        template_name='docs/redoc.html'), name='api-docs'),
    path('<str:s>', redirect_to_recipe),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
