from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('full_name', 'email', 'phone_number',
                  'street_address1', 'street_address2',
                  'town_or_city', 'postcode', 'county',
                  'country',)

    def __init__(self, *args, **kwargs):
        """ Add placeholders and classes, remove auto-generated
            labels and set autofocus on first field """
        super().__init__(*args, **kwargs)
        # The super() method is used to give access to methods
        # and properties of a parent or sibling class.
        # In this case, we are overriding the default init
        # method and adding to it.
        # The init method is called every time a form is
        # instantiated.
        placeholders = {
            'full_name': 'Full Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'street_address1': 'Street Address 1',
            'street_address2': 'Street Address 2',
            'town_or_city': 'Town or City',
            'postcode': 'Postcode',
            'county': 'County, State or Locality',
            'country': 'Country',
        }
        # The placeholders dictionary is used to set the
        # placeholder attribute on the form fields.
        # The keys of the dictionary match the field names
        # in the underlying model.
        # The values of the dictionary are the placeholders
        # themselves.
        self.fields['full_name'].widget.attrs['autofocus'] = True
        # The autofocus attribute is set on the full_name when the form starts.
        # The code below loops through the form fields and
        # sets a class attribute on each one.
        for field in self.fields:
            if self.fields[field].required:
                # The required attribute is used to indicate
                # whether the field is required or not.
                # If the field is required, an asterisk is
                # added to the placeholder.
                placeholder = f'{placeholders[field]} *'
            else:
                placeholder = placeholders[field]
            # The placeholder is then set on the field.
            self.fields[field].widget.attrs['placeholder'] = placeholder
            # The classes are set on the field.
            self.fields[field].widget.attrs['class'] = 'stripe-style-input'
            # The label is set to False to remove the
            # auto-generated label.
            self.fields[field].label = False
