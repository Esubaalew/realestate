from django.shortcuts import render
from .models import Property, User

def home_view(request):
    latest_properties = Property.objects.filter(is_available=True).order_by('-id')[:5]
    agents = User.objects.filter(role=User.AGENT)
    companies = User.objects.filter(role=User.OWNER)
    return render(request, 'home.html', {'properties': latest_properties, 'agents': agents, 'companies': companies})
