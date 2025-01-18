import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Sum
from django.forms import formset_factory

from .models import Order, MenuItem, OrderItem
from .forms import OrderCreateForm, OrderItemForm, OrderUpdateForm


def calculate_total_price(order):
    """
    Вычисляет общую стоимость заказа на основе элементов заказа.
    """
    return sum(oi.quantity * oi.menu_item.price
               for oi in order.orderitem_set.all())


def order_list(request):
    """
    Отображает список всех заказов
    с возможностью фильтрации по номеру стола и статусу.
    """
    search_query = request.GET.get('search', '')
    search_type = request.GET.get('search_type', '')
    status_mapping = {
        'В ожидании': 'pending',
        'Готово': 'ready',
        'Оплачено': 'paid',
    }
    orders = Order.objects.all()
    if search_query:
        if search_type == 'table_number':
            orders = orders.filter(table_number__icontains=search_query)
        elif search_type == 'status':
            internal_status = status_mapping.get(search_query)
            if internal_status:
                orders = orders.filter(status=internal_status)
            else:
                orders = Order.objects.none()
    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'search_query': search_query,
        'search_type': search_type
    })


def order_create(request):
    """
    Обрабатывает создание нового заказа.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_number = data.get('table_number')
            items_data = data.get('items', [])

            # Проверка на занятость стола
            existing_order = Order.objects.filter(
                table_number=table_number,
                status__in=['pending', 'ready']
            ).first()

            if existing_order:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Стол {table_number} занят. Существующий заказ ID: {existing_order.id}.'
                }, status=400)
            form = OrderCreateForm({'table_number': table_number})
            if not form.is_valid():
                return JsonResponse(
                    {'status': 'error', 'errors': form.errors}, status=400)
            order = form.save(commit=False)
            order.status = 'pending'
            order.save()
            for item_data in items_data:
                menu_item_id = item_data.get('menu_item')
                quantity = item_data.get('quantity')
                if menu_item_id and quantity:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=menu_item_id,
                        quantity=quantity)
            order.total_price = calculate_total_price(order)
            order.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Order created',
                'order_id': order.id
            }, status=201)
        except (KeyError, ValueError) as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)}, status=400)
    else:
        form = OrderCreateForm()
        return render(request, 'orders/order_create.html', {
            'form': form,
            'menu_items': MenuItem.objects.all()
        })


def order_detail(request, order_id):
    """
    Отображает детали конкретного заказа по его идентификатору.
    """
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'orders/order_detail.html', {'order': order})


def order_update(request, order_id):
    """
    Обрабатывает обновление существующего заказа.
    """
    order = get_object_or_404(Order, pk=order_id)
    formset = formset_factory(OrderItemForm, can_delete=True)
    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        order_items_form = formset(request.POST)
        if form.is_valid() and order_items_form.is_valid():
            order = form.save()
            order.orderitem_set.all().delete()
            for order_item_form in order_items_form:
                if order_item_form.cleaned_data:
                    order_item = order_item_form.save(commit=False)
                    order_item.order = order
                    order_item.save()
            order.total_price = calculate_total_price(order)
            order.save()
            if order.status == 'paid':
                calculate_revenue()
            return redirect('orders:order_list')
    else:
        form = OrderUpdateForm(instance=order)
        order_items = order.orderitem_set.all()
        initial_data = [{'menu_item': item.menu_item,
                         'quantity': item.quantity} for item in order_items]
        order_items_form = formset(initial=initial_data)
    return render(request, 'orders/order_update.html', {
        'form': form,
        'order_items_form': order_items_form,
        'order': order,
        'menu_items': MenuItem.objects.all()
    })


def order_delete(request, order_id):
    """
    Обрабатывает удаление заказа по его идентификатору.
    """
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.delete()
        return redirect('orders:order_list')
    return render(request, 'orders/order_delete.html', {'order': order})


def calculate_revenue(request=None):
    """
    Вычисляет общую выручку от оплаченных заказов.
    """
    revenue = Order.objects.filter(status='paid').aggregate(
        total_revenue=Sum('total_price'))
    if request:
        return render(request, 'orders/revenue.html', {
            'revenue': revenue['total_revenue'] or 0
        })
    return revenue['total_revenue'] or 0


def order_list_api(request):
    """
    Возвращает список всех заказов в формате JSON.
    """
    orders = Order.objects.all()
    data = [{
        'id': order.id,
        'table_number': order.table_number,
        'items': [{
            'name': item.menu_item.name,
            'price': str(item.menu_item.price),
            'quantity': item.quantity
        } for item in order.orderitem_set.all()],
        'total_price': str(order.total_price),
        'status': order.get_status_display()
    } for order in orders]
    return JsonResponse(data, safe=False)


def order_create_api(request):
    """
    Обрабатывает создание нового заказа через API.
    """
    if request.method == 'POST':
        order_form = OrderCreateForm(request.POST)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            order.status = 'pending'
            order.save()
            items_data = request.POST.getlist("items")
            for item_data in items_data:
                menu_item_id, quantity = map(int, item_data.split('_'))
                OrderItem.objects.create(order=order,
                                         menu_item_id=menu_item_id,
                                         quantity=quantity)
            order.total_price = calculate_total_price(order)
            order.save()
            return JsonResponse({'status': 'success',
                                 'message': 'Order created'}, status=201)
        return JsonResponse({'status': 'error',
                             'errors': order_form.errors}, status=400)
    return JsonResponse({'status': 'error',
                         'message': 'Invalid method'}, status=405)


def order_detail_api(request, order_id):
    """
    Возвращает детали конкретного заказа в формате JSON.
    """
    order = get_object_or_404(Order, pk=order_id)
    data = {
        'id': order.id,
        'table_number': order.table_number,
        'items': [{
            'name': item.menu_item.name,
            'price': str(item.menu_item.price),
            'quantity': item.quantity
        } for item in order.orderitem_set.all()],
        'total_price': str(order.total_price),
        'status': order.get_status_display()
    }
    return JsonResponse(data)


def order_update_api(request, order_id):
    """
    Обрабатывает обновление существующего заказа через API.
    """
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'PUT':
        order_form = OrderUpdateForm(request.POST, instance=order)
        if order_form.is_valid():
            order = order_form.save()
            OrderItem.objects.filter(order=order).delete()
            items_data = request.POST.getlist('items')
            for item_data in items_data:
                menu_item_id, quantity = map(int, item_data.split('_'))
                OrderItem.objects.create(order=order,
                                         menu_item_id=menu_item_id,
                                         quantity=quantity)
            order.total_price = calculate_total_price(order)
            order.save()
            if order.status == 'paid':
                calculate_revenue()
            return JsonResponse({'status': 'success',
                                 'message': 'Order updated'}, status=200)
        return JsonResponse({'status': 'error',
                             'errors': order_form.errors}, status=400)
    return JsonResponse({'status': 'error',
                         'message': 'Invalid method'}, status=405)


def order_delete_api(request, order_id):
    """
    Обрабатывает удаление заказа через API.
    """
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'DELETE':
        order.delete()
        return JsonResponse({'status': 'success',
                             'message': 'Order deleted'}, status=204)
    return JsonResponse({'status': 'error',
                         'message': 'Invalid method'}, status=405)
