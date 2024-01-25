from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower

from .models import Product, Category
from .forms import ProductForm


def all_products(request):
    """ A view to show all products, including sorting and search queries """

    products = Product.objects.all()
    query = None  # to prevent error if no search term is entered
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']  # name of the field we want to sort
            sort = sortkey  # this is used to keep the sort term in the
            # search box after the search is performed
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))
                # annotate current list of products with a new field called
                # lower_name which is the name field converted to lower case
            if sortkey == 'category':
                sortkey = 'category__name'
            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
                    # the - in front of the sortkey reverses the sort order

            products = products.order_by(sortkey)
            # sort the products by the sortkey

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            # __in is a Django field lookup that allows us to check
            # if a given item is in a list
            categories = Category.objects.filter(name__in=categories)
            # displays the category name in the search box after the search

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(
                    request, "You didn't enter any search criteria!")
                return redirect(reverse('products'))

            # Q is a complex query that allows us to use the OR operator (|)
            # to build a query that matches on either name or description
            queries = Q(name__icontains=query) | Q(
                description__icontains=query)
            # filter the products queryset to match the queries
            products = products.filter(queries)

    current_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        # this is used to keep the search term in the
        # search box after the search is performed
        'search_term': query,
        'current_categories': categories,
        # this is used to display the category name in the
        # search box after the search is performed
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


def add_product(request):
    """ Add a product to the store """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        # request.FILES is required to handle the image file
        # that is submitted with the form
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Successfully added product!')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(
                request, 'Failed to add product. Please ensure the form is \
                    valid.')
    else:
        form = ProductForm()

    template = 'products/add_product.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


def edit_product(request, product_id):
    """ Edit a product in the store """
    product = get_object_or_404(Product, pk=product_id)
    # get the product that we want to edit
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        # pass in the product instance as the instance argument
        # to the ProductForm so that the form is pre-filled
        # with the information from the product that we want to edit
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully updated product!')
            return redirect(reverse('product_detail', args=[product.id]))
            # redirect to the product detail page for the product
        else:
            messages.error(
                request, 'Failed to update product. Please ensure the form is \
                    valid.')
    else:
        form = ProductForm(instance=product)
        # pass in the product instance as the instance argument
        # to the ProductForm so that the form is pre-filled
        # with the information from the product that we want to edit
        messages.info(request, f'You are editing {product.name}')

    template = 'products/edit_product.html'
    context = {
        'form': form,
        'product': product,
    }

    return render(request, template, context)


def delete_product(request, product_id):
    """ Delete a product from the store """
    product = get_object_or_404(Product, pk=product_id)
    # get the product that we want to delete
    product.delete()
    messages.success(request, 'Product deleted!')
    return redirect(reverse('products'))
