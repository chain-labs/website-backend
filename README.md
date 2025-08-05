# Chain Labs Backend - Dummy API Server

A FastAPI-based dummy server implementing the complete API specification for frontend integration. This server provides JWT-based authentication, goal personalization, mission tracking, and session management.

## 🚀 Features

- **Fully Async Implementation** using FastAPI + asyncio
- **JWT Authentication** with 1-year token expiry
- **Goal Parsing & Personalization** with AI-style responses
- **Mission & Progress Tracking** with point-based unlocking
- **Session Management** with async in-memory storage
- **Auto-generated API Documentation** via FastAPI
- **Type Safety** using Pydantic models throughout
- **CORS Support** for frontend integration
- **Comprehensive Testing** with pytest and async test fixtures

## 📋 API Endpoints

### Authentication
- `POST /api/auth/session` - Create new session
- `POST /api/auth/refresh` - Refresh tokens
- `DELETE /api/auth/session` - Revoke session

### Goals & Personalization  
- `POST /api/goal` - Submit user goal
- `POST /api/clarify` - Clarify goal with follow-up
- `GET /api/personalised` - Get personalized content

### Missions & Progress
- `GET /api/progress` - Get current progress
- `POST /api/mission/complete` - Complete mission
- `GET /api/unlock-status` - Check unlock status

### Session Management
- `GET /api/session` - Full session hydration

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.13+
- UV package manager

### Installation
```bash
# Clone the repository
cd backend

# Install dependencies (already done if using UV)
uv sync

# Run the server
python main.py
```

The server will start on `http://localhost:8000`

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run tests with coverage
pytest --cov=src
```

#### Testing Philosophy
- **Integration Tests**: Focus on testing complete API flows without mocking internal services
- **Async Testing**: All tests use async/await patterns with proper async fixtures
- **Type Safety**: Leverages Pydantic models for request/response validation in tests
- **Realistic Data**: Uses actual service implementations rather than mocks for internal components
- **Comprehensive Coverage**: Tests cover authentication, goal processing, mission completion, and session management

## 📖 API Documentation

Interactive API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the API

### 1. Create a Session
```bash
curl -X POST http://localhost:8000/api/auth/session \
  -H "Content-Type: application/json"
```

### 2. Submit a Goal (use token from step 1)
```bash
curl -X POST http://localhost:8000/api/goal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"input": "I want to build an AI agent for restaurants"}'
```

### 3. Complete a Mission
```bash
curl -X POST http://localhost:8000/api/mission/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"mission_id": "defineMetrics", "artifact": {"answer": "Your solution"}}'
```

### 4. Check Progress
```bash
curl -X GET http://localhost:8000/api/progress \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📁 Project Structure

```
backend/
├── main.py                 # Entry point
├── test_api.py            # Manual API testing script
├── pytest.ini            # Pytest configuration
├── pyproject.toml         # UV dependencies
├── src/                   # Source code
│   ├── auth/              # JWT utilities & middleware (async)
│   │   ├── jwt_utils.py   # Token generation/validation
│   │   └── middleware.py  # Authentication middleware
│   ├── models/            # Pydantic models (type-safe)
│   │   ├── auth.py        # Auth request/response models
│   │   ├── goal.py        # Goal & personalization models
│   │   ├── mission.py     # Mission & progress models
│   │   └── session.py     # Session models
│   ├── routes/            # API route handlers (async)
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── goals.py       # Goal & personalization endpoints
│   │   ├── missions.py    # Mission & progress endpoints
│   │   └── session.py     # Session management endpoints
│   ├── services/          # Business logic (async)
│   │   ├── session_manager.py  # Async in-memory session storage
│   │   └── mock_data.py        # Mock data generation
│   ├── utils/             # Utilities
│   │   └── errors.py      # Error handling
│   └── main.py            # FastAPI app setup
└── tests/                 # Comprehensive test suite
    ├── conftest.py        # Pytest fixtures & configuration
    ├── test_auth.py       # Authentication endpoint tests
    ├── test_goals.py      # Goal endpoint tests
    ├── test_missions.py   # Mission endpoint tests
    ├── test_session.py    # Session endpoint tests
    └── test_services.py   # Service layer unit tests
```

## 🔧 Configuration

### Environment Variables
- `JWT_SECRET_KEY` - **Required for production** - Secret key for JWT signing
- `PORT` - Server port (defaults to 8000, auto-set by Railway)
- `HOST` - Server host (defaults to 0.0.0.0)
- `RAILWAY_ENVIRONMENT` - Auto-detected Railway environment
- `PYTHONPATH` - Python module path (auto-set by Railway)

Copy `.env.example` to `.env` and update values for local development.

## 🎯 Mock Data Features

- **Dynamic Goal Generation** based on user input
- **Randomized Missions** from a pool of realistic tasks  
- **Smart Case Studies** related to user goals
- **Progressive Unlocking** - call feature unlocks after 2+ completed missions
- **Realistic Point System** with varying point values

## 🔒 Security Notes

This is a **dummy server** for development purposes:
- Uses hardcoded JWT secret (change in production)
- Stores data in memory (use proper database in production)
- No rate limiting or advanced security features
- Allows all CORS origins (restrict in production)

## 🚦 Health Check

Check if the server is running:
```bash
curl http://localhost:8000/health
```

## 🚀 Deployment

This project is ready for production deployment with:

### Railway.app Deployment
- ✅ **One-click deployment** to Railway.app
- ✅ **Auto-scaling** and **health monitoring**
- ✅ **Environment variable** configuration
- ✅ **Custom domain** support

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete deployment guide.

### GitHub Actions CI
- ✅ **Automated testing** on push/PR
- ✅ **Security checks** and linting  
- ✅ **Build validation** and import checks
- ✅ **Performance testing** with response times

### Quick Deploy to Railway
1. Fork this repository
2. Sign up at [railway.app](https://railway.app)
3. Connect your GitHub repo
4. Set `JWT_SECRET_KEY` environment variable
5. Deploy! 🚀

## 📋 Next Steps for Production

1. Replace in-memory storage with a proper database
2. Implement real AI/LLM integration for goal parsing  
3. Implement rate limiting and security headers
4. Add comprehensive logging and monitoring
5. Set up custom domain and SSL

## 🤝 Frontend Integration

This dummy server is designed to be a drop-in replacement for frontend integration testing. All endpoints return realistic mock data that matches the exact schema specified in `api-spec.md`.

The frontend can immediately integrate against this server and later switch to the production backend seamlessly.
