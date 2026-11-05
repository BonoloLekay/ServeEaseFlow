# ServeEaseFlow – System Architecture Document

## 1. Introduction

This document describes the technical architecture of ServeEaseFlow, an Automotive Dealership Service & Operations Management System.

The system follows a multi-platform architecture consisting of two independent React web applications, a shared backend API and a centralised PostgreSQL database.

## 2. Architectural Style

ServeEase will use a modular client-server architecture.

The architecture consists of:

1. Presentation Layer – React applications.
2. Application Layer – FastAPI REST API.
3. Data Access Layer – SQLAlchemy ORM.
4. Database Layer – PostgreSQL.
5. External Integration Layer – PayFast sandbox.
6. Analytics Layer – Pandas, Chart.js and Power BI.

## 3. Application Architecture

### 3.1 Customer Portal

Technology:

- React.
- Vite.
- Tailwind CSS.
- Chart.js where customer-facing visualisations are required.

Responsibilities:

- Customer registration and authentication.
- Customer profile management.
- Vehicle registration.
- Service appointment booking.
- Appointment management.
- Service progress tracking.
- Service history.
- Invoice access.
- PayFast sandbox payments.
- Customer feedback.

### 3.2 Operations Portal

Technology:

- React.
- Vite.
- Tailwind CSS.
- Chart.js.

Responsibilities:

- Staff authentication.
- Role-based access.
- Appointment management.
- Customer and vehicle management.
- Vehicle check-in.
- Job card management.
- Technician allocation.
- Service-bay allocation.
- Workshop monitoring.
- Inventory management.
- Invoice management.
- Payment monitoring.
- Operational dashboards.
- Management reporting.

### 3.3 Backend API

Technology:

- Python.
- FastAPI.
- SQLAlchemy.
- Pydantic.
- JWT authentication.
- Pytest.

Responsibilities:

- Business logic processing.
- Authentication and authorisation.
- API request validation.
- Customer and vehicle management.
- Appointment scheduling.
- Workshop operations.
- Inventory transactions.
- Invoice generation.
- PayFast integration.
- Analytics data processing.
- Database communication.

### 3.4 Database

Technology:

- PostgreSQL.
- SQLAlchemy ORM.

Responsibilities:

- Store customer information.
- Store vehicle records.
- Maintain appointments.
- Maintain job cards and assignments.
- Store inventory information.
- Record invoices and payments.
- Store customer feedback.
- Maintain operational records.

## 4. External Integrations

### 4.1 PayFast Sandbox

ServeEase will integrate with PayFast's sandbox environment.

The integration will support:

- Payment initiation.
- Payment request generation.
- Payment notification handling.
- Payment notification verification.
- Transaction reference management.
- Payment status updates.

The backend will be responsible for validating payment notifications before updating invoice records.

No live payment processing will be performed in the initial release.

### 4.2 Power BI

Power BI will connect to the ServeEase database using an appropriate database connection.

It will provide supplementary management reports covering:

- Financial performance.
- Workshop performance.
- Inventory performance.
- Customer satisfaction.

### 4.3 Chart.js

Chart.js will be integrated into the React applications to provide interactive visualisations using analytics data supplied by the backend API.

## 5. Communication Architecture

1. Customers interact with the Customer Portal.
2. Employees interact with the Operations Portal.
3. Both portals send HTTPS requests to the shared FastAPI backend.
4. The backend authenticates requests and applies business rules.
5. SQLAlchemy communicates with PostgreSQL.
6. The backend communicates with PayFast when payments are initiated or verified.
7. Analytics endpoints provide data to Chart.js.
8. Power BI retrieves data for supplementary management reporting.

## 6. Security Architecture

- JWT-based authentication.
- Secure password hashing.
- Role-based access control.
- Backend permission enforcement.
- Input validation.
- Environment-based secret management.
- HTTPS communication.
- Customer data access restrictions.
- Payment notification verification.
- Database integrity constraints.

## 7. Deployment Architecture

The planned deployment environment is:

| Component           | Hosting  |
| ------------------- | -------- |
| Customer Portal     | Vercel   |
| Operations Portal   | Vercel   |
| FastAPI Backend     | Render   |
| PostgreSQL Database | Supabase |
| Source Code         | GitHub   |

Deployment providers and configurations will be finalised during implementation.

## 8. Architectural Principles

ServeEaseFlow will follow these principles:

- Separation of concerns.
- Modular design.
- Reusable frontend components.
- Centralised business logic.
- Secure API communication.
- Database normalisation.
- Maintainability.
- Scalability.
- Testability.
- Data integrity.

## 9. Architecture Constraints

- Both portals must use the same backend API.
- The database must be centrally managed.
- Sensitive credentials must not be committed to GitHub.
- Payment verification must occur on the backend.
- Role permissions must be enforced server-side.
- Power BI reporting must not bypass database security controls.
