import googlemaps
import requests
from datetime import datetime, timedelta, time
from decimal import Decimal
from django.conf import settings
import logging
from .models import Trip, PlannedStop, ELDLogSheet, DutyStatusEntry

logger = logging.getLogger(__name__)

class RouteCalculationService:
    """Service for calculating HOS-compliant routes"""
    
    def __init__(self):
        try:
            if settings.GOOGLE_MAPS_API_KEY:
                self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
                logger.info("Google Maps client initialized successfully")
            else:
                self.gmaps = None
                logger.warning("Google Maps API key not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
            self.gmaps = None
    
    def calculate_optimized_route(self, trip):
        """Calculate route with mandatory stops for HOS compliance"""
        logger.info(f"Calculating route for trip {trip.trip_id}")
        
        try:
            # Get base route
            base_route = self._get_base_route(trip)
            
            # Calculate required stops
            required_stops = self._calculate_required_stops(base_route, trip)
            
            # Create response
            route_summary = {
                'trip_id': trip.trip_id,
                'route_coordinates': base_route.get('coordinates', []),
                'planned_stops': required_stops,
                'total_distance': base_route.get('total_distance', 0),
                'driving_time': base_route.get('total_duration', 0),
                'total_trip_time': base_route.get('total_duration', 0) + sum(s.get('duration_minutes', 0) for s in required_stops),
                'bounds': base_route.get('bounds', {}),
                'compliance_status': self._check_compliance(base_route, trip)
            }
            
            logger.info(f"Route calculation completed for trip {trip.trip_id}")
            return route_summary
            
        except Exception as e:
            logger.error(f"Error calculating route for trip {trip.trip_id}: {e}")
            # Return mock data for demo purposes
            return self._get_mock_route_data(trip)
    
    def _get_base_route(self, trip):
        """Get route information (with fallback to mock data)"""
        if not self.gmaps:
            logger.warning("Google Maps not available, using mock data")
            return self._get_mock_route_data(trip)
        
        try:
            waypoints = []
            if trip.pickup_location != trip.current_location:
                waypoints.append(trip.pickup_location)
            
            directions_result = self.gmaps.directions(
                origin=trip.current_location,
                destination=trip.dropoff_location,
                waypoints=waypoints,
                mode="driving",
                avoid=["tolls"],
                optimize_waypoints=True,
                departure_time=datetime.now()
            )
            
            if not directions_result:
                return self._get_mock_route_data(trip)
            
            route = directions_result[0]
            return self._process_google_maps_response(route)
            
        except Exception as e:
            logger.error(f"Error getting route from Google Maps: {e}")
            return self._get_mock_route_data(trip)
    
    def _get_mock_route_data(self, trip):
        """Generate mock route data for demo purposes"""
        return {
            'coordinates': [
                [-84.3880, 33.7490],  # Atlanta
                [-86.8025, 33.5186],  # Birmingham  
                [-86.7816, 36.1627]   # Nashville
            ],
            'total_distance': 485.5,
            'total_duration': 480,  # 8 hours in minutes
            'bounds': {
                'ne': {'lat': 36.1627, 'lng': -84.3880},
                'sw': {'lat': 33.5186, 'lng': -86.8025}
            }
        }
    
    def _calculate_required_stops(self, base_route, trip):
        """Calculate all required stops based on HOS regulations"""
        stops = []
        stop_order = 1
        
        # Add pickup stop
        if trip.pickup_location != trip.current_location:
            stops.append({
                'stop_type': 'pickup',
                'location': trip.pickup_location,
                'coordinates': {'lat': 33.5186, 'lng': -86.8025},
                'duration_minutes': 60,
                'reason': '1 hour for pickup activities',
                'stop_order': stop_order,
                'estimated_arrival': datetime.now() + timedelta(hours=2),
                'estimated_departure': datetime.now() + timedelta(hours=3)
            })
            stop_order += 1
        
        # Add fuel stop if over 1000 miles
        if base_route.get('total_distance', 0) > 1000:
            stops.append({
                'stop_type': 'fuel',
                'location': 'Fuel Station - Mile 500',
                'coordinates': {'lat': 34.0, 'lng': -85.5},
                'duration_minutes': 30,
                'reason': 'Fuel stop required - 1000 mile limit',
                'stop_order': stop_order,
                'estimated_arrival': datetime.now() + timedelta(hours=4),
                'estimated_departure': datetime.now() + timedelta(hours=4.5)
            })
            stop_order += 1
        
        # Add rest break if over 8 hours driving
        if base_route.get('total_duration', 0) / 60 >= 8:
            stops.append({
                'stop_type': 'rest',
                'location': 'Rest Area - Highway Rest Stop',
                'coordinates': {'lat': 35.0, 'lng': -86.0},
                'duration_minutes': 30,
                'reason': '30-minute break required after 8 hours driving',
                'stop_order': stop_order,
                'estimated_arrival': datetime.now() + timedelta(hours=6),
                'estimated_departure': datetime.now() + timedelta(hours=6.5)
            })
            stop_order += 1
        
        # Add delivery stop
        stops.append({
            'stop_type': 'delivery',
            'location': trip.dropoff_location,
            'coordinates': {'lat': 36.1627, 'lng': -86.7816},
            'duration_minutes': 60,
            'reason': '1 hour for delivery activities',
            'stop_order': stop_order,
            'estimated_arrival': datetime.now() + timedelta(hours=8),
            'estimated_departure': datetime.now() + timedelta(hours=9)
        })
        
        return stops
    
    def _check_compliance(self, route, trip):
        """Check HOS compliance"""
        total_driving_hours = route.get('total_duration', 0) / 60
        
        compliance_status = {
            'is_compliant': True,
            'violations': [],
            'warnings': []
        }
        
        if total_driving_hours > 11:
            compliance_status['is_compliant'] = False
            compliance_status['violations'].append("Driving time exceeds 11-hour limit")
        
        projected_cycle_hours = float(trip.current_cycle_hours) + total_driving_hours + 3  # Add estimated on-duty time
        if projected_cycle_hours > 70:
            compliance_status['is_compliant'] = False
            compliance_status['violations'].append("Trip would exceed 70-hour/8-day cycle limit")
        
        return compliance_status

class ELDLogGenerationService:
    """Service for generating compliant ELD log sheets"""
    
    def generate_log_sheets(self, trip, route_data):
        """Generate ELD log sheets for the trip"""
        logger.info(f"Generating ELD logs for trip {trip.trip_id}")
        
        try:
            log_sheet_data = self._create_single_day_log(trip, route_data)
            
            log_sheet = ELDLogSheet.objects.create(
                trip=trip,
                driver=trip.driver,
                log_date=datetime.now().date(),
                sheet_number=1,
                total_miles=Decimal(str(route_data.get('total_distance', 485.5))),
                vehicle_numbers="TRK-001",
                shipping_docs="Load #12345",
                off_duty_hours=log_sheet_data['off_duty_hours'],
                sleeper_berth_hours=log_sheet_data['sleeper_berth_hours'],
                driving_hours=log_sheet_data['driving_hours'],
                on_duty_hours=log_sheet_data['on_duty_hours']
            )
            
            # Create duty status entries
            for entry_data in log_sheet_data['duty_entries']:
                DutyStatusEntry.objects.create(
                    log_sheet=log_sheet,
                    **entry_data
                )
            
            logger.info(f"Generated ELD log sheet for trip {trip.trip_id}")
            return [log_sheet]
            
        except Exception as e:
            logger.error(f"Error generating ELD logs for trip {trip.trip_id}: {e}")
            raise
    
    def _create_single_day_log(self, trip, route_data):
        """Create a single day's ELD log data"""
        duty_entries = []
        
        # Sample duty entries for demonstration
        duty_entries = [
            {
                'start_time': time(0, 0),
                'end_time': time(6, 0),
                'duty_status': 'off_duty',
                'location': trip.current_location,
                'remarks': f'Off duty, {trip.current_location}',
                'entry_order': 1
            },
            {
                'start_time': time(6, 0),
                'end_time': time(7, 0),
                'duty_status': 'on_duty',
                'location': trip.current_location,
                'remarks': f'Pre-trip inspection, {trip.current_location}',
                'entry_order': 2
            },
            {
                'start_time': time(7, 0),
                'end_time': time(15, 0),
                'duty_status': 'driving',
                'location': f"En route to {trip.dropoff_location}",
                'remarks': f"Driving to {trip.dropoff_location}",
                'entry_order': 3
            },
            {
                'start_time': time(15, 0),
                'end_time': time(16, 0),
                'duty_status': 'on_duty',
                'location': trip.dropoff_location,
                'remarks': f'Delivery, {trip.dropoff_location}',
                'entry_order': 4
            },
            {
                'start_time': time(16, 0),
                'end_time': time(23, 59),
                'duty_status': 'off_duty',
                'location': trip.dropoff_location,
                'remarks': f'Off duty, {trip.dropoff_location}',
                'entry_order': 5
            }
        ]
        
        return {
            'duty_entries': duty_entries,
            'off_duty_hours': Decimal('14.00'),
            'sleeper_berth_hours': Decimal('0.00'),
            'driving_hours': Decimal('8.00'),
            'on_duty_hours': Decimal('2.00')
        }