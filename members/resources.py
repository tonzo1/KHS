from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.widgets import DateTimeWidget, DateWidget ,ManyToManyWidget# Import the necessary widget
from .models import Member, MembershipHistory, ImageModels

class MemberResource(resources.ModelResource):
    # If you want to customize how certain fields are imported/exported
    # For example, if you want to ensure membership_expiry is parsed correctly
    # or if you want to handle related fields in a specific way.

    date_joined = fields.Field(widget=DateWidget(format='%d/%m/%Y'))
    renewal_date = fields.Field(widget=DateWidget(format='%m/%d/%Y'))
       
    

    class Meta:
        model = Member
        model = Member
        import_id_fields = ('member_id',)
        skip_unchanged = True
        fields = (
            'member_id', 'username', 'first_name', 'last_name',
            'email', 'phone', 'membership_type', 'payment_mode',
            'date_joined', 'renewal_date', 'status', 'contact_point'
        )
        # Specify the fields you want to import/export.
        # It's good practice to explicitly list them for clarity and control.
        # Include all fields you expect in your CSV.

        fields = (
            #'id', # Often useful for updates, but can be excluded for pure imports
            'username',
            'email',
            'first_name',
            'last_name',
            #'phone',
            #'address',
            'membership_type',
            'date_joined',
            #'membership_expiry',
            #'alt_name',       # Assuming these new fields exist on your Member model
            #'payment_mode',   # If they don't, you'll need to add them to models.py
            #'order_number',   # and run makemigrations/migrate.
            'renewal_date',
            #'contact_point',
             'notes',
            # 'profile_image', # Image fields can be tricky to import via CSV directly.
                              # You might need custom logic or leave it out for CSV.
                              # For export, it would just export the path/filename.
            #'notes',
            #'is_active',
            #'is_staff',
            #'is_superuser',
        )
        # Optional: Define the order of fields in the exported CSV
        export_order = (
            #'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'address',
            'membership_type',
            'membership_expiry',
            'date_joined',
            'notes',
            'alt_name',
            'payment_mode'
            #'order_number'
            'renewal_date'
            'contact_point'
            #'is_active',
            #'is_staff',
            #'is_superuser',
        )
        # Specify fields to identify existing records for update/skip during import.
        # For Member, 'username' or 'email' are good unique identifiers.
        import_id_fields = ('username',) # Use 'username' as the unique identifier for imports
        # If you prefer email as primary ID for import: import_id_fields = ('email',)
        # If both are unique and you want to use either: import_id_fields = ('username', 'email')
        # However, it's usually best to pick one primary for import_id_fields.

        # Control import behavior for existing records
        skip_unchanged = True  # Don't update rows if data is identical
        report_skipped = True  # Report rows that were skipped

# You can define resources for other models too, if you need to import/export them.
class MembershipHistoryResource(resources.ModelResource):
    # To handle ForeignKey fields correctly, especially for import:
    member = fields.Field(
        column_name='member_username', # Column header in CSV
        attribute='member',
        widget=ForeignKeyWidget(Member, 'username') # Link to Member model using 'username' field
    )
    changed_by = fields.Field(
        column_name='changed_by_username', # Column header in CSV
        attribute='changed_by',
        widget=ForeignKeyWidget(Member, 'username')
    )

    class Meta:
        model = MembershipHistory
        fields = (
            'id', 'member', 'previous_type', 'new_type', 'changed_by',
            'change_date', 'reason',
        )
        export_order = (
            'id', 'member_username', 'previous_type', 'new_type',
            'changed_by_username', 'change_date', 'reason',
        )
        # For imports, 'id' is often good for existing records if you're updating.
        # If you're only creating new history entries, 'id' might be omitted.
        import_id_fields = ('id',) # Or if you don't care about updates, omit and new ones will be created.

class ImageModelsResource(resources.ModelResource):
    class Meta:
        model = ImageModels
        fields = ('id', 'title', 'image', 'uploaded_at')
        export_order = ('id', 'title', 'image', 'uploaded_at')
        import_id_fields = ('id',)
        # Note: Importing image files themselves via CSV is generally not straightforward.
        # The 'image' field here would refer to the path/filename, not the binary data.
        # For images, you typically upload them separately and then update the database with paths.