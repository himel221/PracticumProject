from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .form import *
from .models import *

def home(request):
    featured_properties = Properties.objects.filter(status='available')[:6]
    return render(request, 'home.html', {'featured_properties': featured_properties})

def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            user_type = form.cleaned_data['user_type']
            if user_type == 'tenant':
                Tenants.objects.create(user=user)
                messages.success(request, 'Tenant account created successfully! Please login.')
            elif user_type == 'owner':
                Owners.objects.create(user=user)
                messages.success(request, 'Owner account created successfully! Please login.')
            
            return redirect('user_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = Users.objects.get(email=email)
            if user.check_password(password):
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    if user.user_type == 'admin' or user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.user_type == 'owner':
                        return redirect('owner_dashboard')
                    else:
                        return redirect('tenant_dashboard')
                else:
                    messages.error(request, 'Your account is disabled.')
            else:
                messages.error(request, 'Invalid email or password.')
        except Users.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    else:
        pass
    
    return render(request, 'auth/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def tenant_dashboard(request):
    if request.user.user_type != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    tenant = get_object_or_404(Tenants, user=request.user)
    bookings = Bookings.objects.filter(tenant=tenant).order_by('-created_at')
    payments = Payments.objects.filter(tenant=tenant).order_by('-created_at')
    complaints = ComplaintsRequests.objects.filter(tenant=tenant).order_by('-created_at')

    # Group complaints for easier display in template
    complaints_open = complaints.filter(status='open')
    complaints_in_progress = complaints.filter(status='in-progress')
    complaints_resolved = complaints.filter(status='resolved')
    
    total_paid = payments.filter(payment_status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'tenant': tenant,
        'bookings': bookings,
        'payments': payments,
        'complaints': complaints,
        'complaints_open': complaints_open,
        'complaints_in_progress': complaints_in_progress,
        'complaints_resolved': complaints_resolved,
        'total_paid': total_paid,
    }
    return render(request, 'dashboard/tenant_dashboard.html', context)

@login_required
def owner_dashboard(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    owner = get_object_or_404(Owners, user=request.user)
    properties = Properties.objects.filter(owner=owner)
    all_bookings = Bookings.objects.filter(property__owner=owner).order_by('-created_at')
    payments = Payments.objects.filter(owner=owner).order_by('-created_at')
    
    pending_bookings = all_bookings.filter(booking_status='pending')
    
    total_properties = properties.count()
    active_bookings = all_bookings.filter(booking_status='confirmed').count()
    total_earnings = payments.filter(payment_status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'owner': owner,
        'properties': properties,
        'bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'total_properties': total_properties,
        'active_bookings': active_bookings,
        'total_earnings': total_earnings,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    total_users = Users.objects.count()
    total_properties = Properties.objects.count()
    total_bookings = Bookings.objects.count()
    total_payments = Payments.objects.count()
    pending_complaints = ComplaintsRequests.objects.filter(status='open').count()
    
    recent_users = Users.objects.order_by('-created_at')[:5]
    recent_bookings = Bookings.objects.order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_properties': total_properties,
        'total_bookings': total_bookings,
        'total_payments': total_payments,
        'pending_complaints': pending_complaints,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def user_profile(request):
    user = request.user
    
    profile_form = UserProfileForm(instance=user)
    tenant_form = None
    owner_form = None
    
    if user.user_type == 'tenant':
        try:
            tenant = Tenants.objects.get(user=user)
            tenant_form = TenantProfileForm(instance=tenant)
        except Tenants.DoesNotExist:
            tenant_form = TenantProfileForm()
    elif user.user_type == 'owner':
        try:
            owner = Owners.objects.get(user=user)
            owner_form = OwnerProfileForm(instance=owner)
        except Owners.DoesNotExist:
            owner_form = OwnerProfileForm()
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
        
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            
            if user.user_type == 'tenant':
                tenant = Tenants.objects.get(user=user)
                tenant_form = TenantProfileForm(request.POST, instance=tenant)
                if tenant_form.is_valid():
                    tenant_form.save()
            elif user.user_type == 'owner':
                owner = Owners.objects.get(user=user)
                owner_form = OwnerProfileForm(request.POST, instance=owner)
                if owner_form.is_valid():
                    owner_form.save()
            
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    context = {
        'profile_form': profile_form,
        'tenant_form': tenant_form,
        'owner_form': owner_form,
    }
    
    return render(request, 'auth/profile.html', context)

@login_required
def property_list(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    owner = get_object_or_404(Owners, user=request.user)
    properties = Properties.objects.filter(owner=owner)
    
    return render(request, 'properties/property_list.html', {'properties': properties})

@login_required
def add_property(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    owner = get_object_or_404(Owners, user=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = owner
            property_obj.save()
            messages.success(request, 'Property added successfully!')
            return redirect('property_list')
    else:
        form = PropertyForm()
    
    return render(request, 'properties/add_property.html', {'form': form})

@login_required
def edit_property(request, property_id):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    property_obj = get_object_or_404(Properties, pk=property_id, owner__user=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('property_list')
    else:
        form = PropertyForm(instance=property_obj)
    
    return render(request, 'properties/edit_property.html', {'form': form, 'property': property_obj})

@login_required
def delete_property(request, property_id):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    property_obj = get_object_or_404(Properties, pk=property_id, owner__user=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('property_list')
    
    return render(request, 'properties/delete_property.html', {'property': property_obj})

def property_search(request):
    properties = Properties.objects.filter(status='available')
    form = PropertySearchForm(request.GET or None)
    
    if form.is_valid():
        city = form.cleaned_data.get('city')
        property_type = form.cleaned_data.get('property_type')
        min_bedrooms = form.cleaned_data.get('min_bedrooms')
        max_bedrooms = form.cleaned_data.get('max_bedrooms')
        min_rent = form.cleaned_data.get('min_rent')
        max_rent = form.cleaned_data.get('max_rent')
        
        if city:
            properties = properties.filter(city__icontains=city)
        if property_type:
            properties = properties.filter(property_type=property_type)
        if min_bedrooms:
            properties = properties.filter(bedrooms__gte=min_bedrooms)
        if max_bedrooms:
            properties = properties.filter(bedrooms__lte=max_bedrooms)
        if min_rent:
            properties = properties.filter(rent_amount__gte=min_rent)
        if max_rent:
            properties = properties.filter(rent_amount__lte=max_rent)
    
    context = {
        'properties': properties,
        'form': form,
    }
    return render(request, 'properties/property_search.html', context)

def property_detail(request, property_id):
    property_obj = get_object_or_404(Properties, pk=property_id)
    images = PropertyImages.objects.filter(property=property_obj)
    reviews = ReviewsRatings.objects.filter(property=property_obj, is_approved=True)
    
    context = {
        'property': property_obj,
        'images': images,
        'reviews': reviews,
    }
    return render(request, 'properties/property_detail.html', context)

@login_required
def book_property(request, property_id):
    if request.user.user_type != 'tenant':
        messages.error(request, 'Only tenants can book properties.')
        return redirect('home')
    
    property_obj = get_object_or_404(Properties, pk=property_id, status='available')
    tenant = get_object_or_404(Tenants, user=request.user)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tenant = tenant
            booking.property = property_obj
            # Compute duration (in months) from start and end dates
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            # Default to 1 month if dates not provided (should be validated earlier)
            months = 1
            if start_date and end_date:
                days = (end_date - start_date).days
                # approximate months as ceil(days / 30)
                import math
                months = max(1, math.ceil(days / 30))

            booking.duration_months = months
            booking.total_amount = property_obj.rent_amount * months
            booking.security_deposit = property_obj.security_deposit or property_obj.rent_amount

            booking.save()
            booking.save()
            
            messages.success(request, 'Property booked successfully!')
            return redirect('tenant_dashboard')
    else:
        form = BookingForm()
    
    context = {
        'property': property_obj,
        'form': form,
    }
    return render(request, 'bookings/book_property.html', context)

@login_required
def confirm_booking(request, booking_id):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        booking = get_object_or_404(Bookings, pk=booking_id, property__owner__user=request.user)
        
        if booking.booking_status == 'pending':
            booking.booking_status = 'confirmed'
            booking.save()
            
            booking.property.status = 'occupied'
            booking.property.save()
            
            messages.success(request, f'Booking #{booking.booking_id} has been confirmed!')
        else:
            messages.warning(request, 'This booking is already processed.')
            
    except Bookings.DoesNotExist:
        messages.error(request, 'Booking not found or you do not have permission.')
    
    return redirect('owner_dashboard')

@login_required
def cancel_booking(request, booking_id):
    # Only accept POST requests for cancellation
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('home')

    try:
        booking = Bookings.objects.get(pk=booking_id)
    except Bookings.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('home')

    # Determine if the requester is authorized (owner of property or the tenant)
    user = request.user
    redirect_target = 'home'
    authorized = False

    if user.user_type == 'owner' and hasattr(user, 'owner'):
        if booking.property.owner.user == user:
            authorized = True
            redirect_target = 'owner_dashboard'

    if user.user_type == 'tenant' and hasattr(user, 'tenant'):
        if booking.tenant.user == user:
            authorized = True
            redirect_target = 'tenant_dashboard'

    if not authorized:
        messages.error(request, 'Booking not found or you do not have permission.')
        return redirect('home')

    if booking.booking_status == 'pending':
        booking.booking_status = 'cancelled'
        booking.save()
        # If property was marked occupied by this booking, free it up
        try:
            prop = booking.property
            if prop.status == 'occupied':
                prop.status = 'available'
                prop.save()
        except Exception:
            pass

        messages.success(request, f'Booking #{booking.booking_id} has been cancelled.')
    else:
        messages.warning(request, 'This booking is already processed.')

    return redirect(redirect_target)


@login_required
def confirm_payment(request, payment_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('owner_payments')

    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')

    try:
        payment = get_object_or_404(Payments, pk=payment_id, owner__user=request.user)
        if payment.payment_status != 'completed':
            payment.payment_status = 'completed'
            if not payment.payment_date:
                from django.utils import timezone
                payment.payment_date = timezone.now().date()
            payment.save()
            messages.success(request, f'Payment #{payment.payment_id} marked as received.')
        else:
            messages.info(request, 'Payment already marked as completed.')
    except Payments.DoesNotExist:
        messages.error(request, 'Payment not found or you do not have permission.')

    return redirect('owner_payments')


@login_required
def export_payments_csv(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')

    owner = get_object_or_404(Owners, user=request.user)
    payments = Payments.objects.filter(owner=owner).order_by('-created_at')

    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="owner_payments.csv"'

    writer = csv.writer(response)
    writer.writerow(['Payment ID', 'Booking ID', 'Property', 'Tenant', 'Amount', 'Payment Date', 'Status'])

    for p in payments:
        writer.writerow([
            p.payment_id,
            getattr(p.booking, 'booking_id', ''),
            getattr(p.booking.property, 'title', ''),
            f"{p.tenant.user.first_name} {p.tenant.user.last_name}",
            str(p.amount),
            p.payment_date or '',
            p.payment_status,
        ])

    return response


@login_required
def export_payments_pdf(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')

    owner = get_object_or_404(Owners, user=request.user)
    payments = Payments.objects.filter(owner=owner).order_by('-created_at')

    try:
        # Use reportlab to generate PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph(f"Payments Report - {owner.user.get_full_name()}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [['Payment ID', 'Booking ID', 'Property', 'Tenant', 'Amount', 'Payment Date', 'Status']]
        for p in payments:
            data.append([
                str(p.payment_id),
                str(getattr(p.booking, 'booking_id', '')),
                getattr(p.booking.property, 'title', ''),
                f"{p.tenant.user.first_name} {p.tenant.user.last_name}",
                str(p.amount),
                str(p.payment_date or ''),
                p.payment_status,
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (4,1), (4,-1), 'RIGHT'),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        from django.http import HttpResponse
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="owner_payments.pdf"'
        return response

    except ImportError:
        messages.error(request, 'PDF export requires the "reportlab" package. Install it with: pip install reportlab')
        return redirect('owner_payments')

@login_required
def make_payment(request, booking_id):
    if request.user.user_type != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    booking = get_object_or_404(Bookings, pk=booking_id, tenant__user=request.user)
    tenant = get_object_or_404(Tenants, user=request.user)
    owner = booking.property.owner
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.tenant = tenant
            payment.owner = owner
            payment.save()
            
            messages.success(request, 'Payment submitted successfully!')
            return redirect('tenant_dashboard')
    else:
        initial_data = {'amount': booking.property.rent_amount}
        form = PaymentForm(initial=initial_data)
    
    context = {
        'booking': booking,
        'form': form,
    }
    return render(request, 'payments/make_payment.html', context)

@login_required
def submit_complaint(request):
    if request.user.user_type != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        tenant = request.user.tenant
    except:
        messages.error(request, 'Tenant profile not found.')
        return redirect('tenant_dashboard')

    try:
        active_booking = Bookings.objects.filter(
            tenant=tenant,
            booking_status__in=['confirmed', 'completed']
        ).latest('start_date')
        property_obj = active_booking.property
    except Bookings.DoesNotExist:
        messages.error(request, 'No active booking found.')
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        form = ComplaintRequestForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = tenant
            complaint.property = property_obj
            complaint.save()
            
            messages.success(request, 'Complaint submitted successfully!')
            return redirect('tenant_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintRequestForm()
    
    return render(request, 'complaints/submit_complaint.html', {
        'form': form,
        'property': property_obj
    })

@login_required
def owner_complaints(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        owner = request.user.owner
    except:
        messages.error(request, 'Owner profile not found.')
        return redirect('login')
    
    owner_properties = Properties.objects.filter(owner=owner)
    # list of tenants who have complaints on owner's properties
    tenants_with_complaints = Tenants.objects.filter(complaints__property__in=owner_properties).distinct()

    # Optionally filter by tenant via GET parameter
    tenant_id = request.GET.get('tenant_id')
    if tenant_id:
        try:
            selected_tenant = Tenants.objects.get(tenant_id=tenant_id)
            complaints = ComplaintsRequests.objects.filter(property__in=owner_properties, tenant=selected_tenant).order_by('-created_at')
        except Tenants.DoesNotExist:
            selected_tenant = None
            complaints = ComplaintsRequests.objects.filter(property__in=owner_properties).order_by('-created_at')
    else:
        selected_tenant = None
        complaints = ComplaintsRequests.objects.filter(property__in=owner_properties).order_by('-created_at')
    
    if request.method == 'POST' and 'complaint_id' in request.POST:
        complaint_id = request.POST.get('complaint_id')
        try:
            complaint = ComplaintsRequests.objects.get(
                complaint_id=complaint_id,
                property__in=owner_properties
            )
            form = ComplaintResolutionForm(request.POST, instance=complaint)
            if form.is_valid():
                resolved_complaint = form.save(commit=False)
                
                if resolved_complaint.status == 'resolved' and not resolved_complaint.resolved_at:
                    resolved_complaint.resolved_at = timezone.now()
                
                if resolved_complaint.status != 'resolved':
                    resolved_complaint.resolved_at = None
                
                resolved_complaint.save()
                messages.success(request, f'Complaint #{complaint_id} updated successfully!')
                return redirect('owner_complaints')
            else:
                messages.error(request, 'Please correct the errors below.')
        except ComplaintsRequests.DoesNotExist:
            messages.error(request, 'Complaint not found.')
    
    total_complaints = complaints.count()
    open_complaints = complaints.filter(status='open').count()
    in_progress_complaints = complaints.filter(status='in-progress').count()
    resolved_complaints = complaints.filter(status='resolved').count()
    
    high_priority_complaints = complaints.filter(priority='high', status__in=['open', 'in-progress'])
    
    context = {
        'owner': owner,
        'complaints': complaints,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'high_priority_complaints': high_priority_complaints,
        'tenants_with_complaints': tenants_with_complaints,
        'selected_tenant': selected_tenant,
    }
    
    return render(request, 'complaints/owner_complaints.html', context)

@login_required
def quick_resolve_complaint(request, complaint_id):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        owner = request.user.owner
        complaint = get_object_or_404(
            ComplaintsRequests, 
            complaint_id=complaint_id,
            property__owner=owner
        )
        
        complaint.status = 'resolved'
        complaint.resolution_notes = 'Resolved by owner.'
        complaint.resolved_at = timezone.now()
        complaint.save()
        
        messages.success(request, f'Complaint #{complaint_id} marked as resolved!')
    except Exception as e:
        messages.error(request, f'Error resolving complaint: {str(e)}')
    
    return redirect('owner_complaints')

@login_required
def submit_review(request, booking_id):
    if request.user.user_type != 'tenant':
        messages.error(request, 'Only tenants can submit reviews.')
        return redirect('home')
    
    booking = get_object_or_404(Bookings, pk=booking_id, tenant__user=request.user)
    
    if ReviewsRatings.objects.filter(booking=booking).exists():
        messages.error(request, 'You have already reviewed this property.')
        return redirect('tenant_dashboard')
    
    if request.method == 'POST':
        form = ReviewRatingForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tenant = booking.tenant
            review.property = booking.property
            review.booking = booking
            review.save()
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('tenant_dashboard')
    else:
        form = ReviewRatingForm()
    
    context = {
        'booking': booking,
        'form': form,
    }
    return render(request, 'reviews/submit_review.html', context)

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('tenant_dashboard' if request.user.user_type == 'tenant' else 'owner_dashboard')
    else:
        form = MessageForm()
    
    return render(request, 'messages/send_message.html', {'form': form})

@login_required
def inbox(request):
    received_messages = Messages.objects.filter(receiver=request.user).order_by('-sent_at')
    sent_messages = Messages.objects.filter(sender=request.user).order_by('-sent_at')
    
    context = {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
    }
    return render(request, 'messages/inbox.html', context)

# NEW VIEWS ADDED
@login_required
def owner_booking_list(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    owner = get_object_or_404(Owners, user=request.user)
    bookings = Bookings.objects.filter(property__owner=owner).order_by('-created_at')
    
    context = {
        'bookings': bookings,
        'owner': owner,
    }
    return render(request, 'owner/owner_booking_list.html', context)

@login_required
def owner_payments(request):
    if request.user.user_type != 'owner':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    owner = get_object_or_404(Owners, user=request.user)
    payments = Payments.objects.filter(owner=owner).order_by('-created_at')
    
    context = {
        'payments': payments,
        'owner': owner,
    }
    # Render the owner payments template (file at templates/owner_payments.html)
    return render(request, 'owner_payments.html', context)

@login_required
def delete_message(request, message_id):
    """Delete a message (sent or received)"""
    try:
        # User can delete messages they sent OR received
        message = get_object_or_404(
            Messages,
            pk=message_id
        )
        
        # Check if user is sender or receiver
        if message.sender != request.user and message.receiver != request.user:
            messages.error(request, 'You do not have permission to delete this message.')
            return redirect('inbox')
        
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        
    except Messages.DoesNotExist:
        messages.error(request, 'Message not found.')
    
    return redirect('inbox')