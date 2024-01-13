from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import OrderLineItem


@receiver(post_save, sender=OrderLineItem)
# The receiver decorator is used to register the signal and
# the sender argument is used to specify the model which
# sends the signal.
def update_on_save(sender, instance, created, **kwargs):
    """ Update order total on lineitem update/create """
    # This function will be triggered whenever a
    # save event occurs on an OrderLineItem instance.
    # Post_save is the signal and the receiver is the
    # update_on_save function itself.
    # The sender is the OrderLineItem model and the
    # instance is the actual instance being saved.
    # The created argument is a boolean which is true
    # if a new object was created and false if an
    # existing object was updated.
    instance.order.update_total()


@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance, **kwargs):
    """ Update order total on lineitem delete """
    # This function will be triggered whenever a
    # delete event occurs on an OrderLineItem instance.
    # Post_delete is the signal and the receiver is the
    # update_on_delete function itself.
    # The sender is the OrderLineItem model and the
    # instance is the actual instance being deleted.
    instance.order.update_total()
