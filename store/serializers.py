# store/serializers.py

# --- Django & Third-Party Imports ---
from django.db.models import F
from rest_framework import serializers

# --- Local Application Imports ---
from .models import User, Category, Product, Cart, CartItem, Order, OrderItem


# =============================================================================
# --- User & Authentication Serializers ---
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying User model data. Excludes sensitive fields.
    """

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'city', 'country', 'credits'
        ]
        # Assumes phone_number, address, city, country, and credits are fields on your User model.


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for handling new user registration. Includes password confirmation.
    """
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        """Ensure passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """Create a new user with a properly hashed password."""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


# =============================================================================
# --- Core Model Serializers (Category & Product) ---
# =============================================================================

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model, including subcategories."""
    subcategories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'subcategories']
        read_only_fields = ['slug']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for the Product model, including the category name for readability."""
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'is_available', 'category', 'category_name', 'image',
            'date_added', 'date_updated'
        ]
        read_only_fields = ['slug', 'date_added', 'date_updated']


# =============================================================================
# --- Cart Serializers ---
# =============================================================================

class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for items within a cart."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    # Use ReadOnlyField for cleaner access to model methods/properties.
    total_price = serializers.ReadOnlyField(source='get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'total_price', 'date_added']
        read_only_fields = ['id', 'date_added']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for the main shopping cart."""
    items = CartItemSerializer(many=True, read_only=True)
    # Use ReadOnlyField for cleaner access to model methods/properties.
    total_price = serializers.ReadOnlyField(source='get_total_price')
    total_items = serializers.ReadOnlyField(source='get_total_items')

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'total_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for adding/updating items in the cart, using product_id."""
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity']

    def validate_product_id(self, value):
        """Check that the product exists and is available."""
        if not Product.objects.filter(pk=value, is_available=True).exists():
            raise serializers.ValidationError("Product does not exist or is not available.")
        return value


# =============================================================================
# --- Order Serializers ---
# =============================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for displaying items within a placed order."""
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_purchase']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for displaying a detailed order history."""
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_username', 'items', 'total_amount',
            'address', 'city', 'postal_code', 'country',
            'date_ordered', 'is_completed', 'transaction_id'
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an order from the cart. Contains all business logic
    for stock validation, order creation, and cart clearing.
    """

    class Meta:
        model = Order
        fields = ['address', 'city', 'postal_code', 'country']

    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.filter(user=user).first()

        if not cart or not cart.items.exists():
            raise serializers.ValidationError("Your cart is empty. Add items before placing an order.")

        order = Order.objects.create(user=user, **validated_data)

        products_to_update = []
        order_items_to_create = []
        total_order_amount = 0

        # Prepare all order items and stock updates
        for cart_item in cart.items.all():
            if cart_item.product.stock < cart_item.quantity:
                order.delete()  # Clean up the partially created order
                raise serializers.ValidationError(
                    f"Insufficient stock for {cart_item.product.name}. "
                    f"Available: {cart_item.product.stock}, Requested: {cart_item.quantity}"
                )

            order_items_to_create.append(
                OrderItem(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price_at_purchase=cart_item.product.price
                )
            )
            total_order_amount += cart_item.get_total_price()

            # Prepare product for stock update using an F() expression
            product = cart_item.product
            product.stock = F('stock') - cart_item.quantity
            products_to_update.append(product)

        # Execute database operations
        OrderItem.objects.bulk_create(order_items_to_create)
        Product.objects.bulk_update(products_to_update, ['stock'])

        # Finalize order and clear cart
        order.total_amount = total_order_amount
        order.save(update_fields=['total_amount'])
        cart.items.all().delete()

        return order


# =============================================================================
# --- Payment Serializers ---
# =============================================================================

class PaymentIntentCreateSerializer(serializers.Serializer):
    """Serializer for validating an order_id to create a payment intent."""
    order_id = serializers.IntegerField()

    def validate_order_id(self, value):
        user = self.context['request'].user
        try:
            order = Order.objects.get(pk=value, user=user, is_completed=False)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid or already completed order does not belong to the current user.")

        if order.total_amount <= 0:
            raise serializers.ValidationError("Order amount must be positive to process payment.")

        return value
