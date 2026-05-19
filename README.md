# VLN4VI - Indoor Navigation System

## Project Overview

VLN4VI is a vision-based indoor navigation system designed for visually impaired users. The system integrates advanced computer vision techniques, semantic understanding, and accessibility features to deliver accurate and reliable indoor navigation.

## System Architecture

```
VLN4VI/
├── backend/                         # Backend services
│   ├── app.py                       # Main application file
│   ├── database_optimization.py     # Database optimization
│   ├── dg_evaluation_enhancement.py # DG evaluation enhancement
│   ├── user_needs_validator.py      # User needs validation
│   ├── accessibility_checker.py     # Accessibility checking
│   ├── indoor_gml_generator.py      # IndoorGML generation
│   ├── enhanced_metrics_collector.py# Enhanced metrics collection
│   └── comprehensive_testing.py     # Comprehensive testing
├── frontend/                        # Frontend interface
│   ├── src/
│   │   ├── App.jsx                  # Main application component
│   │   └── frontend_optimization.jsx# Frontend optimization
│   └── package.json
├── start_system.py                  # System startup script
└── README.md                        # Project documentation
```

## Quick Start

### 1. Requirements

- Python 3.8+
- Node.js 16+
- SQLite 3
- Modern browser support

### 2. Install Dependencies

#### Backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Frontend dependencies

```bash
cd frontend
npm install
```

### 3. Start System

Use the one-click startup script:

```bash
python start_system.py
```

Or start manually:

#### Start the backend

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### Start the frontend

```bash
cd frontend
npm start
```

### 4. Access the System

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- Health check: http://localhost:8000/health/enhanced
- API docs: http://localhost:8000/docs

## Core Features

### 1. Visual Localization

- Photo-based indoor localization
- Confidence estimation
- Multimodal information fusion

### 2. Navigation Instructions

- Natural language instruction generation
- Speech synthesis support
- Multilingual support

### 3. Accessibility

- WCAG 2.2 compliance
- VoiceOver support
- High-contrast mode
- Large-font mode

### 4. Metrics Collection

- Real-time performance monitoring
- User behavior analytics
- System health checks

### 5. Evaluation System

- DG goal evaluation
- User needs validation
- Performance metrics analysis

## API Endpoints

### Core Features

- `POST /api/locate` — Location recognition
- `POST /api/qa` — Question-and-answer interaction

### DG Optimization Features

- `POST /api/dg/metrics/collect` — Metrics collection
- `POST /api/dg/evaluation/record` — Evaluation record
- `POST /api/dg/accessibility/check` — Accessibility check
- `POST /api/dg/indoor_gml/generate` — IndoorGML generation
- `POST /api/dg/user_needs/record` — User needs record

### Data Management

- `GET /api/dg/metrics/export/{session_id}` — Metrics export
- `GET /api/dg/metrics/analytics/{session_id}` — Analytics report
- `GET /api/dg/user_needs/matrix` — Needs matrix

## Database Structure

The system uses two main databases:

### Main Database

- `dg_evaluations` — DG evaluation data
- `user_needs_validation` — User needs validation
- `accessibility_tests` — Accessibility tests
- `indoor_gml_maps` — IndoorGML maps

### Metrics Database

- `metrics` — Metrics data
- `sessions` — Session management
- `evaluation_metrics` — Evaluation metrics
- `user_feedback` — User feedback

## Testing and Validation

### Run Comprehensive Tests

```bash
cd backend
python comprehensive_testing.py
```

### Test Coverage

- Basic connectivity tests
- Database functionality tests
- DG evaluation function tests
- User needs validation tests
- Accessibility tests
- IndoorGML function tests
- Performance tests
- Integration tests

## Configuration

### Environment Variables

```bash
ENABLE_DG_EVALUATION=true
ENABLE_ACCESSIBILITY_CHECKING=true
ENABLE_INDOOR_GML=true
METRICS_STORAGE_PATH=./metrics_data
```

### Database Configuration

- Automatic table creation
- Index optimization
- Performance monitoring

## Development Guide

### Code Structure

- Modular design
- Clear interface definitions
- Comprehensive error handling
- Detailed documentation comments

### Adding New Features

1. Implement the feature in the corresponding module
2. Add API endpoints
3. Update the database schema
4. Write test cases
5. Update the documentation

### Coding Standards

- Follow PEP 8
- Use type hints
- Write docstrings
- Follow error-handling best practices

## Deployment Guide

### Production Environment

- Use a production-grade web server
- Configure a reverse proxy
- Enable HTTPS
- Set up monitoring and logging

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check whether ports 8000 and 3000 are already in use
2. **Missing dependencies**: Make sure all Python packages and Node modules are installed
3. **Database errors**: Check SQLite permissions and file paths
4. **Frontend startup failure**: Check the Node.js version and npm configuration

### Viewing Logs

- Backend logs: console output
- Frontend logs: browser developer tools
- Database logs: SQLite log files

## Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

- Project maintainer: LarryYiGuo
- Email: ucbqwg7@ucl.ac.uk

## Changelog

### v1.0.0 (2025-01-07)

- Initial release
- Full DG optimization features
- Comprehensive test suite
- One-click startup script
