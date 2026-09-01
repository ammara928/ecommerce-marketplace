from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

	path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),
    path('order-success/', views.orderSuccess, name='order-success'),

        # Authentication
    path('login/', views.loginPage, name='login'),
    path('signup/', views.signupPage, name='signup'),
    path('logout/', views.logoutUser, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('product/<int:product_id>/',   views.productDetail,  name='product_detail'),

    path('product/<int:product_id>/review/', views.addReview,  name='add_review'),
]