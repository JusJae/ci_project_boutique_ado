from django.shortcuts import render, redirect

# Create your views here.

def view_bag(request):
    """ A view that displays the shopping bag contents page """

    return render(request, 'bag/bag.html')

def add_to_bag(request, item_id):
    """ Add a quantity of the specified product to the shopping bag """

    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')
    size = None
    if 'product_size' in request.POST:
        size = request.POST['product_size']
    # Gets the bag variable from the session, or create a new one in an empty dict if it doesn't exist
    bag = request.session.get('bag', {})

    if size:
        # If the item is already in the bag, update the quantity
        if item_id in list(bag.keys()):
            # If the size is already in the bag, update the quantity
            if size in bag[item_id]['items_by_size'].keys():
                bag[item_id]['items_by_size'][size] += quantity
            # Otherwise, add the size to the bag
            else:
                bag[item_id]['items_by_size'][size] = quantity
        # Otherwise, add the item to the bag
        else:
            bag[item_id] = {'items_by_size': {size: quantity}}
    else:
        # If the item is already in the bag, update the quantity
        if item_id in list(bag.keys()):
            bag[item_id] += quantity
        # Otherwise, add the item to the bag
        else:
            bag[item_id] = quantity

    # Overwrite the bag variable in the session with the updated version
    request.session['bag'] = bag
    return redirect(redirect_url)
