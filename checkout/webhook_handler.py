from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import UserProfile

import stripe
import json
import time


class StripeWH_Handler:
    """ Handle Stripe webhooks """

    def __init__(self, request):
        self.request = request
        # we assign the request as an attribute of the class
        # so it can be accessed from stripe events

    def _send_confirmation_email(self, order):
        """Send the user a confirmation email"""
        cust_email = order.email
        subject = render_to_string(
            'checkout/confirmation_emails/confirmation_email_subject.txt',
            {'order': order})
        body = render_to_string(
            'checkout/confirmation_emails/confirmation_email_body.txt',
            {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [cust_email]
        )

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f'Unhandled Webhook received: {event["type"]}',
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook from Stripe
        """
        # we get the payment intent object from the event data
        intent = event.data.object
        pid = intent.id
        bag = intent.metadata.bag  # we get the bag from the metadata
        save_info = intent.metadata.save_info  # we get the save info from the metadata # noqa

        # Get the Charge object from the payment intent
        stripe_charge = stripe.Charge.retrieve(intent.latest_charge)

        # we then get the billing details from the payment intent object
        billing_details = stripe_charge.billing_details
        # we get the shipping details from the payment intent object
        shipping_details = intent.shipping
        # we convert the total to an integer
        grand_total = round(stripe_charge.amount / 100, 2)

        # Clean data in the shipping details
        for field, value in shipping_details.address.items():
            # we check if the value is empty
            if value == "":
                # if it is, we set the value to none
                shipping_details.address[field] = None

        # Update profile information if save_info was checked
        profile = None  # we set the profile to none for anonymous users
        username = intent.metadata.username  # we get the username from the metadata # noqa
        if username != 'AnonymousUser':
            # if the user is not anonymous, we get the profile
            profile = UserProfile.objects.get(user__username=username)
            # we check if the save info was checked
            if save_info:
                # if it was, we update the profile information
                profile.default_phone_number = shipping_details.phone
                profile.default_country = shipping_details.address.country
                profile.default_postcode = shipping_details.address.postal_code
                profile.default_town_or_city = shipping_details.address.city
                profile.default_street_address1 = shipping_details.address.line1 # noqa
                profile.default_street_address2 = shipping_details.address.line2 # noqa
                profile.default_county = shipping_details.address.state
                profile.save()

        order_exists = False  # we set the order exists variable to false
        attempt = 1  # we set the attempt variable to 1
        while attempt <= 5:  # as long as the attempt is <=5
            try:
                # we try to get the order using the information in the payment
                # iexact lookup field to get exact match but case insensitive
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    email__iexact=billing_details.email,
                    phone_number__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    postcode__iexact=shipping_details.address.postal_code,
                    town_or_city__iexact=shipping_details.address.city,
                    street_address1__iexact=shipping_details.address.line1,
                    street_address2__iexact=shipping_details.address.line2,
                    county__iexact=shipping_details.address.state,
                    grand_total=grand_total,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                # we check if the order exists
                order_exists = True
                # if it does, we break out of the loop
                break
            except Order.DoesNotExist:
                # if the order does not exist, we create a delay
                # for 1 second
                # and increment the attempt variable
                attempt += 1
                time.sleep(1)
        if order_exists:
            # if the order exists, we send a confirmation email
            self._send_confirmation_email(order)
            # if it does, we return a HTTP response object indicating it that
            # the order already exists
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | SUCCESS: \
                    Verified order already in database',
                status=200)
        else:
            order = None
            # if the order does not exist, we try to create the order
            try:
                order = Order.objects.create(
                    # we create the order using the information in the payment
                    # intent
                    full_name=shipping_details.name,
                    user_profile=profile,
                    email=billing_details.email,
                    phone_number=shipping_details.phone,
                    country=shipping_details.address.country,
                    postcode=shipping_details.address.postal_code,
                    town_or_city=shipping_details.address.city,
                    street_address1=shipping_details.address.line1,
                    street_address2=shipping_details.address.line2,
                    county=shipping_details.address.state,
                    # we set the grand total to 0 as it will be updated
                    # later
                    grand_total=0,
                    original_bag=bag,
                    # we set the stripe pid to the payment intent id
                    stripe_pid=pid,
                )
                for item_id, item_data in json.loads(bag).items():
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
            except Exception as e:
                # if there is an error, we delete the order if it exists
                if order:
                    order.delete()
                return HttpResponse(
                    content=f'Webhook received: {event["type"]} | ERROR: {e}',
                            status=500)
        # we send a confirmation email if cuaght by webhook
        self._send_confirmation_email(order)
        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS: Created \
                order in webhook',
            status=200)

    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        # we return an HTTP response object indicating it was received
        # successfully
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
