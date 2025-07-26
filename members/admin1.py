from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from .models import Member, MembershipHistory, ImageModels
from .forms import MemberForm
from .resources import MemberResource

@admin.register(Member)
class MemberAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = MemberResource
    form = MemberForm
    
    # List display configuration
    list_display = ('email', 'first_name', 'last_name', 'membership_type', 'is_staff', 'is_active')
    list_filter = ('membership_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'membership_type')
    ordering = ('-date_joined',)
    
    # Fieldsets for editing user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image')}),
        ('Membership info', {'fields': ('membership_type', 'membership_expiry')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates & Notes', {'fields': ('date_joined', 'last_login', 'notes')}),
    )
    
    # Fieldsets for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image')
        }),
        ('Membership info', {
            'fields': ('membership_type',)
        }),
        ('Additional Notes', {
            'fields': ('notes',)
        }),
    )

@admin.register(MembershipHistory)
class MembershipHistoryAdmin(admin.ModelAdmin):
    list_display = ('member', 'previous_membership_type', 'new_membership_type', 'change_date')
    list_filter = ('change_date', 'previous_membership_type', 'new_membership_type')
    search_fields = ('member__email', 'member__first_name', 'member__last_name')

@admin.register(ImageModels)
class ImageModelsAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'uploaded_by__email')