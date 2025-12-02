from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("about/", views.about_view, name="about"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("contact/", views.contact_view, name="contact"),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('categories/<slug:slug>/', views.category_products, name='category_products'),
    path('parent/<slug:slug>/', views.parent_category_view, name='parent_category'), 
     path('rental/', views.rental_page, name='rental_page'),
     path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/<str:action>/', views.update_cart, name='update_cart'),
    path("checkout/", views.checkout, name="checkout"),
        path("orders/", views.orders, name="orders"),
path("product/<int:pk>/book/", views.book_now, name="book_now"),

   
]
