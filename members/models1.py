from django.db import models
#Import AbstractBaseUser and BaseUserManager for custom user model with email as username
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # Good practice for translatable strings
import os # For the upload path function

# --- Custom Manager for Member Model ---
class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusers should always be active by default

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

# --- Member Model (Your Custom User Model) ---
class Member(AbstractBaseUser, PermissionsMixin):
    MEMBERSHIP_CHOICES = [
        ('S', 'Single'),
        ('D', 'Double'),
        ('L', 'LifeTime'),
        ('G', 'Gardener'),
    ]

    
    objects = MemberManager()


    # Don't define 'username = None'. AbstractBaseUser doesn't have a username field by default.
    # We define our USERNAME_FIELD below.
    USERNAME_FIELD = 'email' # THIS LINE IS CRUCIAL
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Or whatever fields you want to be required beyond USERNAME_FIELD and password

    email = models.EmailField(_('email address'), unique=True)
    

        # Explicitly define is_active, is_staff, is_superuser fields
    # These typically come from AbstractUser, but with AbstractBaseUser + PermissionsMixin
    # it's best to define them explicitly for admin compatibility.
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )

    # ... (rest of your Member model, including objects = MemberManager()) ...


    # Personal Information
    first_name = models.CharField(_('first name'), max_length=50, blank=True) # Added blank=True for first/last name
    last_name = models.CharField(_('last name'), max_length=50, blank=True) # as they are in REQUIRED_FIELDS
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{8,15}$',
                message="Phone number must be 8-15 digits, with optional + prefix"
            )
        ]
    )
    address = models.TextField(_('address'), blank=True, null=True)
    
    # Membership Information
    membership_type = models.CharField(
        _('membership type'),
        max_length=1,
        choices=MEMBERSHIP_CHOICES,
        default='S'
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    membership_expiry = models.DateField(_('membership expiry'), blank=True, null=True)
    
    # Additional Fields
    profile_image = models.ImageField(
        _('profile image'),
        upload_to='members/profile_images/',
        blank=True,
        null=True,
        help_text="Upload a profile picture for this member"
    )
    
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    # is_active, is_staff, is_superuser are already part of PermissionsMixin
    # No need to redefine them unless you want to change their defaults or help_texts.
    # If you redefine, ensure they are also set in create_superuser.
    # is_active = models.BooleanField(default=True) # No need, inherited from AbstractBaseUser (via PermissionsMixin)

    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS for createsuperuser will automatically ask for first_name and last_name
    # if they are not explicitly set in the create_superuser method.
    REQUIRED_FIELDS = ['first_name', 'last_name'] # These will be prompted during createsuperuser

    # Assign your custom manager to the objects attribute
    objects = MemberManager()

    class Meta:
        verbose_name = _('member') # Use _() for translatability
        verbose_name_plural = _('members') # Use _() for translatability
        ordering = ['-date_joined']
        permissions = [
            ('import_member', 'Can import members'),
            ('export_member', 'Can export members'),
            ("view_history", "Can view membership history"), # Added from previous context
            ("add_imagemodels", "Can add image models"),      # Added from previous context
            ("view_imagemodels", "Can view image models"),    # Added from previous context
            ("delete_imagemodels", "Can delete image models"),# Added from previous context
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def get_absolute_url(self):
        return reverse('members:detail', kwargs={'pk': self.pk})

    def get_membership_type_display(self):
        return dict(self.MEMBERSHIP_CHOICES).get(self.membership_type, 'Unknown')

    def get_membership_badge_color(self):
        colors = {
            'S': 'secondary',
            'D': 'primary',
            'L': 'success',
            'G': 'secondary'
        }
        return colors.get(self.membership_type, 'light')

    # Corrected profile_picture_url method
    def profile_picture_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/static/images/default_profile.png' # Ensure this path is correct in your static files

    # Remove the custom save method, as it's causing issues and is not needed with AbstractBaseUser
    # and a proper custom manager. AbstractBaseUser handles email normalization etc.
    # def save(self, *args, **kwargs):
    #     self.email = self.email.lower()
    #     self.username = self.email # <--- Remove this, username field doesn't exist
    #     super().save(*args, **kwargs)


# --- ImageModels (Remains mostly the same, ensure upload_to matches configuration) ---
class ImageModels(models.Model):
    title = models.CharField(max_length=255, blank=True) # title can be blank
    image = models.ImageField(upload_to='images/')  # Image will be uploaded to 'media/images/'
    uploaded_at = models.DateTimeField(default=timezone.now)  # Timestamp of the upload

    def __str__(self):
        return self.title or os.path.basename(self.image.name) # Better string representation

# --- MembershipHistory (Remains mostly the same) ---
class MembershipHistory(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='membership_history'
    )
    previous_type = models.CharField(
        max_length=1,
        choices=Member.MEMBERSHIP_CHOICES
    )
    new_type = models.CharField(
        max_length=1,
        choices=Member.MEMBERSHIP_CHOICES
    )
    changed_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow blank for 'changed_by' if user is deleted or not set
        related_name='changed_memberships'
    )
    change_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Membership Histories'
        ordering = ['-change_date']

    def __str__(self):
        return f"{self.member} changed from {self.get_previous_type_display()} to {self.get_new_type_display()}"


# --- Removed unused profile_picture_upload_path function and commented out old Member class snippet ---
# The profile_image field now correctly points to 'members/profile_images/' directly.
# The `profile_picture_upload_path` function was defined but not used in the Member model.
# If you want dynamic paths based on instance.pk, you need to set `upload_to=profile_picture_upload_path`.
# For now, keeping it simple as `upload_to='members/profile_images/'` is fine.