from django.shortcuts import render
from .models import PromoBanner, FeaturedSection,Service,Testimonial,ParentCategory

# Pages that extend base.html
# def home(request):
#     banner = PromoBanner.objects.first()
#     categories = ParentCategory.objects.all()
#     featured = FeaturedSection.objects.all()
#     services = Service.objects.all()
#     testimonials = Testimonial.objects.all()   # 👈 Add this

#     return render(request, 'core/home.html', {
#         'categories': categories,
#         'banner': banner,
#         'featured': featured,
#         'services': services,
#         'testimonials': testimonials   # 👈 Pass to template
#     })      
   
# core/views.py (home view)
from django.shortcuts import render
from .models import PromoBanner, FeaturedSection, Service, Testimonial, ParentCategory, Product
# ParentCategoryAssignment is accessed via related_name 'assignments' on ParentCategory

def home(request):
    banner = PromoBanner.objects.first()
    featured = FeaturedSection.objects.all()
    services = Service.objects.all()
    testimonials = Testimonial.objects.all()

    # load parent categories and attach subcategories + preview products
    parents = ParentCategory.objects.all().prefetch_related(
        "assignments__category__products"   # follow mapping -> productcategory -> products
    )

    # Build preview_products for each parent (first 3 newest products across its subcategories)
    parents_with_preview = []
    for parent in parents:
        # get productcategory objects assigned to this parent
        assigned_cats = [a.category for a in parent.assignments.all()]

        # if there are assigned subcategories, collect their products
        if assigned_cats:
            # order by newest (adjust ordering as you like)
            products_qs = Product.objects.filter(category__in=assigned_cats).order_by("-id")
            preview_products = products_qs[:3]
        else:
            preview_products = Product.objects.none()

        # attach attribute for template convenience
        parent.preview_products = preview_products
        parents_with_preview.append(parent)

    return render(request, 'core/home.html', {
        'categories': parents_with_preview,   # still called categories in template
        'banner': banner,
        'featured': featured,
        'services': services,
        'testimonials': testimonials,
    })



# login/signup/logout
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

User = get_user_model()

def _letters_spaces_only(s: str) -> bool:
    import re
    return bool(re.fullmatch(r"[A-Za-z ]+", s or ""))

def _valid_email(s: str) -> bool:
    import re
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]{2,}", s or ""))

def _valid_password(s: str) -> bool:
    # min 6, at least 1 letter and 1 number
    import re
    return bool(re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d).{6,}", s or ""))

def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        remember = request.POST.get("remember") == "on"

        # Does user exist?
        try:
            User.objects.get(username__iexact=username)
            user_exists = True
        except User.DoesNotExist:
            user_exists = False

        if not user_exists:
            messages.error(request, "No user found with that username. Please sign up.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect("login")

        login(request, user)
        if not remember:
            request.session.set_expiry(0)  # session ends on browser close
        messages.success(request, "Welcome back!")
        return redirect("home")

    return render(request, "auth/login.html")

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        last_name  = (request.POST.get("last_name") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        username   = (request.POST.get("username") or "").strip()
        password   = (request.POST.get("password") or "").strip()
        terms      = request.POST.get("terms") == "on"

        # client-like strict checks server-side too
        if not _letters_spaces_only(first_name) or not _letters_spaces_only(last_name):
            messages.error(request, "Name should contain only letters and spaces.")
            return redirect("signup")

        if not _valid_email(email):
            messages.error(request, "Please enter a valid email address.")
            return redirect("signup")

        if not _valid_password(password):
            messages.error(request, "Password must be 6+ chars with at least one letter and one number.")
            return redirect("signup")

        if not terms:
            messages.error(request, "You must agree to the terms & conditions.")
            return redirect("signup")

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists. Try a different one or log in.")
            return redirect("signup")
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already registered. Try logging in.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        messages.success(request, "Account created! You can log in now.")
        return redirect("login")

    return render(request, "auth/signup.html")

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")

# about page 
from django.shortcuts import render
from .models import AboutPage

def about_view(request):
    about = AboutPage.objects.first()   # Only one record needed
    return render(request, "core/about.html", {"about": about})

# contact page
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .models import ContactPage
from .forms import ContactForm

def contact_view(request):
    contact = ContactPage.objects.first()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            phone = form.cleaned_data["phone"]
            how_find = form.cleaned_data["how_find"]
            message = form.cleaned_data["message"]

            # Send email
            subject = f"New Contact from {name}"
            body = f"""
            Name: {name}
            Email: {email}
            Phone: {phone}
            Found Us By: {how_find}
            Message: {message}
            """
            send_mail(subject, body, "yourgmail@gmail.com", ["info@mailjewellery.com"])

            messages.success(request, "Our team will contact you shortly. We received your message!")
            return redirect("contact")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()

    return render(request, "core/contact.html", {"contact": contact, "form": form})

# products
from django.shortcuts import render, get_object_or_404
from .models import ProductCategory, Product

# Show all categories


# Show products under a category
from django.core.paginator import Paginator

def category_products(request, slug):
    category = get_object_or_404(ProductCategory, slug=slug)
    products_list = category.products.all()  
    banner = getattr(category, "banner", None)

    paginator = Paginator(products_list, 12)  # show 12 products per page
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    return render(request, "core/product_detail.html", {
        "category": category,
        "products": products,
        "banner": banner,
    })



# parent has categories
from django.shortcuts import render, get_object_or_404
from .models import ParentCategory

def parent_category_view(request, slug):
    # get the ParentCategory (e.g. Electronics)
    parent = get_object_or_404(ParentCategory, slug=slug)

    # get assigned subcategories via the mapping (ParentCategoryAssignment)
    # using related_name 'assignments' from earlier model suggestion
    assignments = parent.assignments.filter(is_active=True).select_related('category').order_by('order')
    subcategories = [a.category for a in assignments]

    return render(request, "core/parent_category.html", {
        "parent": parent,
        "subcategories": subcategories,
    })

from django.shortcuts import render, get_object_or_404

# def product_detail(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     cart = request.session.get('cart', {})

#     total = sum(item['price'] * item['qty'] for item in cart.values())
#     quantity_in_cart = cart.get(str(pk), {}).get('qty', 1)  # default 1 if not in cart

#     context = {
#         "product": product,
#         "cart": cart,
#         "total": total,
#         "quantity_in_cart": quantity_in_cart
#     }
#     return render(request, "core/product_description.html", context)

# recommendation included
from django.shortcuts import render, get_object_or_404
from .models import Product, ProductRecommendation, UserProductInteraction
from django.contrib import messages

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Ensure session exists (for anonymous logging)
    if not request.session.session_key:
        request.session.create()

    # Log view interaction (non-blocking)
    try:
        UserProductInteraction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            product=product,
            event="view",
            weight=1
        )
    except Exception:
        pass

    # Get recommended ids from ProductRecommendation (if exists)
    recommended = []
    also_bought = []
    try:
        pr = getattr(product, "recommendation", None)
        if pr and pr.recommended_ids:
            rec_ids = pr.recommended_ids  # list from JSONField
            # maintain order of rec_ids
            preserved = {id_: index for index, id_ in enumerate(rec_ids)}
            qs = Product.objects.filter(id__in=rec_ids)
            # convert to list ordered by preserved
            recommended = sorted(qs, key=lambda x: preserved.get(x.id, 999))

        # NEW: also_bought from separate field (keeps signals separate)
        if pr and getattr(pr, "also_bought_ids", None):
            ab_ids = pr.also_bought_ids
            preserved_ab = {id_: index for index, id_ in enumerate(ab_ids)}
            qs_ab = Product.objects.filter(id__in=ab_ids)
            also_bought = sorted(qs_ab, key=lambda x: preserved_ab.get(x.id, 999))
    except Exception:
        recommended = []
        also_bought = []

    # cart snapshot & quantity (as before)
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['qty'] for item in cart.values())
    quantity_in_cart = cart.get(str(pk), {}).get('qty', 1)

    context = {
        "product": product,
        "cart": cart,
        "total": total,
        "quantity_in_cart": quantity_in_cart,
        "recommended": recommended,
        "also_bought": also_bought,   # <- added to context
    }
    return render(request, "core/product_description.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Product

# @login_required
# def book_now(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     cart = request.session.get('cart', {})

#     if request.method == "POST":
#         qty = int(request.POST.get('qty', 1))

#         # Instead of incrementing, overwrite with chosen qty
#         cart[str(pk)] = {
#             'name': product.name,
#             'price': float(product.price_per_day),
#             'image': product.image.url if product.image else '',
#             'qty': qty
#         }

#         request.session['cart'] = cart
#         request.session.modified = True

#         # Redirect back to product detail page
#         return redirect('product_detail', pk=pk)

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from core.models import Product

@login_required
def book_now(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Only accept POST for adding to cart
    if request.method != "POST":
        return redirect('product_detail', pk=pk)

    # Parse qty robustly
    try:
        qty = int(request.POST.get('qty', 1))
    except (ValueError, TypeError):
        qty = 1
    if qty < 1:
        qty = 1

    cart = request.session.get('cart', {})
    pid = str(pk)

    # Safe image URL
    img_url = ""
    try:
        if product.image and hasattr(product.image, "url"):
            img_url = product.image.url
    except Exception:
        img_url = ""

    # If already in cart -> increment qty, otherwise add
    if pid in cart:
        try:
            existing_qty = int(cart[pid].get('qty', 0))
        except (ValueError, TypeError):
            existing_qty = 0
        cart[pid]['qty'] = existing_qty + qty
    else:
        cart[pid] = {
            'name': product.name,
            'price': float(product.price_per_day),
            'image': img_url,
            'qty': qty,
            'category': product.category.name if product.category else ""
        }

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"Added {qty} × {product.name} to cart.")
    return redirect('product_detail', pk=pk)


#     return redirect('product_detail', pk=pk)
# from django.views.decorators.http import require_POST
# @require_POST
# def book_now(request, product_id):
#     """
#     Simple session-based cart add. Works for any Product.
#     Adds or updates item qty in request.session['cart']:
#       cart = {
#         "<product_id>": {"qty": 2, "price": "1200.00", "name": "Product name"},
#         ...
#       }
#     """

#     # 1) fetch product
#     product = get_object_or_404(Product, pk=product_id)

#     # 2) qty from POST (fallback to 1)
#     try:
#         qty = int(request.POST.get("qty", 1))
#         if qty < 1:
#             qty = 1
#     except (ValueError, TypeError):
#         qty = 1

#     # 3) session cart
#     cart = request.session.get("cart", {})

#     pid = str(product.id)
#     # update if exists else add
#     if pid in cart:
#         cart[pid]["qty"] = cart[pid].get("qty", 0) + qty
#     else:
#         cart[pid] = {
#             "qty": qty,
#             "price": str(product.price_per_day),
#             "name": product.name,
#             "category": product.category.name if product.category else "",
#         }

#     request.session["cart"] = cart
#     request.session.modified = True

#     messages.success(request, f"Added {qty} × {product.name} to cart.")
#     # redirect back to product page or cart page
#     return redirect(request.META.get("HTTP_REFERER", reverse("cart_view")))




# rental page
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, ProductCategory

from django.db.models import Q

def rental_page(request):
    products = Product.objects.all().order_by('-id')
    categories = ProductCategory.objects.all()

    category = request.GET.get('category')
    material = request.GET.get('material')
    price = request.GET.get('price')
    gender = request.GET.get('gender')

    if category and category.lower() != "all":
        products = products.filter(category__name__iexact=category)

    if material:
        products = products.filter(Q(metal__icontains=material) | Q(short_description__icontains=material))

    if price:
        if price == "2000":
            products = products.filter(price_per_day__lt=2000)
        elif price == "4000":
            products = products.filter(price_per_day__gte=2000, price_per_day__lte=6000)
        elif price == "6000":
            products = products.filter(price_per_day__gt=6000)

    if gender:
        products = products.filter(gender__iexact=gender)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/rental.html', {
        'products': page_obj,
        'categories': categories,
        'selected_category': category,
        'selected_material': material,
        'selected_price': price,
        'selected_gender': gender,
    })

# whislist page 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product

# Add to Wishlist
# def add_to_wishlist(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     wishlist = request.session.get('wishlist', [])

#     if pk not in wishlist:
#         wishlist.append(pk)
#         request.session['wishlist'] = wishlist
#         messages.success(request, f"{product.name} added to Wishlist!")
#     else:
#         messages.info(request, f"{product.name} is already in Wishlist!")

#     # Redirect to wishlist after adding
#     return redirect('wishlist')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, UserProductInteraction

def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Ensure session exists (required for logging)
    if not request.session.session_key:
        request.session.create()

    # Get wishlist from session
    wishlist = request.session.get("wishlist", [])

    # Add product to wishlist
    if pk not in wishlist:
        wishlist.append(pk)
        request.session["wishlist"] = wishlist
        messages.success(request, f"{product.name} added to your wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")

    # ---------- Log Interaction (for Recommendation Engine) ----------
    try:
        UserProductInteraction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            product=product,
            event="wishlist",   # event type
            weight=2            # wishlist is stronger than view
        )
    except Exception:
        pass  # don't break page if logging fails

    # ---------- Track recent wishlist actions ----------
    recent_wishlist = request.session.get("recent_wishlist", [])
    if pk in recent_wishlist:
        recent_wishlist.remove(pk)
    recent_wishlist.append(pk)
    request.session["recent_wishlist"] = recent_wishlist[-10:]  # store last 10

    # Redirect back to same page
    return redirect('wishlist')



# Wishlist Page
def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids)
    return render(request, 'core/wishlist.html', {'products': products})


# Remove All
def clear_wishlist(request):
    request.session['wishlist'] = []
    messages.success(request, "Wishlist cleared!")
    return redirect('wishlist')


# cart logics
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product

# Add to cart
# @login_required
# def add_to_cart(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     cart = request.session.get('cart', {})

#     if str(pk) in cart:
#         cart[str(pk)]['qty'] += 1
#     else:
#         cart[str(pk)] = {
#             'name': product.name,
#             'price': float(product.price_per_day),
#             'image': product.image.url if product.image else '',
#             'qty': 1
#         }

#     request.session['cart'] = cart
#     messages.success(request, f"{product.name} added to cart!")
#     return redirect('cart_view')

# @login_required
# def add_to_cart(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     cart = request.session.get('cart', {})

#     if str(pk) in cart:
#         cart[str(pk)]['qty'] += 1
#     else:
#         cart[str(pk)] = {
#             'name': product.name,
#             'price': float(product.price_per_day),
#             'image': product.image.url if product.image else '',
#             'qty': 1
#         }

#     request.session['cart'] = cart

#     # Instead of redirecting to cart page, stay on same page
#     referer = request.META.get('HTTP_REFERER', 'home')  
#     return redirect(referer)

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Product, UserProductInteraction

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    cart = request.session.get('cart', {})

    # Add product to cart
    if str(pk) in cart:
        cart[str(pk)]['qty'] += 1
    else:
        cart[str(pk)] = {
            'name': product.name,
            'price': float(product.price_per_day),
            'image': product.image.url if product.image else '',
            'qty': 1
        }

    request.session['cart'] = cart

    # Show message
    messages.success(request, f"{product.name} added to cart!")

    # ----------- Log Interaction for Recommendation Engine -----------
    try:
        UserProductInteraction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            product=product,
            event="cart",   # cart interaction
            weight=3        # cart actions are strong signals
        )
    except Exception:
        pass  # don’t break flow if logging fails

    # ----------- Save recent cart interactions -----------
    recent_cart = request.session.get("recent_cart", [])
    if pk in recent_cart:
        recent_cart.remove(pk)

    recent_cart.append(pk)
    request.session["recent_cart"] = recent_cart[-10:]   # limit to last 10

    # Redirect back to same page
    return redirect(request.META.get("HTTP_REFERER", "home"))

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def orders(request):
    # Example: fetch cart or order details from session/db
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['qty'] for item in cart.values())

    context = {
        "cart": cart,
        "total": total,
    }
    request.session['cart'] = {}
    request.session.modified = True
    return render(request, "core/orders.html", context)

# View Cart
@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['qty'] for item in cart.values())
    tax = total * 0.1
    grand_total = total + tax

    return render(request, 'core/cart.html', {
        'cart': cart,
        'total': total,
        'tax': tax,
        'grand_total': grand_total
    })


# Update quantity
@login_required
def update_cart(request, pk, action):
    cart = request.session.get('cart', {})

    if str(pk) in cart:
        if action == "increase":
            cart[str(pk)]['qty'] += 1
        elif action == "decrease":
            if cart[str(pk)]['qty'] > 1:
                cart[str(pk)]['qty'] -= 1
        elif action == "remove":
            del cart[str(pk)]

    request.session['cart'] = cart
    return redirect('cart_view')


# checkout
# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def checkout(request):
    if request.method == "POST":
        fname = request.POST.get("fname")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        if not fname or not email or not phone or not address:
            messages.error(request, "Please fill all required fields correctly.")
            return redirect("checkout")

        # ✅ Save order later here
        messages.success(request, "✅ Order placed successfully!")
        return redirect("home")

    # cart_total, cart_items, cart_count come from context processor automatically
    return render(request, "core/checkout.html")
