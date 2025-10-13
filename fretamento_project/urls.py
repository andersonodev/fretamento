"""
URL configuration for fretamento_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.health_views import HealthCheckView

# Configurações customizadas do admin
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Administração Django')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Administração do site')

def root_redirect(request):
    """Redireciona a raiz - dashboard para autenticados, login para não autenticados"""
    if request.user.is_authenticated:
        return redirect('core:home')
    return redirect('authentication:login')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_redirect, name='root'),
    path("health/", HealthCheckView.as_view(), name='health_check'),
    path("auth/", include("authentication.urls")),
    path("core/", include("core.urls")),
    path("escalas/", include("escalas.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
