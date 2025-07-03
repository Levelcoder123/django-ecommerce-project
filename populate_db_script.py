# populate_db_script.py
import random
import os
import django
from decimal import Decimal

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_store.settings')
django.setup()

# Now we can import Django models and our factories
from django.db import transaction
from store.models import Category, Product, User, Order, OrderItem, Cart, CartItem
from store.factories import (
    UserFactory, CategoryFactory, ProductFactory,
    OrderFactory
)

# Define some realistic category names
REALISTIC_CATEGORIES = [
    "Electronics", "Books", "Clothing", "Home & Kitchen", "Sports & Outdoors",
    "Toys & Games", "Beauty & Personal Care", "Automotive", "Grocery", "Pet Supplies"
]


@transaction.atomic
def populate_data(
        num_users=5,
        num_categories=len(REALISTIC_CATEGORIES),
        num_products=50,
        num_orders_per_user=2,
        clear_existing_data=False
):
    """
    Populates the database with sample data.
    """

    if clear_existing_data:
        print('WARNING: Clearing existing data (excluding superusers)...')
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.filter(user__is_superuser=False).delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        print('Old data cleared.')

    print('Starting data population...')

    # Create Categories
    print(f'Creating {num_categories} categories...')
    categories = []
    created_category_names = set()
    for i in range(num_categories):
        base_name = REALISTIC_CATEGORIES[i % len(REALISTIC_CATEGORIES)]
        category_name = base_name
        suffix_num = 1
        while category_name in created_category_names:
            category_name = f"{base_name} #{suffix_num}"
            suffix_num += 1

        try:
            category = CategoryFactory(name=category_name)
            categories.append(category)
            created_category_names.add(category_name)
        except Exception as e:
            print(f"Could not create category '{category_name}': {e}")

    if not categories:
        print('No categories created. Cannot create products.')
        return

    print(f'{len(categories)} categories created.')

    # Create Products
    print(f'Creating {num_products} products...')
    products = [ProductFactory(category=random.choice(categories)) for _ in range(num_products)]
    print(f'{len(products)} products created.')

    # Create Users
    print(f'Creating {num_users} regular users...')
    users = [UserFactory() for _ in range(num_users)]
    print(f'{len(users)} users created.')

    # Give admin user some credits for testing
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        admin_user.credits = Decimal('500.00')
        admin_user.save(update_fields=['credits'])
        print(f'Gave admin user {admin_user.username} 500 credits.')

    # Create Orders for some users
    if num_orders_per_user > 0 and users and products:
        print(f'Creating up to {num_orders_per_user} orders for each user...')
        orders_created_count = 0
        for user_for_order in users:
            for _ in range(random.randint(0, num_orders_per_user)):
                OrderFactory(user=user_for_order)
                orders_created_count += 1
        print(f'{orders_created_count} orders created.')

    print('Data population complete!')


# This part allows the script to be run directly, but we will run it via the Django shell
if __name__ == '__main__':
    print("This script should be run from within the Django shell.")
    print("Use: python manage.py shell")
    print("Then: exec(open('populate_db_script.py').read())")
    print("Finally: populate_data()")
