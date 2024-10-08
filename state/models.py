from django.db import models


class Customer(models.Model):
    USER_TYPE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('owner', 'Owner'),
    ]

    telegram_id = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)
    legal_document = models.FileField(upload_to='legal_documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Property(models.Model):
    FOR_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ]

    TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('lease', 'Lease'),
        ('commercial', 'Commercial'),
    ]

    USAGE_CHOICES = [
        ('office', 'For Office'),
        ('shop', 'For Shop'),
        ('restaurant', 'For Restaurant'),
    ]

    owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    for_property = models.CharField(max_length=10, choices=FOR_CHOICES)
    type_property = models.CharField(max_length=12, choices=TYPE_CHOICES)
    usage = models.CharField(max_length=12, choices=USAGE_CHOICES)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    subcity_zone = models.CharField(max_length=100)
    woreda = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    floor_level = models.CharField(max_length=20)
    total_area = models.FloatField()
    area = models.FloatField()
    google_map_link = models.URLField(max_length=200)
    living_rooms = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    kitchens = models.IntegerField()
    built_date = models.DateField()
    number_of_balconies = models.IntegerField()
    average_price_per_square_meter = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    computing_price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    features_and_amenities = models.TextField()
    heating_type = models.CharField(max_length=20, choices=[('gas', 'Gas'), ('electric', 'Electric')])
    cooling = models.CharField(max_length=20, choices=[('AC', 'AC'), ('electric', 'Electric')])
    nearest_residential = models.TextField()
    own_description = models.TextField()
    video = models.URLField(max_length=200, null=True, blank=True)
    link_to_video_or_image = models.URLField(max_length=200, null=True, blank=True)
    ownership_of_property = models.FileField(upload_to='ownership_files/')
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')], default='pending')

    def __str__(self):
        return self.name
