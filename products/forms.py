from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'  # includes all fields from the model

    def __init__(self, *args, **kwargs):
        """ Add placeholders and classes to form inputs """
        super().__init__(*args, **kwargs)
        categories = Category.objects.all()  # get all categories
        # we create a list of tuples of the friendly names - list comprehension
        friendly_names = [(c.id, c.get_friendly_name()) for c in categories]

        # we update the category field on the form with the friendly names
        self.fields['category'].choices = friendly_names
        # we iterate through the fields in the form
        for field_name, field in self.fields.items():
            # we add a class attribute to each field
            field.widget.attrs['class'] = 'border-black rounded-0'
