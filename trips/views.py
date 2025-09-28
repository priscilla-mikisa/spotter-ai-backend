from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Trip, Driver, Carrier
from .serializers import (
    TripCreateSerializer, 
    TripDetailSerializer, 
    DriverSerializer, 
    CarrierSerializer
)
from .services import RouteCalculationService, ELDLogGenerationService
import logging

logger = logging.getLogger(__name__)

class CarrierViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier information"""
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Trip, Driver, Carrier
from .serializers import (
    TripCreateSerializer, 
    TripDetailSerializer, 
    DriverSerializer, 
    CarrierSerializer
)
from .services import RouteCalculationService, ELDLogGenerationService
import logging

logger = logging.getLogger(__name__)

class CarrierViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier information"""
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer

class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for driver information"""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

class TripViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trips"""
    queryset = Trip.objects.all()
    lookup_field = 'trip_id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return TripCreateSerializer
        return TripDetailSerializer
    
    def create(self, request):
        """Create a new trip"""
        logger.info("Creating new trip")
        
        serializer = TripCreateSerializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save()
            logger.info(f"Trip created successfully: {trip.trip_id}")
            
            # Return detailed trip information
            detail_serializer = TripDetailSerializer(trip)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        logger.error(f"Trip creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def calculate_route(self, request, trip_id=None):
        """Calculate route for a specific trip"""
        trip = get_object_or_404(Trip, trip_id=trip_id)
        logger.info(f"Calculating route for trip {trip_id}")
        
        try:
            # Update trip status
            trip.status = 'calculating'
            trip.save()
            
            # Calculate route
            route_service = RouteCalculationService()
            route_data = route_service.calculate_optimized_route(trip)
            
            # Save planned stops
            self._save_planned_stops(trip, route_data.get('planned_stops', []))
            
            # Generate ELD logs
            eld_service = ELDLogGenerationService()
            log_sheets = eld_service.generate_log_sheets(trip, route_data)
            
            # Update trip status
            trip.status = 'calculated'
            trip.save()
            
            logger.info(f"Route calculation completed for trip {trip_id}")
            
            return Response({
                'success': True,
                'message': 'Route calculated successfully',
                'route_data': route_data,
                'log_sheets_generated': len(log_sheets)
            })
            
        except Exception as e:
            trip.status = 'error'
            trip.save()
            logger.error(f"Error calculating route for trip {trip_id}: {e}")
            
            return Response({
                'success': False,
                'message': f'Route calculation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _save_planned_stops(self, trip, stops_data):
        """Save planned stops to database"""
        from .models import PlannedStop
        
        # Clear existing stops
        trip.planned_stops.all().delete()
        
        # Create new stops
        for stop_data in stops_data:
            PlannedStop.objects.create(
                trip=trip,
                stop_order=stop_data.get('stop_order', 0),
                stop_type=stop_data.get('stop_type', 'fuel'),
                location=stop_data.get('location', ''),
                coordinates=stop_data.get('coordinates', {}),
                estimated_arrival=stop_data.get('estimated_arrival'),
                estimated_departure=stop_data.get('estimated_departure'),
                duration_minutes=stop_data.get('duration_minutes', 0),
                reason=stop_data.get('reason', '')
            )

    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer

class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for driver information"""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

class TripViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trips"""
    queryset = Trip.objects.all()
    lookup_field = 'trip_id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return TripCreateSerializer
        return TripDetailSerializer
    
    def create(self, request):
        """Create a new trip"""
        logger.info("Creating new trip")
        
        serializer = TripCreateSerializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save()
            logger.info(f"Trip created successfully: {trip.trip_id}")
            
            # Return detailed trip information
            detail_serializer = TripDetailSerializer(trip)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        logger.error(f"Trip creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def calculate_route(self, request, trip_id=None):
        """Calculate route for a specific trip"""
        trip = get_object_or_404(Trip, trip_id=trip_id)
        logger.info(f"Calculating route for trip {trip_id}")
        
        try:
            # Update trip status
            trip.status = 'calculating'
            trip.save()
            
            # Calculate route
            route_service = RouteCalculationService()
            route_data = route_service.calculate_optimized_route(trip)
            
            # Save planned stops
            self._save_planned_stops(trip, route_data.get('planned_stops', []))
            
            # Generate ELD logs
            eld_service = ELDLogGenerationService()
            log_sheets = eld_service.generate_log_sheets(trip, route_data)
            
            # Update trip status
            trip.status = 'calculated'
            trip.save()
            
            logger.info(f"Route calculation completed for trip {trip_id}")
            
            return Response({
                'success': True,
                'message': 'Route calculated successfully',
                'route_data': route_data,
                'log_sheets_generated': len(log_sheets)
            })
            
        except Exception as e:
            trip.status = 'error'
            trip.save()
            logger.error(f"Error calculating route for trip {trip_id}: {e}")
            
            return Response({
                'success': False,
                'message': f'Route calculation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _save_planned_stops(self, trip, stops_data):
        """Save planned stops to database"""
        from .models import PlannedStop
        
        # Clear existing stops
        trip.planned_stops.all().delete()
        
        # Create new stops
        for stop_data in stops_data:
            PlannedStop.objects.create(
                trip=trip,
                stop_order=stop_data.get('stop_order', 0),
                stop_type=stop_data.get('stop_type', 'fuel'),
                location=stop_data.get('location', ''),
                coordinates=stop_data.get('coordinates', {}),
                estimated_arrival=stop_data.get('estimated_arrival'),
                estimated_departure=stop_data.get('estimated_departure'),
                duration_minutes=stop_data.get('duration_minutes', 0),
                reason=stop_data.get('reason', '')
            )
