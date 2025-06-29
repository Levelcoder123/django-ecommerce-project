# store/views.py

# --- Django & Python Imports ---
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# --- Third-Party Imports ---
import stripe
from rest_framework import permissions, viewsets, status, serializers, generics
from rest_framework.response import Response

# --- Local Application Imports ---
from .forms import CustomAuthenticationForm, OrderAddressForm, CustomUserCreationForm
from .models import User, Category, Product, Cart, CartItem, Order, OrderItem
from .permissions import IsAdminOrReadOnly
from .serializers import (
    UserSerializer, CategorySerializer, ProductSerializer, UserRegistrationSerializer,
    CartSerializer, CartItemSerializer, CartItemCreateUpdateSerializer,
    OrderCreateSerializer, OrderSerializer, PaymentIntentCreateSerializer
)


# =============================================================================
# --- API Views (Django REST Framework) ---
# =============================================================================

# --- User API Views ---
class UserRegistrationView(generics.CreateAPIView):
    """API endpoint for new user registration. Open to anyone."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer


class UserList(generics.ListAPIView):
    """API endpoint to list all users. For admin use only."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetail(generics.RetrieveAPIView):
    """API endpoint to retrieve a single user's details. For admin use only."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


# --- Category API Views ---
class CategoryListCreate(generics.ListCreateAPIView):
    """API endpoint to list all categories or create a new one."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint to retrieve, update, or delete a single category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


# --- Product API Views ---
class ProductListCreate(generics.ListCreateAPIView):
    """API endpoint to list all available products or create a new one."""
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint to retrieve, update, or delete a single product."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


# --- Cart API Views ---
class CartDetailView(generics.RetrieveAPIView):
    """API endpoint to retrieve the current authenticated user's cart."""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing items in the authenticated user's cart."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CartItemCreateUpdateSerializer
        return CartItemSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, pk=serializer.validated_data['product_id'])
        quantity_to_add = serializer.validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 0}
        )

        prospective_total = cart_item.quantity + quantity_to_add
        if prospective_total > product.stock:
            raise serializers.ValidationError({
                'detail': f"Cannot add {quantity_to_add} item(s). Only {product.stock} available."
            })

        if created:
            cart_item.quantity = quantity_to_add
        else:
            cart_item.quantity += quantity_to_add
        cart_item.save()

        display_serializer = CartItemSerializer(cart_item, context={'request': request})
        headers = self.get_success_headers(display_serializer.data)
        return Response(display_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
                        headers=headers)


# --- Order API Views ---
class OrderCreateView(generics.CreateAPIView):
    """API endpoint to create an order from the user's cart."""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read_serializer = OrderSerializer(order, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and retrieving an authenticated user's orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# --- Payment API Views ---
class CreatePaymentIntentView(generics.GenericAPIView):
    """API endpoint to create a Stripe Payment Intent for an order."""
    serializer_class = PaymentIntentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = get_object_or_404(Order, pk=serializer.validated_data['order_id'], user=request.user)
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),
                currency='usd',
                automatic_payment_methods={'enabled': True},
                metadata={'order_id': order.id, 'user_id': request.user.id}
            )
            return Response({'clientSecret': intent.client_secret})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmOrderPaymentView(generics.GenericAPIView):
    """Mock API endpoint to confirm payment for an order."""
    serializer_class = PaymentIntentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = get_object_or_404(Order, pk=serializer.validated_data['order_id'], user=request.user)
        order.is_completed = True
        order.transaction_id = request.data.get('transaction_id', f"mock_{order.id}")
        order.save(update_fields=['is_completed', 'transaction_id'])
        return Response({'status': 'success', 'message': f'Order {order.id} marked as paid.'})


# =============================================================================
# --- Web Page Views (Django Templates) ---
# =============================================================================

def product_list(request):
    """Displays the home page with a list of all available products."""
    products = Product.objects.filter(is_available=True)
    context = {'products': products}
    return render(request, 'store/product_list.html', context)


def product_detail(request, pk):
    """Displays the detail page for a single product."""
    product = get_object_or_404(Product, pk=pk, is_available=True)
    context = {'product': product}
    return render(request, 'store/product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    """Handles adding a product to the cart. Handles GET requests after login redirect."""
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'GET':
        messages.info(request, "You are now logged in. Please try adding the item again.")
        return redirect('product_detail', pk=product_id)

    if request.method == 'POST':
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            quantity_to_add = int(request.POST.get('quantity', 1))
            if quantity_to_add < 1:
                messages.error(request, "Quantity must be at least 1.")
                return redirect('product_detail', pk=product_id)
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
            return redirect('product_detail', pk=product_id)

        cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        prospective_total = cart_item.quantity + quantity_to_add

        if prospective_total > product.stock:
            messages.error(request,
                           f"Cannot add {quantity_to_add} of '{product.name}'. Only {product.stock} available.")
        else:
            cart_item.quantity = prospective_total
            cart_item.save()
            messages.success(request, f"Updated cart with {quantity_to_add} x {product.name}.")

    return redirect('product_detail', pk=product_id)


@login_required
def cart_detail(request):
    """Displays the user's shopping cart."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    context = {'cart': cart}
    return render(request, 'store/cart_detail.html', context)


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Removes an item from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart_detail')


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Updates the quantity of an item in the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get('quantity'))
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity provided.")
        return redirect('cart_detail')

    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f"Removed {cart_item.product.name} from your cart.")
    elif quantity > cart_item.product.stock:
        messages.error(request,
                       f"Cannot update quantity. Only {cart_item.product.stock} of {cart_item.product.name} available.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Updated quantity for {cart_item.product.name}.")

    return redirect('cart_detail')


@login_required
def checkout_page_view(request):
    """Displays the checkout page with cart summary and address form."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect('cart_detail')

    initial_address_data = {
        'address': request.user.address or '',
        'city': request.user.city or '',
        'postal_code': request.user.postal_code or '',
        'country': request.user.country or '',
    }
    address_form = OrderAddressForm(initial=initial_address_data)

    context = {'cart': cart, 'address_form': address_form}
    return render(request, 'store/checkout_page.html', context)


@login_required
@require_POST
def create_order_from_cart_view(request):
    """Handles the creation of an order from the cart using the credits system."""
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart_detail')

    cart_total = cart.get_total_price()
    if user.credits < cart_total:
        messages.error(request, f"Insufficient credits. You need ${cart_total:.2f} but only have ${user.credits:.2f}.")
        return redirect('checkout_page')

    serializer = OrderCreateSerializer(data=request.POST or {}, context={'request': request})
    if serializer.is_valid():
        try:
            order = serializer.save()
            user.credits -= order.total_amount
            user.save(update_fields=['credits'])
            order.is_completed = True
            order.transaction_id = f"credits_{order.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            order.save(update_fields=['is_completed', 'transaction_id'])
            messages.success(request, f"Thank you! Order #{order.id} placed. New balance: ${user.credits:.2f}.")
            return redirect('order_success', order_id=order.id)
        except (serializers.ValidationError, Exception) as e:
            error_message = str(e.detail[0]) if hasattr(e, 'detail') else str(e)
            messages.error(request, f"Could not place order: {error_message}")
    else:
        messages.error(request, "There was an issue with the address information provided.")

    return redirect('checkout_page')


@login_required
def order_success_view(request, order_id):
    """Displays the order confirmation page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'store/order_success.html', context)


@login_required
def my_orders_view(request):
    """Displays the user's order history."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'items__product').order_by(
        '-date_ordered')
    context = {'orders': orders}
    return render(request, 'store/my_orders.html', context)


# --- Authentication Web Page Views ---
def login_page_view(request):
    """Displays and processes the login form."""
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_page = request.GET.get('next')
            return redirect(next_page) if next_page else redirect('product_list')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logs the user out."""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('product_list')


def register_page_view(request):
    """Displays and processes the registration form."""
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Registration successful! Welcome, {user.username}.")
            return redirect('product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})
