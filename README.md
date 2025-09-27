# SpotterAI - Transportation Management System

A Django REST API backend for managing transportation trips, drivers, carriers, and Electronic Logging Device (ELD) compliance.

## Features

- **Trip Management**: Create and track transportation trips
- **Driver Management**: Manage driver information and credentials
- **Carrier Management**: Handle carrier/company information
- **Route Calculation**: Optimize routes with planned stops
- **ELD Compliance**: Generate Electronic Logging Device reports
- **RESTful API**: Full REST API with proper serialization

## Tech Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL
- **Server**: Gunicorn
- **Deployment**: Railway
- **Containerization**: Docker

## API Endpoints

### Base URL
- **Production**: `https://your-app-name.railway.app/api/`
- **Local**: `http://localhost:8000/api/`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trips/` | List all trips |
| POST | `/api/trips/` | Create new trip |
| GET | `/api/trips/{id}/` | Get trip details |
| POST | `/api/trips/{id}/calculate_route/` | Calculate route for trip |
| GET | `/api/drivers/` | List all drivers |
| GET | `/api/drivers/{id}/` | Get driver details |
| GET | `/api/carriers/` | List all carriers |
| GET | `/api/carriers/{id}/` | Get carrier details |

## Data Models

### Trip
- Trip ID, Driver, Locations (current, pickup, dropoff)
- Cycle hours, Status, Planned stops
- Associated ELD log sheets

### Driver
- Driver ID, Name, CDL Number
- Associated Carrier, Creation timestamp

### Carrier
- Company name, DOT Number
- Main office address, Operating schedule

### Planned Stop
- Stop order, type (fuel/rest), Location
- Estimated arrival/departure, Duration, Reason

## Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/spotter-assessment.git
   cd spotter-assessment
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Make sure PostgreSQL is running
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Docker Development

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/

## Deployment

### Railway Deployment

This project is configured for automatic deployment on Railway:

1. **Connect to Railway**
   - Push code to GitHub
   - Connect repository to Railway
   - Add PostgreSQL service

2. **Environment Variables**
   - Railway automatically configures `DATABASE_URL`
   - `RAILWAY_ENVIRONMENT` is set automatically

3. **Automatic Features**
   - Auto-scaling based on traffic
   - HTTPS enabled by default
   - Continuous deployment from GitHub

## API Usage Examples

### Create a Trip
```bash
curl -X POST https://your-app-name.railway.app/api/trips/ \
  -H "Content-Type: application/json" \
  -d '{
    "driver": 1,
    "current_location": "New York, NY",
    "pickup_location": "Boston, MA", 
    "dropoff_location": "Washington, DC",
    "current_cycle_hours": "45.5"
  }'
```

### Calculate Route
```bash
curl -X POST https://your-app-name.railway.app/api/trips/TRIP123/calculate_route/ \
  -H "Content-Type: application/json"
```

### Get Trip Details
```bash
curl https://your-app-name.railway.app/api/trips/TRIP123/
```

## Project Structure

```
spotter_assessment/
├── spotter_assessment/          # Django project settings
│   ├── settings.py             # Configuration for dev/prod
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI application
├── trips/                       # Main application
│   ├── models.py               # Data models
│   ├── views.py                # API views and logic
│   ├── serializers.py          # API serialization
│   ├── services.py             # Business logic services
│   └── urls.py                 # App URL routing
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Local development setup
├── Procfile                    # Railway deployment config
└── README.md                   # This file
```

## Business Logic

### Route Calculation Service
- Optimizes routes between pickup and dropoff locations
- Generates planned stops (fuel, rest, mandatory breaks)
- Calculates total distance and estimated duration
- Considers ELD compliance requirements

### ELD Log Generation Service
- Creates compliant Electronic Logging Device records
- Tracks duty status changes (driving, on-duty, off-duty)
- Monitors Hours of Service (HOS) regulations
- Generates daily log sheets with violation tracking

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
