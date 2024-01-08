from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from .models import Product

# Create your views here.

def all_products(request):
    """ A view to show all products, including sorting and search queries """
    
    products = Product.objects.all()
    query = None  # to prevent error if no search term is entered

    if request.GET:
        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(
                    request, "You didn't enter any search criteria!")
                return redirect(reverse('products'))

            # Q is a complex query that allows us to use the OR operator (|) to build a query that matches on either name or description
            queries = Q(name__icontains=query) | Q(
                description__icontains=query)
            # filter the products queryset to match the queries
            products = products.filter(queries)

    context = {
        'products': products,
        # this is used to keep the search term in the search box after the search is performed
        'search_term': query,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)
