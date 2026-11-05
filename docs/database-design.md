# ServeEaseFlow – Database Design Document

## 1. Introduction

This document defines the proposed relational database structure for ServeEaseFlow.

The database will use PostgreSQL and SQLAlchemy ORM to manage relationships, constraints and data persistence.

The design supports customer management, vehicle servicing, workshop operations, inventory management, financial transactions and business intelligence.

## 2. Database Design Principles

The database will follow these principles:

- Relational database architecture.
- Primary and foreign key constraints.
- Referential integrity.
- Appropriate normalisation.
- Unique constraints where required.
- Indexing for frequently queried fields.
- Transactional consistency.
- Secure storage of sensitive information.

## 3. Database Entities

### 3.1 Authentication and User Management

**users**

Stores authentication and account information.

| Attribute     | Description                |
| ------------- | -------------------------- |
| id            | Primary key                |
| email         | Unique email address       |
| password_hash | Hashed password            |
| role_id       | Foreign key to roles       |
| is_active     | Account status             |
| created_at    | Account creation timestamp |
| updated_at    | Last update timestamp      |

**roles**

Stores system access roles.

| Attribute   | Description      |
| ----------- | ---------------- |
| id          | Primary key      |
| name        | Role name        |
| description | Role description |

Initial roles:

- CUSTOMER
- SERVICE_ADVISOR
- WORKSHOP_MANAGER
- TECHNICIAN
- DEALER_PRINCIPAL

### 3.2 Customer Management

**customers**

Stores customer profile information.

| Attribute  | Description            |
| ---------- | ---------------------- |
| id         | Primary key            |
| user_id    | Foreign key to users   |
| first_name | Customer first name    |
| last_name  | Customer surname       |
| phone      | Contact number         |
| created_at | Registration timestamp |

### 3.3 Vehicle Management

**vehicles**

Stores registered vehicle information.

| Attribute           | Description                          |
| ------------------- | ------------------------------------ |
| id                  | Primary key                          |
| customer_id         | Foreign key to customers             |
| make                | Vehicle manufacturer                 |
| model               | Vehicle model                        |
| registration_number | Unique registration                  |
| vin                 | Unique vehicle identification number |
| model_year          | Vehicle model year                   |
| current_mileage     | Current mileage                      |
| created_at          | Registration timestamp               |

### 3.4 Service Management

**service_categories**

Stores available dealership service categories.

| Attribute          | Description                |
| ------------------ | -------------------------- |
| id                 | Primary key                |
| name               | Service name               |
| description        | Service description        |
| base_price         | Indicative service price   |
| estimated_duration | Estimated service duration |
| is_active          | Availability status        |

**appointments**

Stores customer service appointments.

| Attribute           | Description                       |
| ------------------- | --------------------------------- |
| id                  | Primary key                       |
| customer_id         | Foreign key to customers          |
| vehicle_id          | Foreign key to vehicles           |
| service_category_id | Foreign key to service_categories |
| appointment_date    | Scheduled date and time           |
| description         | Customer service request          |
| status              | Appointment status                |
| created_at          | Booking timestamp                 |

### 3.5 Workshop Management

**job_cards**

Stores workshop job information.

| Attribute        | Description                          |
| ---------------- | ------------------------------------ |
| id               | Primary key                          |
| appointment_id   | Optional foreign key to appointments |
| vehicle_id       | Foreign key to vehicles              |
| customer_id      | Foreign key to customers             |
| job_reference    | Unique job card reference            |
| reported_problem | Reported vehicle problem             |
| inspection_notes | Inspection findings                  |
| status           | Workshop job status                  |
| checked_in_at    | Vehicle check-in timestamp           |
| completed_at     | Job completion timestamp             |
| created_at       | Job creation timestamp               |

**technicians**

Stores technician information.

| Attribute       | Description              |
| --------------- | ------------------------ |
| id              | Primary key              |
| user_id         | Foreign key to users     |
| employee_number | Unique employee number   |
| specialisation  | Technical specialisation |
| is_active       | Employment status        |

**service_bays**

Stores workshop service-bay information.

| Attribute   | Description           |
| ----------- | --------------------- |
| id          | Primary key           |
| bay_number  | Unique bay identifier |
| description | Bay description       |
| is_active   | Availability status   |

**job_assignments**

Stores technician and service-bay allocations.

| Attribute      | Description                 |
| -------------- | --------------------------- |
| id             | Primary key                 |
| job_card_id    | Foreign key to job_cards    |
| technician_id  | Foreign key to technicians  |
| service_bay_id | Foreign key to service_bays |
| assigned_at    | Assignment timestamp        |
| started_at     | Work start timestamp        |
| ended_at       | Work completion timestamp   |

### 3.6 Inventory Management

**parts**

Stores spare-parts information.

| Attribute         | Description             |
| ----------------- | ----------------------- |
| id                | Primary key             |
| part_number       | Unique part number      |
| name              | Part name               |
| description       | Part description        |
| unit_price        | Unit cost               |
| quantity_in_stock | Available stock         |
| reorder_level     | Minimum stock threshold |
| is_active         | Part availability       |

**job_card_parts**

Records spare parts used on workshop jobs.

| Attribute     | Description              |
| ------------- | ------------------------ |
| id            | Primary key              |
| job_card_id   | Foreign key to job_cards |
| part_id       | Foreign key to parts     |
| quantity_used | Quantity consumed        |
| unit_price    | Price at time of use     |
| created_at    | Usage timestamp          |

**inventory_transactions**

Records inventory movements.

| Attribute        | Description                       |
| ---------------- | --------------------------------- |
| id               | Primary key                       |
| part_id          | Foreign key to parts              |
| job_card_id      | Optional foreign key to job_cards |
| transaction_type | Stock movement type               |
| quantity         | Quantity moved                    |
| reference        | Transaction reference             |
| created_at       | Transaction timestamp             |

### 3.7 Financial Management

**invoices**

Stores customer service invoices.

| Attribute      | Description              |
| -------------- | ------------------------ |
| id             | Primary key              |
| job_card_id    | Foreign key to job_cards |
| invoice_number | Unique invoice number    |
| subtotal       | Invoice subtotal         |
| tax_amount     | Tax amount               |
| total_amount   | Total payable            |
| payment_status | Payment status           |
| issued_at      | Invoice issue timestamp  |
| due_at         | Payment due date         |

**payments**

Stores payment transaction records.

| Attribute         | Description                   |
| ----------------- | ----------------------------- |
| id                | Primary key                   |
| invoice_id        | Foreign key to invoices       |
| payment_reference | Unique payment reference      |
| gateway_reference | PayFast transaction reference |
| amount            | Payment amount                |
| payment_method    | Payment method                |
| status            | Payment status                |
| verified_at       | Verification timestamp        |
| created_at        | Transaction timestamp         |

### 3.8 Customer Experience

**feedback**

Stores customer service ratings and comments.

| Attribute   | Description              |
| ----------- | ------------------------ |
| id          | Primary key              |
| customer_id | Foreign key to customers |
| job_card_id | Foreign key to job_cards |
| rating      | Customer rating          |
| comment     | Customer feedback        |
| created_at  | Submission timestamp     |

## 4. Database Relationships

The database will implement the following relationships:

| Parent Entity      | Child Entity           | Relationship       |
| ------------------ | ---------------------- | ------------------ |
| Roles              | Users                  | One-to-many        |
| Users              | Customers              | One-to-one         |
| Users              | Technicians            | One-to-one         |
| Customers          | Vehicles               | One-to-many        |
| Customers          | Appointments           | One-to-many        |
| Vehicles           | Appointments           | One-to-many        |
| Service Categories | Appointments           | One-to-many        |
| Appointments       | Job Cards              | One-to-zero-or-one |
| Job Cards          | Job Assignments        | One-to-many        |
| Technicians        | Job Assignments        | One-to-many        |
| Service Bays       | Job Assignments        | One-to-many        |
| Job Cards          | Job Card Parts         | One-to-many        |
| Parts              | Job Card Parts         | One-to-many        |
| Parts              | Inventory Transactions | One-to-many        |
| Job Cards          | Invoices               | One-to-zero-or-one |
| Invoices           | Payments               | One-to-many        |
| Customers          | Feedback               | One-to-many        |
| Job Cards          | Feedback               | One-to-many        |

## 5. Important Database Constraints

1. User email addresses must be unique.
2. Vehicle registration numbers must be unique.
3. VIN values must be unique.
4. Employee numbers must be unique.
5. Job references must be unique.
6. Invoice numbers must be unique.
7. Payment references must be unique.
8. Inventory quantities cannot be negative.
9. Invoice amounts cannot be negative.
10. Payment amounts must be greater than zero.
11. Feedback ratings must be between 1 and 5.
12. Foreign keys must enforce valid relationships.
13. Technician and service-bay assignments must not overlap for active jobs.
14. Appointment vehicles must belong to the associated customer.

## 6. Payment Data Management

The system shall store PayFast transaction references and payment verification details.

The database shall not store customer card numbers, CVV values or other sensitive card authentication information.

Payment notifications shall be processed through the backend and verified before payment records are updated.

## 7. Analytics Data

The database shall provide the underlying information required for:

- Monthly service revenue.
- Service category performance.
- Appointment trends.
- Workshop utilisation.
- Technician workloads.
- Parts consumption.
- Inventory movement.
- Customer satisfaction.

Python Pandas and Power BI shall be used for supplementary data analysis and reporting.

Chart.js shall display application dashboard visualisations using data retrieved from the backend API.

## 8. Database Technology

- Database: PostgreSQL.
- ORM: SQLAlchemy.
- Database migrations: Alembic.
- Database administration: pgAdmin.
