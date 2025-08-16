# RiskPulse

RiskPulse is an early-stage project focused on portfolio risk analytics. It provides tools for tracking investment positions and evaluating portfolio risk through a clean API and (soon) an interactive frontend.

## Current Features

- **User & Portfolio Management**  create, update, and manage user accounts and their associated portfolios
- **API-First Backend**  built with FastAPI and MongoDB, offering endpoints for managing portfolios and users
- **Testing & Reliability**  end-to-end and unit tests to ensure consistent behavior across portfolio and user flows

## Frontend (In Progress)

A React + TypeScript frontend is currently under development. The frontend will provide a modern, intuitive interface for managing portfolios and viewing risk insights.

## Quick Start

```bash
# Run with Docker
docker-compose up -d

# Access API documentation
# http://localhost:8000/docs
```

## Testing

```bash
cd apps/risk_api
source app/.venv/bin/activate
python -m pytest app/tests/ -v
```

## Roadmap

- Expanded portfolio analytics
- Deeper risk modeling features
- Enhanced visualization via the frontend