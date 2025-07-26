from django.core.management.base import BaseCommand
from members.models import Member
import csv
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports members from CSV into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to the CSV file')

    def clean_phone(self, phone_str):
        """Handle phone numbers including scientific notation"""
        if not phone_str or str(phone_str).lower() == 'nan':
            return None
            
        phone_str = str(phone_str).strip()
        
        if 'E+' in phone_str:
            try:
                return str(int(float(phone_str)))
            except:
                return phone_str.split('.')[0]  # Fallback for scientific notation
        return phone_str.replace(' ', '').replace('-', '').replace('+', '')

    def parse_date(self, date_str):
        """Handle date parsing more robustly"""
        if not date_str:
            return None
            
        date_str = str(date_str).strip()
        
        for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: {date_str}")

    def map_membership(self, membership):
        """Map membership types to single letters"""
        mapping = {
            'Single Membership': 'S',
            'Double Membership': 'D',
            'LifeTime Membership': 'L',
            'Gardener Membership': 'G'
        }
        return mapping.get(membership.strip(), 'S')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        
        with open(csv_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader, 1):
                try:
                    member = Member(
                           username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row['email'],
                    phone=self.clean_phone(row['Phone']),
                    alt_name=row['Alt_name'] or None,  # Handle empty Alt_name
                    membership_type=self.map_membership(row['membership_type']),
                    payment_mode=row['payment_mode'],
                    date_joined=self.parse_date(row['date_joined']),
                    renewal_date=self.parse_date(row['renewal_date']),
                    status=row['Status'],  # Now matches the model
                    contact_point=row['Contact point'],
                    member_id=row['id']   # Now matches the model
                    )
                    member.save()
                    self.stdout.write(f"Successfully imported row {i}: {row['username']}")
                except Exception as e:
                    self.stderr.write(f"Error in row {i}: {str(e)}\nRow data: {row}")