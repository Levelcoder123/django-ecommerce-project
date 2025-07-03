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

# --- NEW HACKING-THEMED DATA ---
HACKING_CATEGORIES = [
    "Hardware Tools", "Wireless Hacking", "Software Tools",
    "Network Analysis", "Forensics", "Development Kits"
]

HACKING_PRODUCTS = {
    "Hardware Tools": [
        {"name": "USB Rubber Ducky", "desc": "A keystroke injection tool disguised as a USB drive.", "price": 49.99},
        {"name": "Flipper Zero", "desc": "A multi-tool device for pentesting, hardware, and IoT enthusiasts.",
         "price": 169.00},
        {"name": "Proxmark3 RDV4", "desc": "The gold standard for RFID/NFC research and security testing.",
         "price": 320.00},
        {"name": "LAN Turtle", "desc": "A covert system administration and penetration testing tool.", "price": 59.99},
    ],
    "Wireless Hacking": [
        {"name": "WiFi Pineapple Mark VII", "desc": "The leading rogue access point and WiFi auditing platform.",
         "price": 199.99},
        {"name": "HackRF One",
         "desc": "A Software Defined Radio (SDR) peripheral capable of transmission or reception of radio signals.",
         "price": 330.00},
        {"name": "Alfa AWUS036ACH WiFi Adapter",
         "desc": "High-gain long-range dual-band USB adapter for packet injection.", "price": 59.95},
    ],
    "Software Tools": [
        {"name": "Metasploit Pro", "desc": "Advanced penetration testing solution. 1-Year Subscription.",
         "price": 15000.00},
        {"name": "Burp Suite Professional",
         "desc": "The web application security tester's toolkit. 1-Year Subscription.", "price": 449.00},
    ],
    "Network Analysis": [
        {"name": "Packet Squirrel", "desc": "A stealthy, pocket-sized man-in-the-middle tool.", "price": 29.99},
        {"name": "Plunder Bug", "desc": "A pocket-sized, passive LAN Tap that's undetectable to the network.",
         "price": 19.99},
    ],
    "Development Kits": [
        {"name": "Raspberry Pi 4 Pentest Kit",
         "desc": "A complete kit with a Raspberry Pi 4 and essential accessories for mobile pentesting.",
         "price": 120.00},
        {"name": "ESP32 Marauder Kit",
         "desc": "A portable WiFi and Bluetooth penetration testing tool based on the ESP32.", "price": 65.00},
    ]
}


@transaction.atomic
def populate_data(clear_existing_data=True):
    """
    Populates the database with sample hacking-themed data.
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
    print('Creating hacking categories...')
    categories = {}
    for cat_name in HACKING_CATEGORIES:
        category = CategoryFactory(name=cat_name)
        categories[cat_name] = category
    print(f'{len(categories)} categories created.')

    # Create Products
    print('Creating hacking products...')
    products = []
    for category_name, product_list in HACKING_PRODUCTS.items():
        category_obj = categories.get(category_name)
        if category_obj:
            for prod_data in product_list:
                products.append(ProductFactory(
                    name=prod_data["name"],
                    description=prod_data["desc"],
                    price=Decimal(str(prod_data["price"])),
                    category=category_obj,
                    stock=random.randint(5, 50)
                ))
    print(f'{len(products)} products created.')

    # Create Users and Orders (can be kept as is)
    print('Creating 5 sample users...')
    users = [UserFactory() for _ in range(5)]
    print(f'{len(users)} users created.')

    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        admin_user.credits = Decimal('1000.00')
        admin_user.save(update_fields=['credits'])
        print(f'Gave admin user {admin_user.username} 1000 credits.')

    if users and products:
        print('Creating some sample orders...')
        orders_created_count = 0
        for user_for_order in users:
            for _ in range(random.randint(0, 2)):
                OrderFactory(user=user_for_order)
                orders_created_count += 1
        print(f'{orders_created_count} orders created.')

    print('Data population complete!')


if __name__ == '__main__':
    print("This script should be run from within the Django shell.")
