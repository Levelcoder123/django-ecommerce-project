"""
Main URL configuration for the ecommerce_store project.
This file delegates routing to the respective app-level URL configuration files.
"""
# --- Django & Third-Party Imports ---
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# =============================================================================
# --- URL Patterns ---
# =============================================================================
urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API Endpoints ---
    path('api/', include('store.api_urls')),

    # --- JWT Authentication API Endpoints ---
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Web Page Endpoints ---
    path('', include('store.urls')),
]

# --- Static and Media File Serving (for Development) ---
# This pattern is only suitable for development. In production, your web server
# (e.g., Nginx) should be configured to serve these files directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
