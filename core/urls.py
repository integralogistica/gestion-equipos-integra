"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from usuarios.views import CustomAuthToken # 1. Importar nuestra vista personalizada

urlpatterns = [
    path('admin/', admin.site.urls),

    # 2. Registrar la nueva ruta de login
    path('api/login/', CustomAuthToken.as_view(), name='api_login'),

    # Mantener las otras rutas de tu API
    path('api/', include('inventory.urls')),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/empleados/', include('empleados.urls')),
    path('api/mantenimientos/', include('mantenimientos.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

# Servir archivos media en desarrollo y producción (necesario para Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
