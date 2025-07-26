from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from django.urls import path, include


urlpatterns = [
    # Admin site
    
    path('grappelli/', include('grappelli.urls')), # Grappelli URLS
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    
    # Members app - simplified include
    path('members/', include('members.urls')),  # Remove namespace here
    
    # Authentication
    path('accounts/', include([
        path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
        path('logout/', auth_views.LogoutView.as_view(), name='logout'),
        path('accounts/', include('django.contrib.auth.urls')), 
        path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
        path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
        path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
        path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
        
    
    ])),
    
    # Root redirect - point to a specific URL instead of named pattern
    path('', RedirectView.as_view(url='/members/'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)