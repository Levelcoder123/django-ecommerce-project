from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from store.models import User, Category, Product, Cart, OrderItem, Order, CartItem


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Info', {'fields': ('phone_number', 'address', 'city', 'country', 'credits')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Info', {'fields': ('phone_number', 'address', 'city', 'country', 'credits')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'price', 'stock', 'is_available', 'date_updated')
    list_filter = ('is_available', 'category', 'date_updated')
    list_editable = ('price', 'stock', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('-date_updated',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'get_total_items', 'get_total_price')
    readonly_fields = ('created_at', 'updated_at')


# Re-register CartAdmin to include CartItemInline if you prefer inline editing
# For now, let's keep them separate for clarity
# admin.site.unregister(Cart)
# @admin.register(Cart)
# class CartAdminWithItems(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'updated_at')
#     inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'date_added', 'get_total_price')
    list_filter = ('cart__user', 'product')  # Filter by user via cart, and by product
    search_fields = ('product__name', 'cart__user__username')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'is_completed', 'date_ordered', 'transaction_id')
    list_filter = ('is_completed', 'date_ordered', 'user')
    search_fields = ('id', 'user__username', 'transaction_id')
    readonly_fields = ('date_ordered', 'total_amount')  # total_amount is calculated


@admin.register(OrderItem)  # Optional, as it's inlined in OrderAdmin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_purchase', 'get_cost')
    list_filter = ('order__user', 'product')
    search_fields = ('product__name', 'order__id', 'order__user__username')
