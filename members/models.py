# Khs_membership_system/members/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
#You are indeed using a Custom User Model (Member) 
# by inheriting from AbstractBaseUser and PermissionsMixin. This is excellent!
# --- Custom Manager for Member Model ---
class MemberManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields): # Add username parameter
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username: # New: check for username
            raise ValueError(_('The Username field must be set'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields) # Pass username
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields): # Add username parameter
        """
        Creates and saves a superuser with the given username, email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(username, email, password, **extra_fields) # Pass username

# --- Member Model (Your Custom User Model) ---
class Member(AbstractBaseUser, PermissionsMixin):
    MEMBERSHIP_CHOICES = [
        ('S', 'Single'),
        ('D', 'Double'),
        ('L', 'LifeTime'),
        ('G', 'Gardener'),
    ]

    objects = MemberManager()

    # --- New: Define username field ---
    #username = models.CharField(_('username'), max_length=150, unique=True,
                               # help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                               # validators=[
                               #     RegexValidator(
                               #         regex=r'^[\w.@+-]+$',
                              #         message=_('Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.')
                               #     ),
    #                            ])

    USERNAME_FIELD = 'username' # CRUCIAL: Now username is the primary login field
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name'] # email is now a required field along with first/last name

    email = models.EmailField(_('email address'), unique=False) # Email still unique
    # Removed the previous `USERNAME_FIELD = 'email'` as it's now set to 'username' above

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

    # Personal Information
    username = models.CharField(_('username'), max_length=10,unique = True,blank=True)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)
    alt_name = models.CharField(max_length=100, blank=True, null=True)
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
    payment_mode = models.CharField(max_length=50, blank=True, null=True)
    order_number = models.CharField(max_length=50, blank=True, null=True,) 
    renewal_date = models.DateField(blank=True, null=True)
    contact_point = models.CharField(max_length=100, blank=True, null=True)
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
STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Need to Renew', 'Need to Renew'),
        ('Expired', 'Expired'),
    ]
    
status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )
    
member_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Member ID'
    )
class Meta:
        verbose_name = _('member')
        verbose_name_plural = _('members')
        ordering = ['-date_joined']
        permissions = [
            ('import_member', 'Can import members'),
            ('export_member', 'Can export members'),
            ("view_history", "Can view membership history"),
            ("add_imagemodels", "Can add image models"),
            ("view_imagemodels", "Can view image models"),
            ("delete_imagemodels", "Can delete image models"),
        ]

def __str__(self):
        return f"{self.get_full_name()} ({self.username})" # Changed to username

#def get_full_name(self):
        #full_name = '%s %s' % (self.first_name, self.last_name)
        #return full_name.strip()

def get_full_name(self):
    """Return the member's full name."""
    return f"{self.first_name or ''} {self.last_name or ''}".strip()
get_full_name.short_description = 'Full Name'  # For admin display


def get_short_name(self):
        return self.first_name

def get_absolute_url(self):
        return reverse('members:detail', kwargs={'pk': self.pk})

def get_membership_type_display(self):
        return dict(self.MEMBERSHIP_CHOICES).get(self.membership_type, 'Unknown')

def get_membership_badge_color(self):
        colors = {
            'S': 'silver',
            'D': 'gold',
            'L': 'yellow',
            'G': 'bronze'
        }
        return colors.get(self.membership_type, 'light')

def profile_picture_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/static/images/default_profile.png'

# --- ImageModels (no change) ---
class ImageModels(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title or os.path.basename(self.image.name)

# --- MembershipHistory (no change) ---
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
        blank=True,
        related_name='changed_memberships'
    )
    change_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Membership Histories'
        ordering = ['-change_date']

    def __str__(self):
        return f"{self.member} changed from {self.get_previous_type_display()} to {self.get_new_type_display()}"