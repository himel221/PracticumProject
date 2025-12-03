# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import *

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Users
        fields = ['user_type', 'email', 'first_name', 'last_name', 'phone']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        return cleaned_data

class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'phone', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = Tenants
        fields = ['emergency_contact', 'employment_status', 'income_range', 'rental_history']
        widgets = {
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'income_range': forms.TextInput(attrs={'class': 'form-control'}),
            'rental_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class OwnerProfileForm(forms.ModelForm):
    class Meta:
        model = Owners
        fields = ['company_name', 'tax_id', 'bank_account_info']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_info': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Properties
        fields = [
            'title', 'description', 'address', 'city', 'state', 'zip_code',
            'property_type', 'bedrooms', 'bathrooms', 'area_sqft', 'rent_amount',
            'security_deposit', 'available_from', 'amenities'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5'}),
            'area_sqft': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'available_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amenities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_rent_amount(self):
        rent_amount = self.cleaned_data.get('rent_amount')
        if rent_amount <= 0:
            raise ValidationError("Rent amount must be positive")
        return rent_amount
    
    def clean_available_from(self):
        available_from = self.cleaned_data.get('available_from')
        if available_from and available_from < timezone.now().date():
            raise ValidationError("Available date cannot be in the past")
        return available_from
    
    def clean_bedrooms(self):
        bedrooms = self.cleaned_data.get('bedrooms')
        if bedrooms and bedrooms < 0:
            raise ValidationError("Number of bedrooms cannot be negative")
        return bedrooms

class PropertySearchForm(forms.Form):
    PROPERTY_TYPE_CHOICES = [
        ('', 'Any Type'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('condo', 'Condominium'),
        ('studio', 'Studio'),
    ]
    
    city = forms.CharField(
        required=False, 
        max_length=100, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter city'
        })
    )
    
    property_type = forms.ChoiceField(
        choices=PROPERTY_TYPE_CHOICES, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_bedrooms = forms.IntegerField(
        required=False, 
        min_value=0, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Min bedrooms'
        })
    )
    
    max_bedrooms = forms.IntegerField(
        required=False, 
        min_value=0, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Max bedrooms'
        })
    )
    
    min_rent = forms.DecimalField(
        required=False, 
        min_value=0, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Min rent', 
            'step': '0.01'
        })
    )
    
    max_rent = forms.DecimalField(
        required=False, 
        min_value=0, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Max rent', 
            'step': '0.01'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_bedrooms = cleaned_data.get('min_bedrooms')
        max_bedrooms = cleaned_data.get('max_bedrooms')
        min_rent = cleaned_data.get('min_rent')
        max_rent = cleaned_data.get('max_rent')
        
        if min_bedrooms and max_bedrooms and min_bedrooms > max_bedrooms:
            raise ValidationError("Minimum bedrooms cannot be greater than maximum bedrooms")
        
        if min_rent and max_rent and min_rent > max_rent:
            raise ValidationError("Minimum rent cannot be greater than maximum rent")
        
        return cleaned_data

class BookingForm(forms.ModelForm):
    class Meta:
        model = Bookings
        fields = ['start_date', 'end_date', 'duration_months', 'special_requests']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        duration_months = cleaned_data.get('duration_months')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            if start_date < timezone.now().date():
                raise ValidationError("Start date cannot be in the past")
        
        if duration_months and duration_months < 1:
            raise ValidationError("Duration must be at least 1 month")
        
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payments
        fields = ['amount', 'payment_method', 'due_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")
        return amount
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise ValidationError("Due date cannot be in the past")
        return due_date

class ComplaintRequestForm(forms.ModelForm):
    class Meta:
        model = ComplaintsRequests
        fields = ['type', 'title', 'description', 'priority']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long")
        return title

class ComplaintResolutionForm(forms.ModelForm):
    class Meta:
        model = ComplaintsRequests
        fields = ['status', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class ReviewRatingForm(forms.ModelForm):
    class Meta:
        model = ReviewsRatings
        fields = ['rating', 'review_text']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 5
            }),
            'review_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5")
        return rating
    
    def clean_review_text(self):
        review_text = self.cleaned_data.get('review_text')
        if review_text and len(review_text) < 10:
            raise ValidationError("Review must be at least 10 characters long")
        return review_text

class OwnerResponseForm(forms.ModelForm):
    class Meta:
        model = ReviewsRatings
        fields = ['owner_response']
        widgets = {
            'owner_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Messages
        fields = ['receiver', 'property', 'message_text']
        widgets = {
            'receiver': forms.Select(attrs={'class': 'form-control'}),
            'property': forms.Select(attrs={'class': 'form-control'}),
            'message_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Type your message here...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only show tenants and owners
        self.fields['receiver'].queryset = Users.objects.exclude(
            user_type='admin'
        )
        
        # Filter properties to only show available ones
        self.fields['property'].queryset = Properties.objects.filter(
            status='available'
        )
    
    def clean_message_text(self):
        message_text = self.cleaned_data.get('message_text')
        if len(message_text.strip()) < 1:
            raise ValidationError("Message cannot be empty")
        return message_text

class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImages
        fields = ['image_url', 'caption', 'is_primary']
        widgets = {
            'image_url': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter image caption'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminUserManagementForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['user_type', 'email', 'first_name', 'last_name', 'phone', 'status']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class AdminPropertyManagementForm(forms.ModelForm):
    class Meta:
        model = Properties
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# Filter Forms for Admin
class BookingFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date_from = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )
    
    start_date_to = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )

class PaymentFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_date_from = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )
    
    payment_date_to = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )

# Bulk Action Forms
class BulkActionForm(forms.Form):
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('delete', 'Delete Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    selected_ids = forms.CharField(widget=forms.HiddenInput())

class ReportGenerationForm(forms.Form):
    REPORT_TYPE_CHOICES = [
        ('booking', 'Booking Report'),
        ('payment', 'Payment Report'),
        ('property', 'Property Report'),
        ('user', 'User Report'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )
    
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        
        return cleaned_data

# Custom form for login without ModelForm
class SimpleLoginForm(forms.Form):
    email = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )