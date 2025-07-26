from django.urls import path
from .views import (
    dashboard,
    MemberListView,
    MemberCreateView,
    MemberDetailView,
    MemberUpdateView,
    MemberDeleteView,
    import_csv,
    export_csv,
    image_upload,
    image_list,   # <--- UNCOMMENT THIS LINE
    image_delete, # <--- UNCOMMENT THIS LINE
)

# IMPORTANT: Import Django's built-in authentication views
from django.contrib.auth import views as auth_views

app_name = 'members'  # Namespace declaration

urlpatterns = [
    # AUTHENTICATION URLs (Crucial for fixing the 404 for login)
    path('login/', auth_views.LoginView.as_view(template_name='members/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Dashboard
    path('', dashboard, name='dashboard'), # This makes '/members/' go to dashboard

    # Member CRUD
    path('list/', MemberListView.as_view(), name='list'),
    path('create/', MemberCreateView.as_view(), name='create'),
    path('<int:pk>/', MemberDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', MemberUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', MemberDeleteView.as_view(), name='delete'),

    # Image Upload
    path('upload-image/', image_upload, name='image_upload'),

    # CSV Handling
    path('import/', import_csv, name='import'),
    path('export/', export_csv, name='export'),

    # Add these if you want to manage generic images with image_list and image_delete views
    path('images/', image_list, name='image_list'),           # <--- UNCOMMENT THIS LINE
    path('images/<int:pk>/delete/', image_delete, name='image_delete'), # <--- UNCOMMENT THIS LINE
]