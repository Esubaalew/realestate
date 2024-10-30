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
from django.contrib import messages

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

    # Check if telegram_id ends with '!'
    redirect_condition = telegram_id.endswith('!')
    if redirect_condition:
        telegram_id = telegram_id[:-1]  # Remove '!' from the ID

    user = get_object_or_404(Customer, telegram_id=telegram_id)
    logger.info(f"tgWebAppStartParam: {start_param}, redirect_condition: {redirect_condition}")

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

        # Check if we should redirect to add_property
        if redirect_condition:
            redirect_url = reverse('add_property') + f"?telegram_id={telegram_id}"
            logger.info(f"Redirecting to: {redirect_url}")  # Logging the redirect URL
            return HttpResponseRedirect(redirect_url)

        # If no redirect condition met, redirect to profile
        return HttpResponseRedirect(reverse('profile') + f"?tgWebAppStartParam={start_param}")

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


@csrf_exempt
def add_property(request):
    if request.method == 'POST':
        # Extract data from POST request
        telegram_id = request.GET.get('telegram_id')  # Get telegram ID from the URL
        owner = get_object_or_404(Customer, telegram_id=telegram_id)  # Retrieve the owner

        data = {
            'owner': owner,  # Set the owner from the retrieved Customer instance
            'name': request.POST.get('name'),
            'for_property': request.POST.get('for_property'),
            'type_property': request.POST.get('type_property'),
            'usage': request.POST.get('usage'),  # Include usage
            'country': request.POST.get('country'),  # Include country
            'region': request.POST.get('region'),  # Include region
            'city': request.POST.get('city'),  # Include city
            'subcity_zone': request.POST.get('subcity_zone'),  # Include subcity zone
            'woreda': request.POST.get('woreda'),  # Include woreda
            'address': request.POST.get('address'),  # Include address
            'floor_level': request.POST.get('floor_level'),  # Include floor level
            'total_area': request.POST.get('total_area'),
            'area': request.POST.get('area'),
            'google_map_link': request.POST.get('google_map_link'),
            'living_rooms': request.POST.get('living_rooms'),
            'bedrooms': request.POST.get('bedrooms'),
            'bathrooms': request.POST.get('bathrooms'),
            'kitchens': request.POST.get('kitchens'),  # Include kitchens
            'built_date': request.POST.get('built_date'),  # Include built date
            'number_of_balconies': request.POST.get('number_of_balconies'),  # Include balconies
            'average_price_per_square_meter': request.POST.get('average_price_per_square_meter'),
            'selling_price': request.POST.get('selling_price'),
            'computing_price': request.POST.get('computing_price'),  # Include computing price
            'monthly_rent': request.POST.get('monthly_rent'),
            'features_and_amenities': request.POST.get('features_and_amenities'),
            'heating_type': request.POST.get('heating_type'),  # Include heating type
            'cooling': request.POST.get('cooling'),  # Include cooling
            'nearest_residential': request.POST.get('nearest_residential'),
            'own_description': request.POST.get('own_description'),  # Include own description

            'link_to_video_or_image': request.POST.get('link_to_video_or_image'),  # Include video/image link
            'ownership_of_property': request.FILES.get('ownership_of_property'),  # Include ownership document
        }

        # Create Property instance and save
        property_instance = Property(**data)
        property_instance.save()

        messages.success(request, "Property added successfully!")
        return redirect('property_success')  # Redirect to success page

    return render(request, 'property_form.html')


@csrf_exempt
def my_properties(request):
    telegram_id = request.GET.get('telegram_id')
    owner = get_object_or_404(Customer, telegram_id=telegram_id)
    # Get the properties added by the owner
    properties = Property.objects.filter(owner=owner)

    context = {
        'properties': properties,
        'owner': owner,
    }
    return render(request, 'my_properties.html', context)


