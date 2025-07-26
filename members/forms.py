from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import FileExtensionValidator
from .models import Member
import re



class MemberForm(UserCreationForm):
    MEMBERSHIP_CHOICES = [
        ('S', 'Single'),
        ('D', 'Double'),
        ('L', 'LifeTime'),
        ('G', 'Gardener'),
    ]
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        required=False,
        help_text="Leave blank to keep existing password"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False
    )
    
    membership_type = forms.ChoiceField(
        choices=MEMBERSHIP_CHOICES,
        widget=forms.RadioSelect
    )
    

    class Meta:
        model = Member
        fields = [
            'first_name', 
            'last_name',
            'email',
            'phone',
            'address',
            'membership_type',
            'profile_image',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'phone': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'profile_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Member.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError("This email is already in use.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not re.match(r'^\+?[0-9]{8,15}$', phone):
            raise ValidationError("Enter a valid phone number (8-15 digits, + optional)")
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            self.add_error('confirm_password', "Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        member = super().save(commit=False)
       # if self.cleaned_data['password']:
        #    member.set_password(self.cleaned_data['password'])
        if commit:
            member.save()
            #self.save_m2m()
        return member


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        help_text="Upload a CSV file with member data. Required columns: first_name, last_name, email"
    )
    overwrite = forms.BooleanField(
        required=False,
        initial=False,
        label="Overwrite existing members",
        help_text="Check to update existing members with matching emails"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Test mode (no changes will be saved)",
        help_text="Check to validate the CSV without saving to database"
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
            raise ValidationError("File too large (max 5MB)")
        
        # Basic CSV content validation
        try:
            content = csv_file.read().decode('utf-8')
            first_line = content.splitlines()[0]
            if not all(field in content for field in ['first_name', 'last_name', 'email']):
                raise ValidationError("CSV missing required columns: first_name, last_name, email")
        except UnicodeDecodeError:
            raise ValidationError("File encoding error - please use UTF-8 encoded CSV")
        finally:
            csv_file.seek(0)  # Reset file pointer
            
        return csv_file