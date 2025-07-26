from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from .models import Member, MembershipHistory, ImageModels
from .forms import MemberForm
from .resources import MemberResource, MembershipHistoryResource, ImageModelsResource

@admin.register(Member)
class MemberAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = MemberResource
    form = MemberForm
    
    # Use either the model's get_full_name or an admin method, not both
    list_display = ('username', 'email', 'membership_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('membership_type', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    # Fieldsets for edit page
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image', 'notes')}),
        ('Membership info', {'fields': ('membership_type', 'membership_expiry', 'member_id', 'status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('date_joined', 'last_login', 'renewal_date')}),
    )
    
    # Fieldsets for add page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image')}),
        ('Membership info', {'fields': ('membership_type', 'member_id', 'status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    readonly_fields = ('date_joined', 'last_login')

@admin.register(MembershipHistory)
class MembershipHistoryAdmin(ImportExportModelAdmin):
    resource_class = MembershipHistoryResource
    list_display = ('member', 'previous_type', 'new_type', 'changed_by', 'change_date')
    search_fields = ('member__username', 'member__email', 'changed_by__username', 'changed_by__email')
    list_filter = ('previous_type', 'new_type', 'change_date')
    raw_id_fields = ('member', 'changed_by')

@admin.register(ImageModels)
class ImageModelsAdmin(ImportExportModelAdmin):
    resource_class = ImageModelsResource
    list_display = ('title', 'image_preview', 'uploaded_at')
    search_fields = ('title',)
    list_filter = ('uploaded_at',)
    
    def image_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Preview'