from rest_framework import serializers
from decimal import Decimal
from .models import Trip, Driver, Carrier, PlannedStop, ELDLogSheet, DutyStatusEntry
import logging

logger = logging.getLogger(__name__)

class CarrierSerializer(serializers.ModelSerializer):
    """Serializer for carrier information"""
    
    class Meta:
        model = Carrier
        fields = ['id', 'name', 'dot_number', 'main_office_address', 'operates_every_day']

class DriverSerializer(serializers.ModelSerializer):
    """Serializer for driver information"""
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    
    class Meta:
        model = Driver
        fields = ['id', 'driver_id', 'name', 'cdl_number', 'carrier', 'carrier_name', 'created_at']

class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new trips"""
    
    class Meta:
        model = Trip
        fields = ['driver', 'current_location', 'pickup_location', 'dropoff_location', 'current_cycle_hours']
    
    def validate_current_cycle_hours(self, value):
        """Validate cycle hours are within acceptable range"""
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Cycle hours cannot be negative")
        if value > Decimal('70.00'):
            raise serializers.ValidationError("Cycle hours cannot exceed 70 hours")
        return value
    
    def validate(self, data):
        """Validate trip data"""
        locations = [
            data.get('current_location', '').strip().lower(),
            data.get('pickup_location', '').strip().lower(),
            data.get('dropoff_location', '').strip().lower()
        ]
        
        if len(set(locations)) < 2:
            raise serializers.ValidationError(
                "Trip must have at least 2 different locations"
            )
        
        logger.info(f"Creating trip for driver {data['driver']} from {data['current_location']}")
        return data

class PlannedStopSerializer(serializers.ModelSerializer):
    """Serializer for planned stops"""
    stop_type_display = serializers.CharField(source='get_stop_type_display', read_only=True)
    
    class Meta:
        model = PlannedStop
        fields = [
            'id', 'stop_order', 'stop_type', 'stop_type_display', 
            'location', 'coordinates', 'estimated_arrival', 
            'estimated_departure', 'duration_minutes', 'reason'
        ]

class DutyStatusEntrySerializer(serializers.ModelSerializer):
    """Serializer for duty status entries"""
    duty_status_display = serializers.CharField(source='get_duty_status_display', read_only=True)
    
    class Meta:
        model = DutyStatusEntry
        fields = [
            'id', 'start_time', 'end_time', 'duty_status', 
            'duty_status_display', 'location', 'remarks', 'entry_order'
        ]

class ELDLogSheetSerializer(serializers.ModelSerializer):
    """Serializer for ELD log sheets"""
    duty_entries = DutyStatusEntrySerializer(many=True, read_only=True)
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    
    class Meta:
        model = ELDLogSheet
        fields = [
            'id', 'log_date', 'sheet_number', 'total_miles', 
            'vehicle_numbers', 'shipping_docs', 'off_duty_hours', 
            'sleeper_berth_hours', 'driving_hours', 'on_duty_hours',
            'duty_entries', 'driver_name', 'created_at'
        ]

class TripDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for trip information"""
    driver = DriverSerializer(read_only=True)
    planned_stops = PlannedStopSerializer(many=True, read_only=True)
    log_sheets = ELDLogSheetSerializer(many=True, read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'trip_id', 'driver', 'current_location',
            'pickup_location', 'dropoff_location', 'current_cycle_hours',
            'status', 'created_at', 'updated_at', 'planned_stops', 'log_sheets'
        ]