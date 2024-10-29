from rest_framework import viewsets
from .models import Customer, Property
from .serializers import CustomerSerializer, PropertySerializer
from django.urls import reverse
import logging
import asyncio
import json
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .bot import bot_tele

from django.http import HttpResponseRedirect

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
    start_param = request.GET.get('tgWebAppStartParam', '')
    telegram_id = start_param.replace('edit-', '')
    user = get_object_or_404(Customer, telegram_id=telegram_id)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        user_type = request.POST.get('user_type', user.user_type)
        legal_document = request.FILES.get('legal_document')

        # Basic validation
        if not full_name:
            return render_profile_with_error(request, user, "Full Name cannot be empty.")

        # Additional checks based on user_type
        if user_type == 'owner':
            if not phone_number:
                return render_profile_with_error(request, user, "Phone Number is required for owners.")
            if not legal_document:
                return render_profile_with_error(request, user, "Legal Document is required for owners.")
        elif user_type == 'agent' and not phone_number:
            return render_profile_with_error(request, user, "Phone Number is required for agents.")

        # Update fields and save
        user.full_name = full_name
        user.email = email
        user.phone_number = phone_number
        user.address = address
        user.is_verified = False
        user.user_type = user_type

        if legal_document:
            user.legal_document = legal_document

        user.save()

        return HttpResponseRedirect(reverse('profile') + f"?tgWebAppStartParam=edit-{telegram_id}")

    # Render the profile template with user data
    return render_profile(request, user)


def render_profile_with_error(request, user, error):
    return render(request, 'profile.html', {
        'telegram_id': user.telegram_id,
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'is_verified': user.is_verified,
        'user_type': user.user_type,
        'legal_document': user.legal_document,
        'error': error,
    })


def render_profile(request, user):
    return render(request, 'profile.html', {
        'telegram_id': user.telegram_id,
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'is_verified': user.is_verified,
        'user_type': user.user_type,
        'legal_document': user.legal_document,
    })

