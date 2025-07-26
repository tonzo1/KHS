from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models # Needed for Q objects in queries
from django.http import HttpResponse # Needed for CSV file responses
from django.core.files.storage import FileSystemStorage # CORRECTED IMPORT: No longer 'import FileSystemStorage'
from django.utils import timezone # Needed for timezone-aware datetimes for import
from django.contrib.auth.decorators import login_required, permission_required 
import csv
from io import TextIOWrapper
import os # Potentially useful for file path manipulation, though not strictly needed here for the main fix

from .models import Member, MembershipHistory, ImageModels # Ensure all models are imported
from .forms import MemberForm, CSVImportForm

# Dashboard View
@login_required # Ensures only logged-in users can access the dashboard
def dashboard(request):
    """
    Displays key metrics and information on the membership dashboard.
    """
    total_members = Member.objects.count()
    active_members = Member.objects.filter(is_active=True).count()
    # Assuming 'P' is the code for Premium members based on your MEMBERSHIP_TYPES
    premium_members = Member.objects.filter(membership_type='P').count()
    # You could add logic for upcoming renewals, recently added members, etc.

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'premium_members': premium_members,
    }
    return render(request, 'members/dashboard.html', context)

# Member List View (Read)
class MemberListView(LoginRequiredMixin, ListView):
    model = Member
    template_name = 'members/member_list.html'
    context_object_name = 'members' # The variable name to use in the template
    paginate_by = 20 # Number of members per page
    ordering = ['-date_joined'] # Order by most recently joined

    def get_queryset(self):
        """
        Overrides the default queryset to implement search functionality.
        """
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            # Use Q objects for OR queries to search across multiple fields
            queryset = queryset.filter(
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(email__icontains=search_query) |
                models.Q(phone__icontains=search_query) |
                models.Q(membership_type__icontains=search_query) # Search by type code (R, P, V)
            )
        # Use .distinct() to prevent duplicate rows if a search query matches multiple fields
        # (e.g., if 'john' is in first_name and last_name, without distinct, John might appear twice)
        return queryset.distinct()

# Member Detail View (Read single member)
class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = 'members/member_detail.html'
    context_object_name = 'member'

# Member Create View (Create new member)
class MemberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'members/member_form.html'
    success_url = reverse_lazy('members:list') # Redirect to the member list after creation
    permission_required = 'members.add_member' # Requires 'members.add_member' permission

    def form_valid(self, form):
        """
        Called when the form is valid. Adds a success message.
        The form's save method (from MemberForm, inheriting UserCreationForm)
        will handle password hashing and saving the instance correctly.
        """
        messages.success(self.request, "Member created successfully!")
        return super().form_valid(form)

# Member Update View (Edit existing member)
class MemberUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'members/member_form.html'
    success_url = reverse_lazy('members:list') # Redirect to the member list after update
    permission_required = 'members.change_member' # Requires 'members.change_member' permission

    def form_valid(self, form):
        """
        Called when the form is valid. Adds a success message.
        """
        messages.success(self.request, "Member updated successfully!")
        return super().form_valid(form)

# Member Delete View (Delete member)
class MemberDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Member
    template_name = 'members/member_confirm_delete.html'
    success_url = reverse_lazy('members:list') # Redirect to member list after deletion
    permission_required = 'members.delete_member' # Requires 'members.delete_member' permission

    def delete(self, request, *args, **kwargs):
        """
        Overrides the delete method to add a success message.
        """
        messages.success(request, "Member deleted successfully!")
        return super().delete(request, *args, **kwargs)

# CSV Export View
@login_required # Ensure user is logged in

@permission_required('members.export_member') # <--- CHANGE THIS DECORATOR for function-based views
def export_csv(request):
    """
    Generates and downloads a CSV file containing all member data.
    """
    response = HttpResponse(content_type='text/csv')
    # Set the filename for the downloaded file
    response['Content-Disposition'] = 'attachment; filename="members_export.csv"'

    writer = csv.writer(response)
    # Define and write the header row for the CSV
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Address',
        'Membership Type', 'Date Joined', 'Membership Expiry', 'Notes',
        'Is Active', 'Is Staff', 'Is Superuser'
    ])

    # Fetch all members, ordered for consistent output
    members = Member.objects.all().order_by('last_name', 'first_name')
    for member in members:
        # Write each member's data as a row
        writer.writerow([
            member.id,
            member.first_name,
            member.last_name,
            member.email,
            member.phone,
            member.address,
            member.get_membership_type_display(), # Use model method to get human-readable membership type
            member.date_joined.strftime('%Y-%m-%d %H:%M:%S') if member.date_joined else '', # Format datetime
            member.membership_expiry.strftime('%Y-%m-%d') if member.membership_expiry else '', # Format date
            member.notes,
            'Yes' if member.is_active else 'No', # Convert boolean to readable string
            'Yes' if member.is_staff else 'No',
            'Yes' if member.is_superuser else 'No',
        ])
    messages.success(request, "Members exported to CSV successfully!")
    return response

# CSV Import View
@login_required # Ensure user is logged in
@permission_required('members.import_member') # <--- CHANGE THIS DECORATOR for function-based views

def import_csv(request):
    """
    Handles the upload and processing of a CSV file to import or update member data.
    """
    form = CSVImportForm() # Initialize an empty form for GET requests (displaying the upload form)

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            overwrite = form.cleaned_data['overwrite']
            dry_run = form.cleaned_data['dry_run']

            # Wrap the uploaded file in TextIOWrapper to read it as text, ensuring UTF-8 encoding
            decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(decoded_file)
            
            # Define the minimum required headers for your CSV
            required_headers = ['first_name', 'last_name', 'email']
            
            # Validate if all required headers are present in the uploaded CSV
            if not all(h in reader.fieldnames for h in required_headers):
                missing_headers = [h for h in required_headers if h not in reader.fieldnames]
                messages.error(request, f"CSV missing required columns: {', '.join(missing_headers)}")
                return render(request, 'members/import_csv.html', {'form': form})

            imported_count = 0
            updated_count = 0
            errors = []
            
            # Iterate through each row in the CSV
            for row_num, row in enumerate(reader, start=2): # Start counting from line 2 (after header)
                try:
                    # ALL the code for processing a single row goes here:
                    email = row.get('email', '').lower() # Get email and convert to lowercase
                    if not email: # Skip rows with no email
                        errors.append(f"Row {row_num}: Missing email, skipping row.")
                        continue

                    # Attempt to find an existing member by email
                    member_exists = Member.objects.filter(email=email).first()

                    if member_exists and not overwrite:
                        # If member exists and overwrite is not enabled, skip this row
                        errors.append(f"Row {row_num} (Email: {email}): Member already exists, skipping (overwrite not enabled).")
                        continue

                    if member_exists and overwrite:
                        # If member exists and overwrite is enabled, update existing member
                        member = member_exists
                        updated_count += 1
                    else:
                        # Create a new member instance
                        member = Member()
                        imported_count += 1
                        # For new members created via import, set an unusable password.
                        # This prevents direct login but allows the user object to be saved.
                        # You might have an activation process or a default password policy.
                        member.set_unusable_password()

                    # Populate member fields from CSV row, using .get() with defaults for safety
                    member.first_name = row.get('first_name', '')
                    member.last_name = row.get('last_name', '')
                    member.email = email # Already lowercased above
                    member.phone = row.get('phone', '')
                    member.address = row.get('address', '')

                    # Map human-readable membership type from CSV to model code (e.g., "Regular" to "R")
                    membership_type_map = {
                        ('S', 'Single'),
                        ('D', 'Double'),
                        ('L', 'LifeTime'),
                        ('G', 'Gardener')
                    }
                    csv_membership_type = row.get('membership_type', 'Regular') # Default to 'Single' if not specified
                    member.membership_type = membership_type_map.get(csv_membership_type, 'S') # Default to 'R' if not in map

                    member.notes = row.get('notes', '')
                    
                    # Handle boolean fields, converting "True"/"False" strings to actual booleans
                    member.is_active = row.get('is_active', 'True').lower() == 'true'
                    member.is_staff = row.get('is_staff', 'False').lower() == 'true'
                    member.is_superuser = row.get('is_superuser', 'False').lower() == 'true'

                    # Handle date fields for import
                    # Date Joined (e.g., '2023-01-15 10:30:00')
                    date_joined_str = row.get('date_joined')
                    if date_joined_str:
                        try:
                            # Parse string to datetime object and make it timezone-aware
                            member.date_joined = timezone.datetime.strptime(date_joined_str, '%Y-%m-%d %H:%M:%S').astimezone(timezone.get_current_timezone())
                        except ValueError:
                            errors.append(f"Row {row_num} (Email: {email}): Invalid date_joined format. Expected YYYY-MM-DD HH:MM:SS.")
                            # Do not continue, process rest of the row, but log error
                    # If date_joined is not in CSV, Member model's default=timezone.now will apply for new members

                    # Membership Expiry (e.g., '2024-12-31')
                    membership_expiry_str = row.get('membership_expiry')
                    if membership_expiry_str:
                        try:
                            # Parse string to date object
                            member.membership_expiry = timezone.datetime.strptime(membership_expiry_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Row {row_num} (Email: {email}): Invalid membership_expiry format. Expected YYYY-MM-DD.")
                            # Continue to save if other fields are okay, just note error.
                        if not dry_run:
                            member.save()

                except Exception as e: # <--- THIS IS THE EXCEPT BLOCK YOU NEED
                    # Catch any other unexpected errors during row processing
                    errors.append(f"Error processing row {row_num} (Email: {row.get('email', 'N/A')}): {str(e)}")



# Display summary and error messages after processing all rows
            if errors:
                for error_msg in errors:
                    messages.error(request, error_msg)
            
            summary_message = f"CSV import finished. Imported: {imported_count}, Updated: {updated_count}."
            if dry_run:
                messages.info(request, "DRY RUN COMPLETE: No changes were made to the database.")
            messages.success(request, summary_message)

            return redirect('members:list') # Redirect to the member list after import/dry run

    # For GET requests, render the import form
    return render(request, 'members/import_csv.html', {'form': form})

# Image Upload View (for generic ImageModels, not Member.profile_image)
# This view is for uploading images to your ImageModels, which seems separate from
# a Member's profile picture which is typically handled by the MemberForm itself.
def image_upload(request):
    """
    Handles the upload of a generic image to the ImageModels.
    """
    if request.method == 'POST' and request.FILES.get('image_file'):
        try:
            image_file = request.FILES['image_file']
            fs = FileSystemStorage() # This storage saves files to your MEDIA_ROOT
            
            # fs.save() returns the relative path from MEDIA_ROOT.
            # Example: If MEDIA_ROOT is /path/to/project/media/
            # and image_file.name is 'my_pic.jpg', filename will be 'my_pic.jpg'
            # The file will be saved at /path/to/project/media/my_pic.jpg
            filename = fs.save(image_file.name, image_file)
            
            # Create an ImageModels instance to record the upload
            ImageModels.objects.create(title=image_file.name, image=filename) # Store the path/name
            
            uploaded_file_url = fs.url(filename) # Get the accessible URL
            messages.success(request, 'Image uploaded successfully!')
            return render(request, 'members/image_upload.html', {
                'uploaded_file_url': uploaded_file_url

})
        except Exception as e:
            messages.error(request, f'Error uploading image: {str(e)}')
    return render(request, 'members/image_upload.html')

# View to list generic images (if ImageModels is used)
@login_required # Ensure user is logged in
def image_list(request):
    """
    Lists all uploaded images from ImageModels.
    """
    images = ImageModels.objects.all().order_by('-uploaded_at')
    return render(request, 'members/image_list.html', {'images': images})

# View to delete a generic image (if ImageModels is used)
@login_required # Ensure user is logged in
@permission_required('members.delete_imagemodels') # Correct decorator for function-based views
def image_delete(request, pk):

    """
    Deletes a specific image from ImageModels and its corresponding file from storage.
    """
    image = get_object_or_404(ImageModels, pk=pk)
    if request.method == 'POST':
        # Delete the file from storage system first
        if image.image: # Check if an image file is associated
            image.image.delete(save=False) # delete from storage, but don't save model yet (will be deleted next)

        image.delete() # Delete the model instance from the database
        messages.success(request, f"Image '{image.title}' deleted successfully!")
        return redirect('members:image_list') # Redirect to a list of images or similar
    
    # For GET request, display confirmation page before deletion
    return render(request, 'members/image_confirm_delete.html', {'image': image})