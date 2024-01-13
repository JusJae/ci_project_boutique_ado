from django.shortcuts import (
    render, redirect, reverse, HttpResponse, get_object_or_404)
from django.contrib import messages

from products.models import Product


def view_bag(request):
    """ A view that displays the shopping bag contents page """

    return render(request, 'bag/bag.html')


def add_to_bag(request, item_id):
    """ Add a quantity of the specified product to the shopping bag """

    product = Product.objects.get(pk=item_id)
    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')
    size = None
    if 'product_size' in request.POST:
        size = request.POST['product_size']
    # Gets the bag variable from the session, or create a new one in an
        # empty dict if it doesn't exist
    bag = request.session.get('bag', {})

    if size:
        # If the item is already in the bag, update the quantity
        if item_id in list(bag.keys()):
            # If the size is already in the bag, update the quantity
            if size in bag[item_id]['items_by_size'].keys():
                bag[item_id]['items_by_size'][size] += quantity
                messages.success(
                    request,
                    f'Updated size {size.upper()} {product.name} quantity to '
                    f'{bag[item_id]["items_by_size"][size]}'
                )
            # Otherwise, add the size to the bag
            else:
                bag[item_id]['items_by_size'][size] = quantity
                messages.success(request, f'Added size {size.upper()} {
                    product.name} to your bag')
        # Otherwise, add the item to the bag
        else:
            bag[item_id] = {'items_by_size': {size: quantity}}
            messages.success(request, f'Added size {size.upper()} {
                product.name} to your bag')
    else:
        # If the item is already in the bag, update the quantity
        if item_id in list(bag.keys()):
            bag[item_id] += quantity
            messages.success(request, f'Updated {
                product.name} quantity to {bag[item_id]}')
        # Otherwise, add the item to the bag
        else:
            bag[item_id] = quantity
            messages.success(request, f'Added {product.name} to your bag')

    # Overwrite the bag variable in the session with the updated version
    request.session['bag'] = bag
    return redirect(redirect_url)


def adjust_bag(request, item_id):
    """ Adjust the quantity of the specified product to the specified amount"""

    product = get_object_or_404(Product, pk=item_id)
    quantity = int(request.POST.get('quantity'))
    size = None
    if 'product_size' in request.POST:
        size = request.POST['product_size']
    bag = request.session.get('bag', {})

    if size:
        # If the quantity is greater than 0, update the quantity
        if quantity > 0:
            bag[item_id]['items_by_size'][size] = quantity
            messages.success(
                request,
                f'Updated size {size.upper()} {product.name} quantity to '
                f'{bag[item_id]["items_by_size"][size]}')
        # Otherwise, remove the item from the bag
        else:
            del bag[item_id]['items_by_size'][size]
            if not bag[item_id]['items_by_size']:
                bag.pop(item_id)  # Removes the item from the bag
                messages.success(request, f'Removed size {size.upper()} {
                    product.name} from your bag')
    else:
        if quantity > 0:
            bag[item_id] = quantity
            messages.success(request, f'Updated {
                product.name} quantity to {bag[item_id]}')
        else:
            bag.pop(item_id)  # Removes the item from the bag
            messages.success(request, f'Removed {product.name} from your bag')

    # Overwrite the bag variable in the session with the updated version
    request.session['bag'] = bag
    return redirect(reverse('view_bag'))


def remove_from_bag(request, item_id):
    """ Removes the item from the shopping bag """

    try:
        product = get_object_or_404(Product, pk=item_id)
        size = None
        if 'product_size' in request.POST:
            size = request.POST['product_size']
        bag = request.session.get('bag', {})

        if size:
            del bag[item_id]['items_by_size'][size]
            if not bag[item_id]['items_by_size']:
                bag.pop(item_id)
            messages.success(request, f'Removed size {size.upper()} {
                    product.name} from your bag')
        else:
            # Removes the item from the bag if there is no size
            bag.pop(item_id)
            messages.success(request, f'Removed {product.name} from your bag')

        request.session['bag'] = bag
        return HttpResponse(status=200)

    except Exception as e:
        messages.error(request, f'Error removing item: {e}')
        return HttpResponse(status=500)
