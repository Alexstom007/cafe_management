from django import forms
from django.core.exceptions import ValidationError

from .models import Order, OrderItem


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table_number'].widget.attrs['placeholder'] = (
            'Введите номер стола')

    def clean_table_number(self):
        table_number = self.cleaned_data.get('table_number')
        if table_number:
            existing_orders = Order.objects.filter(
                table_number=table_number,
                status__in=['pending', 'ready'])
            if existing_orders.exists():
                raise ValidationError(
                    f'Стол {table_number} ещё не оплачен.')
        return table_number


class OrderUpdateForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['table_number', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table_number'].widget.attrs['placeholder'] = (
            'Введите номер стола'
        )
