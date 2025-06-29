from store.models import Cart


def cart_item_count_processor(request):
    count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        count = cart.get_total_items()
    return {'cart_item_count': count}
