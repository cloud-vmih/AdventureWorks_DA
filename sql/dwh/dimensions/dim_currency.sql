CREATE TABLE IF NOT EXISTS dwh.dim_currency (
    currency_key SERIAL PRIMARY KEY,
    currency_code CHAR(3) UNIQUE,
    currency_name VARCHAR(50)
);

TRUNCATE TABLE dwh.dim_currency CASCADE;

INSERT INTO dwh.dim_currency (currency_code, currency_name)
SELECT currencycode, name FROM staging.currency;
