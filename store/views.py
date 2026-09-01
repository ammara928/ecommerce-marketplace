
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Product, OrderItem, Review
from .forms import ReviewForm
from django.http import JsonResponse
from .models import *
from .utils import cookieCart, cartData, guestOrder
from .models import Customer, Order, ShippingAddress    
import json
import datetime
from decimal import Decimal

def signupPage(request):

    if request.user.is_authenticated:                
        return redirect('store')

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                'Username already exists!'
            )

            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Customer.objects.create(
            user=user,
            name=username,
            email=email
        )

        messages.success(
            request,
            'Account created successfully! Please login.'
        )

        return redirect('login')

    return render(request, 'store/signup.html')

def loginPage(request):

    if request.user.is_authenticated:
        return redirect('store')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.username}!'
            )

            return redirect('store')

        else:

            messages.error(
                request,
                'Username or password is incorrect!'
            )

    return render(request, 'store/login.html')

def logoutUser(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('store')

@login_required
def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    customer = request.user.customer

    orders = Order.objects.filter(
        customer=customer,
        complete=True
    ).order_by('-date_ordered')

    total_orders = orders.count()

    total_spent = sum(
        order.get_cart_total
        for order in orders
    )

    purchased_items = OrderItem.objects.filter(
        order__customer=customer,
        order__complete=True
    ).select_related('product', 'order')

    context = {
        'customer': customer,
        'orders': orders,
        'purchased_items': purchased_items,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }

    return render(
        request,
        'store/dashboard.html',
        context
    )
def store(request):

	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)



def cart(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)
 

def checkout(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)


def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
    if request.method != 'POST':
        return JsonResponse({
            'error': 'Invalid request method'
        }, status=400)

    try:
        data = json.loads(request.body)

        # ==========================================
        # GET TOTAL FROM FRONTEND
        # ==========================================

        total = Decimal(str(data.get('total', '0')))

        print("Frontend total:", total)

        # ==========================================
        # LOGGED-IN USER
        # ==========================================

        if request.user.is_authenticated:

            customer = request.user.customer

            order = Order.objects.filter(
                customer=customer,
                complete=False
            ).order_by('-date_ordered').first()

            if not order:
                return JsonResponse({
                    'error': 'No active order found'
                }, status=400)

        # ==========================================
        # GUEST USER
        # ==========================================

        else:

            form_data = data.get('form', {})

            name = form_data.get('name', '').strip()
            email = form_data.get('email', '').strip()

            if not name or not email:
                return JsonResponse({
                    'error': 'Name and email are required'
                }, status=400)

            # Create guest customer
            customer = Customer.objects.create(
                name=name,
                email=email
            )

            # Create order
            order = Order.objects.create(
                customer=customer,
                complete=False
            )

            # ======================================
            # GET PRODUCTS FROM COOKIE CART
            # ======================================

            try:
                cart = json.loads(request.COOKIES.get('cart', '{}'))
            except:
                cart = {}

            # ======================================
            # CREATE ORDER ITEMS
            # ======================================

            for product_id, item_data in cart.items():

                try:
                    product = Product.objects.get(id=product_id)

                    quantity = int(item_data.get('quantity', 0))

                    if quantity > 0:

                        OrderItem.objects.create(
                            product=product,
                            order=order,
                            quantity=quantity
                        )

                except Product.DoesNotExist:
                    pass

        # ==========================================
        # CALCULATE DATABASE TOTAL
        # ==========================================

        order_total = Decimal(str(order.get_cart_total))

        print("Database total:", order_total)

        # ==========================================
        # CHECK TOTAL
        # ==========================================

        if total != order_total:

            return JsonResponse({
                'error': 'Total does not match',
                'frontend_total': str(total),
                'database_total': str(order_total)
            }, status=400)

        # ==========================================
        # SHIPPING ADDRESS
        # ==========================================

        if order.shipping:

            shipping = data.get('shipping', {})

            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=shipping.get('address', ''),
                city=shipping.get('city', ''),
                state=shipping.get('state', ''),
                zipcode=shipping.get('zipcode', ''),
                country=shipping.get('country', '')
            )

        # ==========================================
        # COMPLETE ORDER
        # ==========================================

        order.complete = True
        order.transaction_id = str(
            datetime.datetime.now().timestamp()
        )
        order.save()

        # ==========================================
        # SUCCESS
        # ==========================================

        return JsonResponse({
            'success': True,
            'message': 'Order completed successfully!'
        })

    except Exception as e:

        print("PROCESS ORDER ERROR:", str(e))

        return JsonResponse({
            'error': str(e)
        }, status=400)

def orderSuccess(request): 
      return render(request, 'store/order_success.html')


def productDetail(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    reviews = product.reviews.all().order_by('-created_at')

    can_review = False

    if request.user.is_authenticated:

        customer = request.user.customer

        can_review = OrderItem.objects.filter(
            order__customer=customer,
            order__complete=True,
            product=product
        ).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'can_review': can_review,
    }

    return render(request, 'store/product_detail.html', context)
@login_required
def addReview(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    customer = request.user.customer

    # Check if customer purchased this product
    has_purchased = OrderItem.objects.filter(
        order__customer=customer,
        order__complete=True,
        product=product
    ).exists()

    if not has_purchased:

        messages.error(
            request,
            "You can only review products you have purchased."
        )

        return redirect(
            'product_detail',
            product_id=product.id
        )

    # Get existing review if it exists
    review = Review.objects.filter(
        product=product,
        customer=customer
    ).first()

    if request.method == 'POST':

        form = ReviewForm(
            request.POST,
            instance=review
        )

        if form.is_valid():

            review = form.save(commit=False)

            review.product = product
            review.customer = customer

            review.save()

            messages.success(
                request,
                "Your review has been submitted successfully!"
            )

            return redirect(
                'product_detail',
                product_id=product.id
            )

    else:

        form = ReviewForm(instance=review)

    return render(
        request,
        'store/add_review.html',
        {
            'form': form,
            'product': product,
        }
    )

