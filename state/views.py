from django.urls import reverse
from rest_framework import viewsets
from .models import Customer, Property
from .serializers import CustomerSerializer, PropertySerializer
from django.shortcuts import render, get_object_or_404
import logging
import asyncio
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .bot import bot_tele

logger = logging.getLogger(__name__)

@csrf_exempt
def index(request):
    if request.method == 'POST':
        data = request.body
        res = json.loads(data.decode('utf-8'))

        # Log the JSON data to avoid print issues
        logger.info(json.dumps(res, ensure_ascii=False, indent=4))

        asyncio.run(bot_tele(res))
        return HttpResponse("ok")
    else:
        return render(request, 'index.html')

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer


@csrf_exempt
def profile(request):
    # Get the start parameter from the URL
    start_param = request.GET.get('tgWebAppStartParam', '')
    telegram_id = start_param.replace('edit-', '')

    user = get_object_or_404(Customer, telegram_id=telegram_id)

    if request.method == 'POST':
        user.full_name = request.POST.get('full_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        user.address = request.POST.get('address')
        user.is_verified = False
        user.save()

        url = f"{reverse('profile')}?tgWebAppStartParam=edit-{telegram_id}"
        return HttpResponseRedirect(url)

    # Render the profile template with user data
    return render(request, 'profile.html', {
        'telegram_id': user.telegram_id,
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'is_verified': user.is_verified,
    })

