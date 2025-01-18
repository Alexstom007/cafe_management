from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/update/', views.order_update, name='order_update'),
    path('<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path('revenue/', views.calculate_revenue, name='revenue'),
    # API endpoints
    path('api/orders/', views.order_list_api, name='order_list_api'),
    path('api/orders/create/', views.order_create_api,
         name='order_create_api'),
    path('api/orders/<int:order_id>/', views.order_detail_api,
         name='order_detail_api'),
    path('api/orders/<int:order_id>/update/', views.order_update_api,
         name='order_update_api'),
    path('api/orders/<int:order_id>/delete/', views.order_delete_api,
         name='order_delete_api'),
]
