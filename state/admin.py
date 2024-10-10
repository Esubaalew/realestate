from django.contrib import admin
from .models import User, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1  # Number of empty forms to display for adding new images


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'property_type', 'is_available')
    search_fields = ('title', 'location', 'description')
    list_filter = ('property_type', 'is_available')
    inlines = [PropertyImageInline]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role', 'phone_number', 'profile_complete')
    search_fields = ('full_name', 'email', 'phone_number')
    list_filter = ('role', 'profile_complete')

    # Hide the first_name and last_name fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info',
         {'fields': ('full_name', 'email', 'phone_number', 'profile_picture', 'role', 'company', 'legal_document')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Profile Status', {'fields': ('profile_complete',)}),
    )


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'is_preview')
    search_fields = ('property__title',)
