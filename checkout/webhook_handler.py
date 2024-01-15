from django.http import HttpResponse


class StripeWH_Handler:
    """ Handle Stripe webhooks """

    def __init__(self, request):
        self.request = request
        # we assign the request as an attribute of the class
        # so it can be accessed from stripe events

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        # we return an HTTP response object indicating it was received
        # successfully
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
