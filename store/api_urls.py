# store/api_urls.py

# --- Django & Third-Party Imports ---
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- Local Application Imports ---
from . import views

# =============================================================================
# --- Router Configuration ---
# =============================================================================
# ViewSets provide a full set of CRUD actions without needing separate views.
router = DefaultRouter()
router.register(r'cart-items', views.CartItemViewSet, basename='cartitem')
router.register(r'orders', views.OrderViewSet, basename='order')

# =============================================================================
# --- URL Patterns ---
# =============================================================================
# All URLs here are prefixed with /api/ from the main urls.py
urlpatterns = [
    # --- Authentication ---
    path('register/', views.UserRegistrationView.as_view(), name='api-register'),

    # --- Users ---
    path('users/', views.UserList.as_view(), name='api-user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='api-user-detail'),

    # --- Categories ---
    path('categories/', views.CategoryListCreate.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='api-category-detail'),

    # --- Products ---
    path('products/', views.ProductListCreate.as_view(), name='api-product-list'),
    path('products/<int:pk>/', views.ProductDetail.as_view(), name='api-product-detail'),

    # --- Cart ---
    path('cart/', views.CartDetailView.as_view(), name='api-cart-detail'),

    # --- Orders (Specific Actions) ---
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),

    # --- Payment (Mock Stripe) ---
    path('payment/create-intent/', views.CreatePaymentIntentView.as_view(), name='api-create-payment-intent'),
    path('payment/confirm-order/', views.ConfirmOrderPaymentView.as_view(), name='api-confirm-order-payment'),

    # --- Include Router URLs ---
    # This automatically generates URLs for the registered ViewSets.
    # e.g., /api/cart-items/, /api/cart-items/<pk>/, /api/orders/, /api/orders/<pk>/
    path('', include(router.urls)),
]
