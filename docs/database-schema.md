# PredictCNC — Database Schema Specification

## Schema Design (SQLAlchemy ORM Models)

`mermaid
erDiagram
    COMPANIES ||--o{ USERS : has
    COMPANIES ||--o{ MACHINES : owns
    MACHINES ||--o{ PREDICTIONS : records
    MACHINES ||--o{ MAINTENANCE_TICKETS : has
    PREDICTIONS ||--o| MAINTENANCE_TICKETS : triggers

    COMPANIES {
        int id PK
        string name UK
        datetime created_at
    }

    USERS {
        int id PK
        int company_id FK
        string username UK
        string email UK
        string hashed_password
        string full_name
        string role
        datetime created_at
    }

    MACHINES {
        int id PK
        int company_id FK
        string machine_code
        string machine_name
        string department
        string manufacturer
        date installation_date
        string status Healthy | Warning | Critical
        datetime updated_at
    }

    PREDICTIONS {
        int id PK
        int machine_id FK
        float air_temperature
        float process_temperature
        float rotational_speed
        float torque
        float tool_wear
        float rpm_torque_interaction
        float load_stress
        float temperature_difference
        float temperature_ratio
        float tool_wear_mean_10
        float air_temp_mean_10
        string prediction_label
        float failure_probability
        string risk_level
        json diagnosis_data
        datetime predicted_at
    }

    MAINTENANCE_TICKETS {
        int id PK
        int machine_id FK
        int prediction_id FK
        string priority High | Medium | Low
        string status Pending | In Progress | Completed
        text remarks
        datetime created_at
        datetime resolved_at
    }
`
