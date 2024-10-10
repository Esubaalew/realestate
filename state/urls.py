from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from .views import CustomerViewSet, PropertyViewSet
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'properties', PropertyViewSet)
urlpatterns = [
path('api/', include(router.urls)),
path("", views.index),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)