from django.shortcuts import (
    render, redirect, reverse, get_object_or_404, HttpResponse)
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings

from .forms import OrderForm
from .models import Order, OrderLineItem

from products.models import Product
from profiles.models import UserProfile
from profiles.forms import UserProfileForm
from bag.contexts import bag_contents
# this is the context processor we created in the bag app that
# returns a dictionary of the bag contents

import stripe
import json


@require_POST
def cache_checkout_data(request):
    """ A view to cache the checkout data """
    try:
        # we get the payment intent id from the post data
        pid = request.POST.get('client_secret').split('_secret')[0]
        # we set the stripe api key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        # we update the payment intent with the form data
        stripe.PaymentIntent.modify(pid, metadata={
            'bag': json.dumps(request.session.get('bag', {})),
            # we add the bag to the metadata in a json format
            'save_info': request.POST.get('save_info'),
            # we add the save info to the metadata
            'username': request.user,
            # we add the username to the metadata
        })
        return HttpResponse(status=200)
    except Exception as e:
        # if there is an error, we display a message to the user
        messages.error(request, 'Sorry, your payment cannot be processed right now. Please try again later.')  # noqa
        # we return a HTTP response with a 400 error
        return HttpResponse(content=str(e), status=400)


def checkout(request):
    """ A view to return the checkout page """

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    # if the request method is POST, then the form has been submitted
    # and we can process the data
    if request.method == 'POST':
        bag = request.session.get('bag', {})

        form_data = {
            # the form data is the same as the order model fields
            # so we can just use the request.POST data
            'full_name': request.POST['full_name'],
            'email': request.POST['email'],
            'phone_number': request.POST['phone_number'],
            # we don't need to pass the address line 1 and 2 as they
            # are not in the form, but we can get them from the bag
            # contents context processor
            'country': request.POST['country'],
            'postcode': request.POST['postcode'],
            'town_or_city': request.POST['town_or_city'],
            'street_address1': request.POST['street_address1'],
            'street_address2': request.POST['street_address2'],
            # we don't need to pass the county as it is not in the form,
            # but we can get it from the bag contents context processor
            'county': request.POST['county'],
        }
        order_form = OrderForm(form_data)
        # we pass the form data to the order form so that it can be
        # validated and saved
        if order_form.is_valid():
            # if the form is valid, we save the order
            # we add commit=False to prevent multiple saves on db
            order = order_form.save(commit=False)
            # we get the payment intent id from the post data
            pid = request.POST.get('client_secret').split('_secret')[0]
            # we set the order stripe pid to the payment intent id
            order.stripe_pid = pid
            # we set the original bag to the bag in the session
            order.original_bag = json.dumps(bag)
            # we save the order
            order.save()
            # we loop through the bag items and create an order line item
            # for each one
            for item_id, item_data in bag.items():
                try:
                    # we get the product id from the bag
                    product = Product.objects.get(id=item_id)
                    # if the item has no size, we set the size to none
                    if isinstance(item_data, int):
                        order_line_item = OrderLineItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_line_item.save()
                    # if the item has a size, we set the size to the item
                    # data
                    else:
                        for size, quantity in item_data['items_by_size'].items(): # noqa
                            order_line_item = OrderLineItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size,
                            )
                            order_line_item.save()
                # if there is an error, we display a message to the user
                except Product.DoesNotExist:
                    messages.error(request, (
                        "One of the products in your bag wasn't"
                        "found in our database. "
                        "Please call us for assistance!"
                    ))
                    # we delete the order if there is an error
                    order.delete()
                    # we redirect the user to the bag page
                    return redirect(reverse('view_bag'))

            # we save the user's info to their profile if they are logged in
            request.session['save_info'] = 'save-info' in request.POST
            # we redirect the user to the checkout success page
            return redirect(reverse('checkout_success',
                                    args=[order.order_number]))
        # if the form is not valid, we display a message to the user
        else:
            messages.error(request, 'There was an error with your form. Please double check your information.')  # noqa
    else:
        bag = request.session.get('bag', {})
        if not bag:
            messages.error(request, "There's nothing in your bag right now")
            return redirect(reverse('products'))

        current_bag = bag_contents(request)
        total = current_bag['grand_total']
        stripe_total = round(total * 100)
        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )

        # Attempt to prefill the form with any info the user maintains in
        # their profile
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                order_form = OrderForm(initial={
                    'full_name': profile.user.get_full_name(),
                    'email': profile.user.email,
                    'phone_number': profile.default_phone_number,
                    'country': profile.default_country,
                    'postcode': profile.default_postcode,
                    'town_or_city': profile.default_town_or_city,
                    'street_address1': profile.default_street_address1,
                    'street_address2': profile.default_street_address2,
                    'county': profile.default_county,
                })
            except UserProfile.DoesNotExist:
                order_form = OrderForm()
        else:
            order_form = OrderForm()

    if not stripe_public_key:
        messages.warning(request, 'Stripe public key is missing. Did you forget to set it in your environment?')  # noqa

    template = 'checkout/checkout.html'
    context = {
        'order_form': order_form,
        'stripe_public_key': stripe_public_key,
        'client_secret': intent.client_secret,
    }

    return render(request, template, context)


def checkout_success(request, order_number):
    """ A view to handle successful checkouts """

    # we get the save info from the session
    save_info = request.session.get('save_info') # noqa
    # we get the order from the previous view
    order = get_object_or_404(Order, order_number=order_number)

    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        # Attach the user's profile to the order
        order.user_profile = profile
        order.save()

    # Save the user's info
    if save_info:
        profile_data = {
            # we set the profile data to the order data
            'default_phone_number': order.phone_number,
            'default_country': order.country,
            'default_postcode': order.postcode,
            'default_town_or_city': order.town_or_city,
            'default_street_address1': order.street_address1,
            'default_street_address2': order.street_address2,
            'default_county': order.county,
        }
        # we create a user profile form instance with the profile data
        user_profile_form = UserProfileForm(profile_data, instance=profile)
        # we save the user profile form
        if user_profile_form.is_valid():
            user_profile_form.save()

    messages.success(request, f'Order successfully processed! Your order number is {order_number}. A confirmation email will be sent to {order.email}.')  # noqa

    # if the user has a bag in the session, we delete it
    if 'bag' in request.session:
        del request.session['bag']

    # we render the checkout success template
    template = 'checkout/checkout_success.html'
    context = {
        'order': order,
    }

    return render(request, template, context)
