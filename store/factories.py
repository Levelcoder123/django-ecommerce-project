import factory
from factory.django import DjangoModelFactory

from store.models import User, Category, Product, Order, CartItem, Cart


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')

    # This automatically creates a Cart right after a User is created
    # and links it back to the user.
    cart = factory.RelatedFactory('store.factories.CartFactory', factory_related_name='user')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or 'defaultpassword123'
        self.set_password(password)


class CartFactory(DjangoModelFactory):
    class Meta:
        model = Cart

    # The 'user' field will be handled by the RelatedFactory in UserFactory
    # No need to define it here when used that way.


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    description = factory.Faker('sentence')


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('catch_phrase')
    description = factory.Faker('text')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    stock = factory.Faker('random_int', min=5, max=50)
    is_available = True

    # This automatically creates a Category using CategoryFactory
    # and links it to this product.
    category = factory.SubFactory(CategoryFactory)


class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    total_amount = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    is_completed = True
