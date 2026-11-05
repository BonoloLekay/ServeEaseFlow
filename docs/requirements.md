# ServeEaseFlow – System Requirements Specification

## 1. Project Overview

### 1.1 System Name

ServeEaseFlow – Automotive Dealership Service & Operations Management System.

### 1.2 Purpose

ServeEaseFlow is a multi-platform automotive dealership management system designed to improve the management of vehicle servicing, customer interactions, workshop operations, spare-parts inventory and dealership performance.

The system will provide customers with a dedicated portal for managing their vehicles and service appointments, while dealership employees will use an operations portal to coordinate workshop activities and manage dealership services.

Both applications will communicate with a shared backend API and PostgreSQL database.

### 1.3 Problem Statement

Automotive dealerships manage several interconnected activities, including customer bookings, vehicle servicing, technician allocation, workshop scheduling, inventory control and financial administration.

When these activities are managed through disconnected processes, dealerships may experience:

- Inefficient appointment management.
- Poor visibility of vehicle service progress.
- Scheduling conflicts involving technicians and service bays.
- Inaccurate spare-parts inventory records.
- Delays in generating invoices and recording payments.
- Limited visibility into operational and financial performance.

ServeEaseFlow aims to centralise these activities within an integrated information system.

### 1.4 Project Objectives

The system aims to:

1. Provide customers with an accessible vehicle service booking platform.
2. Improve dealership appointment and workshop management.
3. Support technician and service-bay allocation.
4. Maintain accurate spare-parts inventory records.
5. Manage job cards, invoices and payment records.
6. Provide management with operational and financial analytics.
7. Improve data accuracy, security and operational efficiency.

## 2. Project Scope

### 2.1 In Scope

- Customer registration and authentication.
- Customer profile management.
- Vehicle registration and management.
- Service catalogue management.
- Vehicle service appointment booking.
- Appointment confirmation and rescheduling.
- Workshop job-card management.
- Technician and service-bay allocation.
- Workshop service-status tracking.
- Spare-parts inventory management.
- Invoice generation.
- PayFast sandbox payment gateway integration.
- Payment initiation and transaction verification.
- Payment status tracking.
- Payment confirmation and invoice updates.
- Customer service history.
- Customer satisfaction feedback.
- Dealership management dashboards.
- Operational and financial reporting.

### 2.2 Out of Scope

The initial release will not include:

- Live PayFast payment processing.
- Actual customer charges and settlement of funds.
- Direct integration with BMW internal systems.
- Predictive maintenance using machine learning.
- Automated WhatsApp Business API integration.
- Multi-dealership enterprise management.
- Real-time vehicle diagnostics.
- Delivery or collection logistics.

### 2.3 Intended Users

- Customers.
- Service Advisors.
- Workshop Managers.
- Technicians.
- Dealer Principals.

## 3. Functional Requirements

### 3.1 Customer Portal

The Customer Portal will allow customers to interact with the dealership and manage their vehicle servicing activities.

#### FR-001: Customer Registration

The system shall allow new customers to create accounts by providing their personal details, email address and password.

#### FR-002: Customer Authentication

The system shall allow registered customers to securely log in and log out.

#### FR-003: Customer Profile Management

The system shall allow customers to view and update their profile information.

#### FR-004: Vehicle Registration

The system shall allow customers to register vehicles by providing:

- Vehicle make.
- Vehicle model.
- Registration number.
- Vehicle identification number (VIN).
- Model year.
- Current mileage.

#### FR-005: Vehicle Management

The system shall allow customers to view and manage vehicles linked to their accounts.

#### FR-006: Service Catalogue

The system shall allow customers to browse available vehicle maintenance and repair services.

#### FR-007: Appointment Booking

The system shall allow customers to book service appointments by selecting:

- A registered vehicle.
- A service category.
- A preferred appointment date.
- An available appointment time.
- A description of the service request.

#### FR-008: Appointment Management

The system shall allow customers to view their appointments and request cancellations or rescheduling, subject to dealership rules.

#### FR-009: Booking Confirmation

The system shall display confirmation details when an appointment has been successfully submitted.

#### FR-010: Service Tracking

The system shall allow customers to monitor the progress of their vehicle through the service workflow.

#### FR-011: Service History

The system shall allow customers to view previous vehicle service records.

#### FR-012: Invoice Access

The system shall allow customers to view invoices associated with their completed services.

#### FR-013: Online Payments

The system shall integrate with the PayFast sandbox to allow customers to initiate payments against valid invoices.

#### FR-014: Payment Status

The system shall display payment statuses, including pending, successful and failed transactions.

#### FR-015: Payment Verification

The system shall verify payment notifications received from PayFast before updating an invoice as paid.

#### FR-016: Customer Feedback

The system shall allow customers to submit ratings and feedback after completing a service.

### 3.2 Dealership Operations Portal

The Operations Portal will provide authorised dealership employees with tools to manage customer appointments, workshop activities, inventory and dealership performance.

#### FR-017: Staff Authentication

The system shall allow authorised dealership employees to securely access the Operations Portal.

#### FR-018: Role-Based Access Control

The system shall restrict access to system functionality according to the employee's assigned role.

The initial roles shall include:

- Service Advisor.
- Workshop Manager.
- Technician.
- Dealer Principal.

#### FR-019: Appointment Management

The system shall allow Service Advisors to view, confirm, reschedule and cancel customer appointments.

#### FR-020: Customer and Vehicle Information

The system shall allow authorised employees to access relevant customer and vehicle information.

#### FR-021: Vehicle Check-In

The system shall allow Service Advisors to record when a customer brings a vehicle into the dealership.

#### FR-022: Job Card Management

The system shall allow authorised employees to create, view and update workshop job cards.

Each job card shall contain:

- Job card reference number.
- Customer information.
- Vehicle information.
- Reported vehicle problem.
- Requested services.
- Assigned technician.
- Service bay.
- Job status.
- Parts used.
- Work completion details.

#### FR-023: Technician Management

The system shall allow Workshop Managers to manage technician records and assign technicians to workshop jobs.

#### FR-024: Service Bay Management

The system shall allow Workshop Managers to manage service bays and allocate them to active workshop jobs.

#### FR-025: Workshop Scheduling

The system shall prevent conflicting technician and service-bay assignments.

#### FR-026: Workshop Progress Monitoring

The system shall allow authorised employees to monitor active jobs and update their service statuses.

#### FR-027: Parts Management

The system shall allow Workshop Managers to create, update and view spare-parts records.

#### FR-028: Inventory Monitoring

The system shall automatically update inventory quantities when parts are used on workshop jobs.

#### FR-029: Low-Stock Monitoring

The system shall identify inventory items whose quantities fall below their defined reorder levels.

#### FR-030: Invoice Generation

The system shall allow authorised employees to generate invoices for completed services.

#### FR-031: Payment Monitoring

The system shall allow authorised employees to view payment transactions and their verification statuses.

#### FR-032: Operational Dashboard

The system shall provide management with an overview of dealership operations, including:

- Total appointments.
- Active workshop jobs.
- Completed services.
- Delayed workshop jobs.
- Technician workloads.
- Service bay utilisation.
- Low-stock inventory alerts.

#### FR-033: Financial Dashboard

The system shall provide the Dealer Principal with financial insights, including:

- Total service revenue.
- Monthly revenue trends.
- Revenue by service category.
- Outstanding invoices.
- Successful payment transactions.

#### FR-034: Customer Satisfaction Reporting

The system shall allow management to review customer satisfaction ratings and feedback.

#### FR-035: Staff Account Management

The system shall allow authorised management users to create, update, deactivate and assign roles to dealership staff accounts.

## 4. Business Rules

| ID     | Business Rule                                                                             |
| ------ | ----------------------------------------------------------------------------------------- |
| BR-001 | A customer must have a registered account before booking a service appointment.           |
| BR-002 | A vehicle must be registered to a customer before it can be booked for servicing.         |
| BR-003 | A vehicle registration number and VIN must be uniquely identifiable within the system.    |
| BR-004 | Every appointment must reference a valid customer, vehicle and service category.          |
| BR-005 | Appointment dates must not be in the past.                                                |
| BR-006 | Appointment confirmation is subject to dealership availability.                           |
| BR-007 | Only authorised staff may confirm or manage dealership appointments.                      |
| BR-008 | A job card must exist before workshop work begins.                                        |
| BR-009 | Each job card must reference a valid appointment or an authorised walk-in service record. |
| BR-010 | A technician cannot be assigned to overlapping active jobs.                               |
| BR-011 | A service bay cannot be assigned to overlapping active jobs.                              |
| BR-012 | Only authorised Workshop Managers may allocate technicians and service bays.              |
| BR-013 | Workshop job statuses must follow the defined service workflow.                           |
| BR-014 | Parts usage must create an inventory transaction and update available stock.              |
| BR-015 | Inventory quantities must not become negative.                                            |
| BR-016 | Completed jobs must have recorded completion details.                                     |
| BR-017 | An invoice must reference a valid job card.                                               |
| BR-018 | Payments must reference a valid invoice.                                                  |
| BR-019 | An invoice may only be marked as paid after successful payment verification.              |
| BR-020 | PayFast sandbox notifications must be validated before payment records are updated.       |
| BR-021 | Payment references must be unique to prevent duplicate transaction processing.            |
| BR-022 | Customers may only access their own vehicles, appointments, invoices and service history. |
| BR-023 | Employees may only access functionality permitted by their assigned roles.                |
| BR-024 | Deactivated staff accounts must not be allowed to authenticate.                           |
| BR-025 | Customer feedback may only be submitted for completed services.                           |

## 5. Service Workflow

The system shall support the following vehicle servicing workflow:

1. Customer registers or logs in.
2. Customer registers a vehicle.
3. Customer selects a service category.
4. Customer books an appointment.
5. Service Advisor reviews and confirms the appointment.
6. Customer brings the vehicle to the dealership.
7. Service Advisor checks in the vehicle.
8. A job card is created.
9. Workshop Manager assigns a technician and service bay.
10. Technician performs vehicle inspection.
11. Service work begins.
12. Required spare parts are recorded and deducted from inventory.
13. Quality inspection is completed.
14. Job card is marked as completed.
15. Invoice is generated.
16. Customer initiates payment through PayFast sandbox.
17. Payment notification is verified.
18. Vehicle is marked ready for collection.
19. Customer collects the vehicle.
20. Customer may submit service feedback.

## 6. Non-Functional Requirements

### 6.1 Security

- NFR-001: The system shall securely hash user passwords.
- NFR-002: The system shall use JWT-based authentication.
- NFR-003: The system shall enforce role-based access control on backend endpoints.
- NFR-004: The system shall validate and sanitise user input.
- NFR-005: The system shall protect sensitive configuration values using environment variables.
- NFR-006: The system shall verify PayFast payment notifications before updating payment statuses.
- NFR-007: The system shall prevent customers from accessing other customers' records.

### 6.2 Performance

- NFR-008: The system shall support concurrent customer and employee access.
- NFR-009: API endpoints shall return responses within acceptable response times under normal operating conditions.
- NFR-010: Database queries shall be designed efficiently using appropriate indexing and relationships.

### 6.3 Reliability and Data Integrity

- NFR-011: The system shall maintain consistent records across customer, vehicle, appointment, job card, inventory and payment modules.
- NFR-012: Critical database operations shall use transactions where appropriate.
- NFR-013: Duplicate payment notifications shall not result in duplicate payment processing.
- NFR-014: The system shall handle validation errors and unexpected failures gracefully.

### 6.4 Usability and Accessibility

- NFR-015: Both portals shall provide responsive interfaces for desktop, tablet and mobile devices.
- NFR-016: The system shall provide clear feedback for successful and unsuccessful operations.
- NFR-017: Navigation shall be consistent and understandable for each user role.

### 6.5 Maintainability

- NFR-018: The backend shall follow a modular architecture.
- NFR-019: Frontend applications shall use reusable components.
- NFR-020: The system shall maintain clear technical documentation.
- NFR-021: The source code shall follow consistent naming and coding conventions.

### 6.6 Testing

- NFR-022: Backend business logic shall have automated unit tests.
- NFR-023: API endpoints shall have automated integration tests.
- NFR-024: Authentication, authorisation, appointment scheduling, inventory updates and payment verification shall be tested.

### 6.7 Privacy

- NFR-025: The system shall use fictional customer and vehicle data for demonstration purposes.
- NFR-026: Personal information shall only be accessible to authorised users.
- NFR-027: The system shall be designed with South Africa's POPIA principles in mind.

## 7. Technology Constraints

The initial implementation shall use the following technologies:

| Layer                               | Technology      |
| ----------------------------------- | --------------- |
| Customer Portal                     | React + Vite    |
| Operations Portal                   | React + Vite    |
| Styling                             | Tailwind CSS    |
| Backend API                         | Python FastAPI  |
| ORM                                 | SQLAlchemy      |
| Data Validation                     | Pydantic        |
| Database                            | PostgreSQL      |
| Authentication                      | JWT             |
| Password Hashing                    | bcrypt          |
| Data Analytics and Processing       | Python + Pandas |
| Visualisations                      | Chart.j         |
| Business Intelligence and Reporting | Power BI        |
| Payment Gateway                     | PayFast Sandbox |
| Backend Testing                     | Pytest          |
| Version Control                     | Git and GitHub  |

## 8. Project Deliverables

The project shall deliver:

1. Customer Portal.
2. Dealership Operations Portal.
3. Shared REST API.
4. PostgreSQL database.
5. Authentication and role-based access control.
6. Appointment and workshop management.
7. Inventory management.
8. Invoice and PayFast sandbox integration.
9. Management analytics dashboard.
10. Automated tests.
11. System documentation.
12. Deployed demonstration environment.

## 9. Business Intelligence and Analytics

ServeEaseFlow shall incorporate business intelligence capabilities to support operational monitoring and management decision-making.

### 9.1 Application Analytics

The React applications shall use Chart.js to display interactive dashboards using data retrieved from the FastAPI backend.

The dashboards shall include:

- Monthly service revenue.
- Appointment trends.
- Workshop utilisation.
- Job completion statistics.
- Technician workloads.
- Inventory levels.
- Customer satisfaction ratings.

### 9.2 Power BI Reporting

Microsoft Power BI shall be used to develop supplementary business intelligence reports using data from the ServeEaseFlow PostgreSQL database.

The reports shall include:

1. **Financial Analysis:** Revenue trends, average invoice values and payment collection performance.
2. **Workshop Analysis:** Job completion times, technician performance and service-bay utilisation.
3. **Inventory Analysis:** Parts consumption, stock movement and low-stock trends.
4. **Customer Analysis:** Customer satisfaction, repeat bookings and service preferences.

### 9.3 Data Processing

Python and Pandas shall support data extraction, cleaning, transformation and analysis.

The analytics implementation shall use fictional demonstration data to generate meaningful business insights.
