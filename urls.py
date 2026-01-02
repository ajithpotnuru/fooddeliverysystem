from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.auth_login, name='login'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_status'),
    path('ratings/', views.add_rating, name='add_rating'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('menu/<int:restaurant_id>/', views.menu_items, name='menu'),
]
