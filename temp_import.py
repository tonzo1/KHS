# create temp_import.py in your project root:
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Khs_membership_system.settings')
django.setup()

from members.models import Member
# Paste your import logic here