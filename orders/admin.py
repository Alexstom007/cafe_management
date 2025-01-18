from django.contrib import admin

from .models import Order, MenuItem, OrderItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'price')
    search_fields = (
        'name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_number', 'total_price', 'status')
    list_filter = ('status',)
    search_fields = ('id', 'table_number')
    readonly_fields = ('total_price',)
    inlines = [OrderItemInline]
