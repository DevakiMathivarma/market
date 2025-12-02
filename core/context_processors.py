def cart_context(request):
    cart = request.session.get('cart', {})
    total_items = sum(item['qty'] for item in cart.values()) if cart else 0
    total_price = sum(item['price'] * item['qty'] for item in cart.values()) if cart else 0
    
    return {
        "cart_items": cart,
        "cart_count": total_items,
        "cart_total": total_price
    }
