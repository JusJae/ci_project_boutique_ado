from django.shortcuts import render, redirect

# Create your views here.

def view_bag(request):
    """ A view that displays the shopping bag contents page """

    return render(request, 'bag/bag.html')

def add_to_bag(request, item_id):
    """ Add a quantity of the specified product to the shopping bag """

    quantity = int(request.POST.get('quantity'))
    redirect_url = request.POST.get('redirect_url')
    # below gets the bag variable from the session, or create a new one in an empty dict if it doesn't exist
    bag = request.session.get('bag', {})
    # If the item is already in the bag, update the quantity
    if item_id in list(bag.keys()):
        bag[item_id] += quantity
    # Otherwise, add the item to the bag
    else:
        bag[item_id] = quantity
    # Overwrite the bag variable in the session with the updated version
    request.session['bag'] = bag
    print(request.session['bag'])
    return redirect(redirect_url)
