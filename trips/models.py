from django.db import models

# Create your models here.
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)

class Carrier(models.Model):
    """Motor carrier information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Carrier company name")
    dot_number = models.CharField(max_length=20, help_text="DOT number")
    main_office_address = models.TextField(help_text="Main office address")
    operates_every_day = models.BooleanField(
        default=True, 
        help_text="True for 70hr/8day rule, False for 60hr/7day rule"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'carriers'
        verbose_name = 'Carrier'
        verbose_name_plural = 'Carriers'
    
    def __str__(self):
        return self.name

class Driver(models.Model):
    """Driver information for ELD compliance tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver_id = models.CharField(max_length=50, unique=True, help_text="Unique driver identifier")
    name = models.CharField(max_length=100, help_text="Driver's full name")
    cdl_number = models.CharField(max_length=50, help_text="Commercial Driver's License number")
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name='drivers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drivers'
        ordering = ['name']
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'
    
    def __str__(self):
        return f"{self.name} ({self.driver_id})"

class Trip(models.Model):
    """Trip planning and tracking"""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('calculating', 'Calculating Route'),
        ('calculated', 'Route Calculated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip_id = models.CharField(max_length=50, unique=True, help_text="Unique trip identifier")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trips')
    current_location = models.CharField(max_length=500, help_text="Starting location address")
    pickup_location = models.CharField(max_length=500, help_text="Pickup location address")
    dropoff_location = models.CharField(max_length=500, help_text="Delivery location address")
    current_cycle_hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('70.00'))],
        help_text="Hours used in current 8-day cycle (0-70)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trips'
        ordering = ['-created_at']
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'
    
    def save(self, *args, **kwargs):
        if not self.trip_id:
            self.trip_id = f"TRP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        logger.info(f"Trip saved: {self.trip_id} - Status: {self.status}")
    
    def __str__(self):
        return f"Trip {self.trip_id} - {self.driver.name}"

class PlannedStop(models.Model):
    """Planned stops along the route for HOS compliance"""
    STOP_TYPES = [
        ('fuel', 'Fuel Stop'),
        ('rest', 'Mandatory Rest Break'),
        ('pickup', 'Pickup Location'),
        ('delivery', 'Delivery Location'),
        ('sleeper', 'Sleeper Berth Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='planned_stops')
    stop_order = models.IntegerField(help_text="Order of stop in sequence")
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    location = models.CharField(max_length=500, help_text="Stop location address")
    coordinates = models.JSONField(help_text="Latitude and longitude coordinates")
    estimated_arrival = models.DateTimeField(help_text="Estimated arrival time")
    estimated_departure = models.DateTimeField(help_text="Estimated departure time")
    duration_minutes = models.IntegerField(help_text="Stop duration in minutes")
    reason = models.TextField(help_text="HOS compliance reason for stop")
    
    class Meta:
        db_table = 'planned_stops'
        ordering = ['trip', 'stop_order']
        verbose_name = 'Planned Stop'
        verbose_name_plural = 'Planned Stops'
    
    def __str__(self):
        return f"{self.get_stop_type_display()} - {self.location}"

class ELDLogSheet(models.Model):
    """Electronic Logging Device daily log sheet"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='log_sheets')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='log_sheets')
    log_date = models.DateField(help_text="Date of log sheet")
    sheet_number = models.IntegerField(help_text="Sheet number for multi-day trips")
    total_miles = models.DecimalField(max_digits=6, decimal_places=1, help_text="Total miles driven")
    vehicle_numbers = models.CharField(max_length=100, help_text="Vehicle identification numbers")
    shipping_docs = models.TextField(help_text="Shipping document information")
    
    # Hour totals (must sum to 24.0)
    off_duty_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    sleeper_berth_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    driving_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    on_duty_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eld_log_sheets'
        ordering = ['log_date', 'sheet_number']
        verbose_name = 'ELD Log Sheet'
        verbose_name_plural = 'ELD Log Sheets'
    
    def __str__(self):
        return f"Log {self.log_date} - {self.driver.name} (Sheet {self.sheet_number})"

class DutyStatusEntry(models.Model):
    """Individual duty status entries for log sheet"""
    DUTY_STATUS_CHOICES = [
        ('off_duty', 'Off Duty'),
        ('sleeper_berth', 'Sleeper Berth'),
        ('driving', 'Driving'),
        ('on_duty', 'On Duty (Not Driving)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    log_sheet = models.ForeignKey(ELDLogSheet, on_delete=models.CASCADE, related_name='duty_entries')
    start_time = models.TimeField(help_text="Start time of duty status")
    end_time = models.TimeField(help_text="End time of duty status")
    duty_status = models.CharField(max_length=20, choices=DUTY_STATUS_CHOICES)
    location = models.CharField(max_length=500, help_text="Location during this duty status")
    remarks = models.TextField(help_text="Remarks for this duty period")
    entry_order = models.IntegerField(help_text="Order of entry in the log")
    
    class Meta:
        db_table = 'duty_status_entries'
        ordering = ['log_sheet', 'entry_order']
        verbose_name = 'Duty Status Entry'
        verbose_name_plural = 'Duty Status Entries'
    
    def __str__(self):
        return f"{self.get_duty_status_display()}: {self.start_time}-{self.end_time}"