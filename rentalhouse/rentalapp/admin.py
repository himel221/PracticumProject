from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'status', 'is_active', 'created_at')
    list_filter = ('user_type', 'status', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'profile_picture')}),
        ('Permissions', {'fields': ('user_type', 'status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )

class TenantAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'emergency_contact', 'employment_status')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

class OwnerAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'company_name', 'verification_status')
    search_fields = ('user__first_name', 'user__last_name', 'company_name')
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'property_type', 'rent_amount', 'status')
    list_filter = ('property_type', 'status', 'city')
    search_fields = ('title', 'city', 'address')

class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'tenant', 'property', 'start_date', 'end_date', 'booking_status')
    list_filter = ('booking_status', 'start_date')
    search_fields = ('tenant__user__first_name', 'property__title')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'tenant', 'amount', 'payment_status', 'due_date')
    list_filter = ('payment_status', 'payment_method')
    search_fields = ('tenant__user__first_name', 'transaction_id')

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'property', 'type', 'priority', 'status')
    list_filter = ('type', 'priority', 'status')
    search_fields = ('title', 'tenant__user__first_name')

# Register all models
admin.site.register(Users, UserAdmin)
admin.site.register(Tenants, TenantAdmin)
admin.site.register(Owners, OwnerAdmin)
admin.site.register(Properties, PropertyAdmin)
admin.site.register(Bookings, BookingAdmin)
admin.site.register(Payments, PaymentAdmin)
admin.site.register(ComplaintsRequests, ComplaintAdmin)
admin.site.register(ReviewsRatings)
admin.site.register(Messages)
admin.site.register(Notifications)
admin.site.register(PropertyImages)

# Customize admin site
admin.site.site_header = "Rental Management System Admin"
admin.site.site_title = "Rental Management System"
admin.site.index_title = "Welcome to Rental Management System Admin Panel"