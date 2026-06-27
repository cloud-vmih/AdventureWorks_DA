CREATE TABLE IF NOT EXISTS dwh.dim_employee (
    employee_key SERIAL PRIMARY KEY,
    employee_id INT UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    job_title VARCHAR(50),
    birth_date DATE,
    hire_date DATE,
    marital_status CHAR(1),
    gender CHAR(1),
    territory_id INT,
    current_flag BOOLEAN,
    modified_date TIMESTAMP
);

TRUNCATE TABLE dwh.dim_employee CASCADE;

INSERT INTO dwh.dim_employee (employee_id, first_name, last_name, job_title, birth_date, hire_date, marital_status, gender, territory_id, current_flag, modified_date)
SELECT
    e.businessentityid as employee_id,
    p.firstname as first_name,
    p.lastname as last_name,
    e.jobtitle as job_title,
    e.birthdate as birth_date,
    e.hiredate as hire_date,
    e.maritalstatus as marital_status,
    e.gender,
    sth.territoryid as territory_id,
    e.currentflag as current_flag,
    e.modifieddate as modified_date
FROM staging.employee e
LEFT JOIN staging.person p ON e.businessentityid = p.businessentityid
LEFT JOIN staging.salesterritoryhistory sth ON e.businessentityid = sth.businessentityid AND sth.enddate IS NULL;
