from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_products, name='products'), # this is the url for the products page
    path('<product_id>/', views.product_detail, name='product_detail'), # <product_id> is a variable that will be passed to the view as a parameter and may need int before the produc_id to convert it to an integer
]
