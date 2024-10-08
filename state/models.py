from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    CUSTOMER = 'customer'
    AGENT = 'agent'
    OWNER = 'owner'

    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (AGENT, 'Agent'),
        (OWNER, 'Owner'),
    ]

    # New fields for additional information
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER)

    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    legal_document = models.FileField(upload_to='legal_documents/', blank=True, null=True)
    profile_complete = models.BooleanField(default=False)

    # Adding related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.full_name

    def is_profile_complete(self):
        if self.role in [self.AGENT, self.OWNER]:
            return bool(self.legal_document)
        return True


class Property(models.Model):
    SALE = 'sale'
    RENT = 'rent'

    PROPERTY_TYPE_CHOICES = [
        (SALE, 'For Sale'),
        (RENT, 'For Rent'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    property_type = models.CharField(max_length=4, choices=PROPERTY_TYPE_CHOICES)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')

    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    size_in_sqft = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title} ({self.get_property_type_display()})'

    class Meta:
        verbose_name_plural = 'Properties'


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    is_preview = models.BooleanField(default=False) 

    def __str__(self):
        return f"Image for {self.property.title} (Preview: {self.is_preview})"