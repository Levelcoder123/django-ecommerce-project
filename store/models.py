# store/models.py

# --- Django & Python Imports ---
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.conf import settings
from decimal import Decimal


# =============================================================================
# --- User Model ---
# =============================================================================

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds fields for user profile information and e-commerce credits.
    """
    # Note: username, password, email, first_name, last_name are inherited.
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))

    def __str__(self):
        return self.username


# =============================================================================
# --- Core Store Models (Category & Product) ---
# =============================================================================

class Category(models.Model):
    """Represents a product category, which can be hierarchical."""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True,
                            help_text="Auto-generated from name if left blank.")
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Assign if this is a subcategory."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Represents an item for sale in the store."""
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True,
                            help_text="Auto-generated from name if left blank.")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generates a unique slug if one isn't provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure the slug is unique by appending a number if necessary
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# =============================================================================
# --- Cart Models ---
# =============================================================================

class Cart(models.Model):
    """Represents a user's shopping cart."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_items(self):
        """Returns the total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """Returns the total price of all items in the cart."""
        return sum(item.get_total_price() for item in self.items.all())


class CartItem(models.Model):
    """Represents a single item (a product and its quantity) within a cart."""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart for {self.cart.user.username}"

    def get_total_price(self):
        """Calculates the subtotal for this cart item."""
        return self.quantity * self.product.price


# =============================================================================
# --- Order Models ---
# =============================================================================

class Order(models.Model):
    """Represents a completed customer order."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='orders')
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date_ordered = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-date_ordered']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username if self.user else 'Guest'}"

    def update_total_amount(self):
        """Recalculates total amount from all its items. More efficient to calculate on creation."""
        # Note: This method is less efficient than calculating the total once upon order creation.
        # It requires fetching all related items every time it's called.
        total = sum(item.get_cost() for item in self.items.all())
        if self.total_amount != total:
            self.total_amount = total
            self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    """Represents a single item within a completed order."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        product_name = self.product.name if self.product else "[Deleted Product]"
        return f"{self.quantity} x {product_name} in Order #{self.order.id}"

    def get_cost(self):
        """Calculates the total cost for this line item."""
        return self.quantity * self.price_at_purchase
