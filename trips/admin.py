from django.contrib import admin

# Register your models here.
from .models import Carrier, Driver, Trip, PlannedStop, ELDLogSheet, DutyStatusEntry

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'dot_number', 'operates_every_day', 'created_at']
    list_filter = ['operates_every_day', 'created_at']
    search_fields = ['name', 'dot_number']

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'driver_id', 'cdl_number', 'carrier', 'created_at']
    list_filter = ['carrier', 'created_at']
    search_fields = ['name', 'driver_id', 'cdl_number']

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['trip_id', 'driver', 'status', 'current_cycle_hours', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['trip_id', 'driver__name']
    readonly_fields = ['trip_id', 'created_at', 'updated_at']

@admin.register(PlannedStop)
class PlannedStopAdmin(admin.ModelAdmin):
    list_display = ['trip', 'stop_type', 'location', 'stop_order', 'duration_minutes']
    list_filter = ['stop_type', 'trip__status']
    search_fields = ['trip__trip_id', 'location']

@admin.register(ELDLogSheet)
class ELDLogSheetAdmin(admin.ModelAdmin):
    list_display = ['log_date', 'driver', 'sheet_number', 'driving_hours', 'total_miles']
    list_filter = ['log_date', 'driver']
    search_fields = ['driver__name', 'trip__trip_id']

@admin.register(DutyStatusEntry)
class DutyStatusEntryAdmin(admin.ModelAdmin):
    list_display = ['log_sheet', 'duty_status', 'start_time', 'end_time', 'location']
    list_filter = ['duty_status', 'log_sheet__log_date']
    search_fields = ['location', 'remarks']