from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.factories import UserFactory, CategoryFactory, ProductFactory, OrderFactory, CartItemFactory


class ECommerceAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.admin_user = UserFactory(is_staff=True, is_superuser=True)

        cls.category = CategoryFactory(name='Electronics')
        cls.product = ProductFactory(category=cls.category, stock=10, price='699.99')
        cls.another_product = ProductFactory(category=cls.category, stock=5, price='19.99')

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_product_list_unauthenticated(self):
        url = reverse('api-product-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {i['name'] for i in resp.data},
            {self.product.name, self.another_product.name}
        )

    def test_category_creation_unauthorized(self):
        url = reverse('category-list-create')
        data = {'name': 'New Category'}
        self.assertEqual(
            self.client.post(url, data, format='json').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self._auth(self.user)
        self.assertEqual(
            self.client.post(url, data, format='json').status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_category_creation_admin(self):
        url = reverse('category-list-create')
        self._auth(self.admin_user)
        resp = self.client.post(url, {'name': 'New Category by Admin'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'New Category by Admin')

    def test_add_to_cart_unauthenticated(self):
        url = reverse('cartitem-list')
        resp = self.client.post(url, {'product_id': self.product.id, 'quantity': 1}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_to_cart_authenticated(self):
        self._auth(self.user)
        url = reverse('cartitem-list')
        resp = self.client.post(url, {'product_id': self.product.id, 'quantity': 2}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        item = self.user.cart.items.first()
        self.assertEqual(self.user.cart.items.count(), 1)
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_insufficient_stock(self):
        self._auth(self.user)
        url = reverse('cartitem-list')
        resp = self.client.post(
            url, {'product_id': self.product.id, 'quantity': self.product.stock + 1}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot add', str(resp.data))

    def test_update_cart_item_quantity(self):
        self._auth(self.user)
        item = CartItemFactory(cart=self.user.cart, product=self.product, quantity=1)
        url = reverse('cartitem-detail', kwargs={'pk': item.pk})
        resp = self.client.patch(url, {'quantity': 5}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_delete_cart_item(self):
        self._auth(self.user)
        item = CartItemFactory(cart=self.user.cart, product=self.product, quantity=1)
        self.assertEqual(self.user.cart.items.count(), 1)
        url = reverse('cartitem-detail', kwargs={'pk': item.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.user.cart.items.count(), 0)

    def test_user_cannot_access_another_users_cart(self):
        item = CartItemFactory(cart=self.other_user.cart, product=self.product, quantity=1)
        self._auth(self.user)
        url = reverse('cartitem-detail', kwargs={'pk': item.pk})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_from_cart(self):
        self._auth(self.user)
        self.client.post(reverse('cartitem-list'), {'product_id': self.product.id, 'quantity': 3}, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.cart.items.count(), 1)
        initial_stock = self.product.stock
        resp = self.client.post(
            reverse('order-create'),
            {'address': '123 Test St', 'city': 'Testville'},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        order = self.user.orders.first()
        self.assertEqual(self.user.orders.count(), 1)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal(self.product.price) * 3)
        self.assertEqual(self.user.cart.items.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 3)

    def test_list_own_orders(self):
        OrderFactory(user=self.user, total_amount=100.00)
        OrderFactory(user=self.other_user, total_amount=50.00)
        self._auth(self.user)
        resp = self.client.get(reverse('order-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(float(resp.data[0]['total_amount']), 100.00)

    def test_user_cannot_access_another_users_order_detail(self):
        order = OrderFactory(user=self.other_user, total_amount=50.00)
        self._auth(self.user)
        resp = self.client.get(reverse('order-detail', kwargs={'pk': order.pk}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
