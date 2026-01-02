from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, F
from django.utils import timezone
import json

@csrf_exempt
def auth_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'role': user.role})
    return JsonResponse({'success': False})

@login_required
def create_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = Order.objects.create(
            customer=request.user,
            restaurant_id=data['restaurant_id'],
            total_amount=data['total_amount'],
            delivery_address=data['address']
        )
        for item in data['items']:
            OrderItem.objects.create(
                order=order,
                menu_item_id=item['menu_item_id'],
                quantity=item['quantity'],
                price=item['price']
            )
        # Auto-assign delivery partner
        delivery_partner = User.objects.filter(role='delivery').first()
        if delivery_partner:
            order.delivery_partner = delivery_partner
            order.status = 'confirmed'
            order.save()
        return JsonResponse({'order_id': order.id})

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=order_id)
        order.status = data['status']
        if data['status'] == 'delivered':
            order.delivered_at = timezone.now()
        order.save()
        return JsonResponse({'success': True})

@login_required
def add_rating(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        Rating.objects.create(
            order_id=data['order_id'],
            rating=data['rating'],
            comment=data.get('comment', '')
        )
        return JsonResponse({'success': True})

def analytics_dashboard(request):
    # Average delivery time
    avg_delivery_time = Order.objects.filter(
        status='delivered',
        delivered_at__isnull=False
    ).aggregate(
        avg_time=Avg(F('delivered_at') - F('created_at'))
    )
    
    # Peak order times
    peak_hours = Order.objects.extra(
        select={'hour': 'EXTRACT(hour FROM created_at)'}
    ).values('hour').annotate(count=Count('id')).order_by('-count')
    
    # Best restaurants
    best_restaurants = Restaurant.objects.annotate(
        avg_rating=Avg('order__rating__rating'),
        order_count=Count('order')
    ).order_by('-avg_rating')[:10]
    
    return JsonResponse({
        'avg_delivery_time': str(avg_delivery_time['avg_time']) if avg_delivery_time['avg_time'] else '0',
        'peak_hours': list(peak_hours),
        'best_restaurants': [{'name': r.name, 'rating': r.avg_rating, 'orders': r.order_count} 
                           for r in best_restaurants]
    })

def menu_items(request, restaurant_id):
    items = MenuItem.objects.filter(restaurant_id=restaurant_id, available=True)
    return JsonResponse({
        'items': [{'id': i.id, 'name': i.name, 'price': str(i.price)} for i in items]
    })
