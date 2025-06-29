from django.urls import path

from store import views

# =============================================================================
# --- URL Patterns ---
# =============================================================================
# These URLs are for the user-facing, server-side rendered website.
urlpatterns = [
    # --- Product URLs ---
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # --- Cart URLs ---
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/item/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/item/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # --- Checkout & Order URLs ---
    path('checkout/', views.checkout_page_view, name='checkout_page'),
    path('order/create/', views.create_order_from_cart_view, name='create_order_from_cart'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),

    # --- User Account URLs ---
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('register/', views.register_page_view, name='register_page'),
    path('login/', views.login_page_view, name='login_page'),
    path('logout/', views.logout_view, name='logout_view'),
]
