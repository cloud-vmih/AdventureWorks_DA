CREATE TABLE IF NOT EXISTS dwh.fact_currency_rate (
    currency_rate_key SERIAL PRIMARY KEY,
    currency_rate_id INT,
    currency_key INT REFERENCES dwh.dim_currency(currency_key),
    date_key INT REFERENCES dwh.dim_date(date_key),
    average_rate NUMERIC,
    end_of_day_rate NUMERIC
);

TRUNCATE TABLE dwh.fact_currency_rate;

INSERT INTO dwh.fact_currency_rate (currency_rate_id, currency_key, date_key, average_rate, end_of_day_rate)
SELECT
    cr.currencyrateid as currency_rate_id,
    cur.currency_key,
    d.date_key,
    cr.averagerate as average_rate,
    cr.endofdayrate as end_of_day_rate
FROM staging.currencyrate cr
LEFT JOIN dwh.dim_currency cur ON cr.tocurrencycode = cur.currency_code
LEFT JOIN dwh.dim_date d ON cr.currencyratedate::DATE = d.full_date;
