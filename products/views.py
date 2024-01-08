from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
from .models import Product, Category

# Create your views here.

def all_products(request):
    """ A view to show all products, including sorting and search queries """
    
    products = Product.objects.all()
    query = None  # to prevent error if no search term is entered
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort'] # this is the name of the field we want to sort on
            sort = sortkey # this is used to keep the sort term in the search box after the search is performed
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name')) # annotate current list of products with a new field called lower_name which is the name field converted to lower case
            if sortkey == 'category':
                    sortkey = 'category__name'
            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}' # the - in front of the sortkey reverses the order of the sort

            products = products.order_by(sortkey) # sort the products by the sortkey

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories) # __in is a Django field lookup that allows us to check if a given item is in a list
            categories = Category.objects.filter(name__in=categories) # this is used to display the category name in the search box after the search is performed
        
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
            
    current_sorting = f'{sort}_{direction}' 

    context = {
        'products': products,
        # this is used to keep the search term in the search box after the search is performed
        'search_term': query,
        'current_categories': categories, # this is used to display the category name in the search box after the search is performed
        'current_sorting': current_sorting,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)
