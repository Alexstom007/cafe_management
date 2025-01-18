from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class MenuItem(models.Model):
    """
    Модель для представления блюда в меню.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=('Название блюда'),)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=('Стоимость'),
        validators=[MinValueValidator(Decimal('0.00'))])

    def __str__(self):
        return f"{self.name} - {self.price} руб."


class Order(models.Model):
    """
    Модель для представления заказа.
    """
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('ready', 'Готово'),
        ('paid', 'Оплачено'),
    ]
    table_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=('Номер стола'),)
    items = models.ManyToManyField(
        MenuItem,
        related_name='orders',
        through='OrderItem',
        verbose_name=('Блюда стола'),)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=('Сумма стола'),
        validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name=('Статус стола'),
        default='pending')

    def save(self, *args, **kwargs):
        """
        Сохраняет заказ и обновляет общую стоимость.
        """
        created = not self.pk
        super().save(*args, **kwargs)
        if not created and hasattr(self, 'orderitem_set'):
            self.total_price = sum(
                order_item.menu_item.price * order_item.quantity
                for order_item in self.orderitem_set.all())
            super().save(*args, **kwargs)

    def __str__(self):
        return (f'Order #{self.id} - Table {self.table_number} - '
                f'{self.get_status_display()} - ${self.total_price}')


class OrderItem(models.Model):
    """
    Модель для представления элемента заказа.
    """
    order = models.ForeignKey(
          Order,
          on_delete=models.CASCADE)
    menu_item = models.ForeignKey(
          MenuItem,
          on_delete=models.CASCADE,
          verbose_name=('Блюдо со стоимостью'),)
    quantity = models.PositiveIntegerField(
          default=1,
          verbose_name=('Колличество'),)

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"
