# Razorpay eMandate API

A production-grade FastAPI application for implementing Razorpay eMandate recurring payments with comprehensive features including async task processing, request/response logging, and standardized API responses.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **Async Task Processing**: Celery integration for background tasks
- **Database**: SQLAlchemy with MySQL support and Alembic migrations
- **Request/Response Logging**: Comprehensive API logging with structured logs
- **Standardized Responses**: Consistent API response format
- **Mock Mode**: Development mode with mock Razorpay responses
- **Production Ready**: Docker support, proper error handling, and monitoring
- **eMandate Support**: Complete Razorpay eMandate implementation

## Project Structure

```
razorpay-emandate/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── customers.py
│   │       │   ├── mandates.py
│   │       │   ├── payments.py
│   │       │   ├── emandate.py
│   │       │   └── webhooks.py
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── celery_app.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   ├── services/
│   │   ├── database_service.py
│   │   └── razorpay_service.py
│   ├── tasks/
│   │   ├── emandate_tasks.py
│   │   └── webhook_tasks.py
│   ├── utils/
│   │   └── helpers.py
│   └── main.py
├── alembic/
├── tests/
├── logs/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd razorpay-emandate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Set up database**
   ```bash
   # Create MySQL database
   mysql -u root -p -e "CREATE DATABASE razorpay_emandate;"
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start Redis** (if not using Docker)
   ```bash
   redis-server
   ```

### Running the Application

#### Option 1: Local Development

1. **Start the API server**
   ```bash
   python main.py
   # OR
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Celery worker** (in another terminal)
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

3. **Start Celery beat** (in another terminal, optional)
   ```bash
   celery -A app.core.celery_app beat --loglevel=info
   ```

#### Option 2: Docker

```bash
docker-compose up -d
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/docs` - API documentation

### Customer Management

- `POST /api/v1/customers/` - Create customer
- `GET /api/v1/customers/{id}` - Get customer
- `PUT /api/v1/customers/{id}` - Update customer
- `GET /api/v1/customers/` - List customers

### Mandate Management

- `POST /api/v1/mandates/` - Create mandate
- `GET /api/v1/mandates/{id}` - Get mandate
- `PUT /api/v1/mandates/{id}` - Update mandate
- `GET /api/v1/mandates/customer/{customer_id}` - List customer mandates

### Payment Operations

- `POST /api/v1/payments/orders` - Create order
- `POST /api/v1/payments/` - Create payment
- `GET /api/v1/payments/{id}` - Get payment
- `GET /api/v1/payments/customer/{customer_id}` - List customer payments

### eMandate Operations

- `POST /api/v1/emandate/authorize` - Authorize eMandate
- `POST /api/v1/emandate/recurring-payment` - Create recurring payment
- `POST /api/v1/emandate/validate-mandate/{mandate_id}` - Validate mandate
- `GET /api/v1/emandate/mandate-status/{mandate_id}` - Get mandate status

### Webhook Handling

- `POST /api/v1/webhooks/razorpay` - Razorpay webhook endpoint
- `GET /api/v1/webhooks/events/{event_id}` - Get webhook event
- `GET /api/v1/webhooks/events` - List webhook events

## API Usage Examples

### 1. Create Customer

```bash
curl -X POST "http://localhost:8000/api/v1/customers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "contact": "9876543210",
    "gstin": "29ABCDE1234F1Z5"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Customer created successfully",
  "timestamp": 1698765432.123,
  "data": {
    "customer": {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "contact": "9876543210",
      "gstin": "29ABCDE1234F1Z5",
      "razorpay_customer_id": "cust_mock_1",
      "created_at": "2023-10-31T12:30:32"
    }
  }
}
```

### 2. Authorize eMandate

```bash
curl -X POST "http://localhost:8000/api/v1/emandate/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "amount": 1000.00,
    "frequency": "monthly",
    "description": "Monthly subscription payment",
    "notes": {
      "plan": "premium"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "eMandate authorization initiated successfully",
  "timestamp": 1698765432.123,
  "data": {
    "mandate_id": 1,
    "task_id": "task-uuid-here",
    "status": "processing",
    "customer_id": 1
  }
}
```

### 3. Create Recurring Payment

```bash
curl -X POST "http://localhost:8000/api/v1/emandate/recurring-payment" \
  -H "Content-Type: application/json" \
  -d '{
    "mandate_id": 1,
    "amount": 500.00,
    "description": "Monthly subscription charge",
    "receipt": "receipt_001"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Recurring payment initiated successfully",
  "timestamp": 1698765432.123,
  "data": {
    "mandate_id": 1,
    "task_id": "task-uuid-here",
    "status": "processing",
    "amount": 500.0
  }
}
```

### 4. Get Mandate Status

```bash
curl -X GET "http://localhost:8000/api/v1/emandate/mandate-status/1"
```

**Response:**
```json
{
  "success": true,
  "message": "Mandate status retrieved successfully",
  "timestamp": 1698765432.123,
  "data": {
    "mandate_id": 1,
    "status": "confirmed",
    "razorpay_mandate_id": "mandate_mock_1",
    "amount": 1000.0,
    "currency": "INR",
    "frequency": "monthly"
  }
}
```

### 5. Handle Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/razorpay" \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: signature-here" \
  -d '{
    "event": "payment.captured",
    "account_id": "acc_00000000000001",
    "entity": {
      "id": "pay_00000000000001",
      "amount": 50000,
      "currency": "INR",
      "status": "captured"
    },
    "contains": ["payment"],
    "created_at": 1698765432
  }'
```

## eMandate Flow

### 1. Authorization Flow

1. **Create Customer**: Register customer in the system
2. **Authorize eMandate**: Create mandate and initiate authorization
3. **Customer Authorization**: Customer authorizes the mandate (handled by Razorpay)
4. **Webhook Processing**: Receive and process authorization confirmation

### 2. Recurring Payment Flow

1. **Validate Mandate**: Ensure mandate is active and confirmed
2. **Create Recurring Payment**: Initiate payment using the mandate
3. **Payment Processing**: Razorpay processes the payment automatically
4. **Webhook Handling**: Receive payment status updates

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/razorpay_emandate
TEST_DATABASE_URL=mysql+pymysql://user:password@localhost:3306/razorpay_emandate_test

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Application Configuration
APP_NAME=Razorpay eMandate API
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Database Schema

### Core Tables

- **customers**: Customer information and Razorpay customer IDs
- **mandates**: eMandate details and authorization status
- **payments**: Payment records and transaction details
- **orders**: Razorpay order information
- **webhook_events**: Webhook event processing log
- **api_logs**: API request/response logging

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding New Features

1. Add models in `app/models/models.py`
2. Create schemas in `app/schemas/schemas.py`
3. Implement services in `app/services/`
4. Add API endpoints in `app/api/v1/endpoints/`
5. Create Celery tasks in `app/tasks/`
6. Write tests in `tests/`

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery=3
```

### Environment Setup

1. Set up production database (MySQL)
2. Configure Redis for production
3. Set up reverse proxy (Nginx)
4. Configure monitoring (Prometheus/Grafana)
5. Set up log aggregation (ELK stack)

### Security Considerations

- Use strong SECRET_KEY in production
- Enable HTTPS with SSL certificates
- Configure CORS properly
- Validate webhook signatures
- Implement rate limiting
- Use environment variables for sensitive data

## Monitoring

### Health Checks

- API health: `GET /health`
- Database connectivity check
- Redis connectivity check
- Celery worker status

### Logging

- Structured logging with JSON format
- Request/response logging
- Error tracking
- Performance metrics

### Metrics

- API response times
- Database query performance
- Celery task execution times
- Error rates

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MySQL service status
   - Verify database credentials
   - Ensure database exists

2. **Celery Tasks Not Processing**
   - Check Redis connection
   - Verify Celery worker is running
   - Check task queue status

3. **Webhook Signature Validation Failed**
   - Verify webhook secret configuration
   - Check request headers
   - Validate payload format

### Debug Mode

Set `DEBUG=True` in environment variables to enable:
- Mock Razorpay responses
- Detailed error messages
- API documentation endpoints

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:
- Create GitHub issues for bugs
- Check documentation for common questions
- Review API documentation for usage examples
