import sys
import pandas as pd
import requests
from pandas_datareader import data as pdr
from src.common.database import get_dwh_engine

START_YEAR = 2022
END_YEAR = 2025

COUNTRIES = {
    "US": "United States",
    "CA": "Canada",
    "FR": "France",
    "DE": "Germany",
    "AU": "Australia",
    "GB": "United Kingdom"
}

WB_INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",
    "income": "NY.GNP.PCAP.CD",
    "population": "SP.POP.TOTL"
}

EXCHANGE_RATE_MAP = {
    "US": None,
    "CA": "DEXCAUS",
    "FR": "DEXUSEU",
    "DE": "DEXUSEU",
    "AU": "DEXUSAL",
    "GB": "DEXUSUK"
}

CPI_FRED_MAP = {
    "US": "CPIAUCSL",
    "CA": "CANCPIALLMINMEI",
    "FR": "FRACPIALLMINMEI",
    "DE": "DEUCPIALLMINMEI",
    "AU": "AUSCPIALLQINMEI",
    "GB": "GBRCPIALLMINMEI"
}

TERRITORIES = [
    [1,  "Northwest",      "US", "North America"],
    [2,  "Northeast",      "US", "North America"],
    [3,  "Central",        "US", "North America"],
    [4,  "Southwest",      "US", "North America"],
    [5,  "Southeast",      "US", "North America"],
    [6,  "Canada",         "CA", "North America"],
    [7,  "France",         "FR", "Europe"],
    [8,  "Germany",        "DE", "Europe"],
    [9,  "Australia",      "AU", "Pacific"],
    [10, "United Kingdom", "GB", "Europe"],
]


def create_monthly_base():
    dates = pd.date_range(start=f"{START_YEAR}-01-01", end=f"{END_YEAR}-12-01", freq="MS")
    rows = []
    for country_code, country_name in COUNTRIES.items():
        for d in dates:
            rows.append({
                "country_code": country_code,
                "country_name": country_name,
                "date": d,
                "year": d.year,
                "month": d.month
            })
    return pd.DataFrame(rows)


def fetch_worldbank(country_code, indicator_name, indicator_code):
    url = (
        f"https://api.worldbank.org/v2/country/{country_code}"
        f"/indicator/{indicator_code}"
        f"?format=json&date={START_YEAR}:{END_YEAR}&per_page=1000"
    )
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"World Bank error: {country_code} {indicator_name}")
            return pd.DataFrame()
        data = r.json()
        if len(data) < 2 or data[1] is None:
            return pd.DataFrame()
        rows = []
        for item in data[1]:
            rows.append({"country_code": country_code, "year": int(item["date"]), indicator_name: item["value"]})
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"World Bank error: {country_code} {indicator_name} - {e}")
        return pd.DataFrame()


def collect_worldbank_annual():
    records = []
    for indicator_name, indicator_code in WB_INDICATORS.items():
        for cc in COUNTRIES:
            df = fetch_worldbank(cc, indicator_name, indicator_code)
            if not df.empty:
                records.append(df)
    if not records:
        return pd.DataFrame()
    combined = pd.concat(records, ignore_index=True)
    base = pd.MultiIndex.from_product(
        [COUNTRIES.keys(), range(START_YEAR, END_YEAR + 1)],
        names=["country_code", "year"]
    ).to_frame(index=False)
    for indicator_name in WB_INDICATORS:
        temp = combined[combined[indicator_name].notna()][["country_code", "year", indicator_name]]
        base = base.merge(temp, on=["country_code", "year"], how="left")
    return base


def fred_to_monthly(series_code, value_name, start_override=None):
    start_date = start_override or f"{START_YEAR}-01-01"
    end_date = f"{END_YEAR}-12-31"
    try:
        temp = pdr.DataReader(series_code, "fred", start_date, end_date)
        temp = temp.reset_index()
        temp.columns = ["date", value_name]
        temp["date"] = pd.to_datetime(temp["date"])
        temp["year"] = temp["date"].dt.year
        temp["month"] = temp["date"].dt.month
        return temp.groupby(["year", "month"], as_index=False)[value_name].mean()
    except Exception as e:
        print(f"FRED error: {series_code} - {e}")
        return pd.DataFrame(columns=["year", "month", value_name])


def run_macro_etl():
    print("=== Fetching Macroeconomic Data from World Bank + FRED ===")

    print("Creating monthly base...")
    df_monthly = create_monthly_base()

    print("Fetching World Bank data (GDP, income, population)...")
    df_wb = collect_worldbank_annual()
    if not df_wb.empty:
        df_macro = df_monthly.merge(df_wb, on=["country_code", "year"], how="left")
        df_macro = df_macro.sort_values(["country_code", "date"])
        df_macro[["gdp", "income", "population"]] = (
            df_macro.groupby("country_code")[["gdp", "income", "population"]].ffill()
        )
    else:
        print("Warning: No World Bank data fetched, continuing with empty columns.")
        df_macro = df_monthly.copy()
        df_macro["gdp"] = None
        df_macro["income"] = None
        df_macro["population"] = None

    print("Fetching FRED data (oil price, interest rate)...")
    oil_price = fred_to_monthly("DCOILWTICO", "oil_price")
    interest_rate = fred_to_monthly("FEDFUNDS", "interest_rate")
    df_macro = df_macro.merge(oil_price, on=["year", "month"], how="left")
    df_macro = df_macro.merge(interest_rate, on=["year", "month"], how="left")

    print("Fetching exchange rates...")
    df_macro["exchange_rate"] = None
    for country_code, fred_code in EXCHANGE_RATE_MAP.items():
        mask = df_macro["country_code"] == country_code
        if fred_code is None:
            df_macro.loc[mask, "exchange_rate"] = 1.0
        else:
            temp = fred_to_monthly(fred_code, "exchange_rate_temp")
            if not temp.empty:
                df_macro = df_macro.merge(temp, on=["year", "month"], how="left")
                df_macro.loc[mask, "exchange_rate"] = df_macro.loc[mask, "exchange_rate_temp"]
                df_macro = df_macro.drop(columns=["exchange_rate_temp"])

    print("Fetching CPI and calculating inflation...")
    dates_ext = pd.date_range(start="2021-01-01", end=f"{END_YEAR}-12-01", freq="MS")
    rows_ext = []
    for cc in COUNTRIES:
        for d in dates_ext:
            rows_ext.append({"country_code": cc, "year": d.year, "month": d.month})
    df_ext = pd.DataFrame(rows_ext)

    for country_code, series_code in CPI_FRED_MAP.items():
        print(f"  Fetching CPI: {country_code} ({series_code})")
        temp = fred_to_monthly(series_code, "cpi_temp", start_override="2021-01-01")
        if temp.empty:
            print(f"  Skipping CPI for {country_code}")
            continue
        mask = df_ext["country_code"] == country_code
        df_ext = df_ext.merge(temp, on=["year", "month"], how="left")
        df_ext.loc[mask, "cpi"] = df_ext.loc[mask, "cpi_temp"]
        df_ext = df_ext.drop(columns=["cpi_temp"])

    df_ext = df_ext.sort_values(["country_code", "year", "month"])
    df_ext["cpi"] = df_ext.groupby("country_code")["cpi"].ffill()
    df_ext["cpi_lag12"] = df_ext.groupby("country_code")["cpi"].shift(12)
    df_ext["inflation"] = (
        (df_ext["cpi"] - df_ext["cpi_lag12"]) / df_ext["cpi_lag12"] * 100
    ).round(6)
    df_ext = df_ext.drop(columns=["cpi_lag12"])
    df_ext = df_ext[df_ext["year"] >= START_YEAR][
        ["country_code", "year", "month", "cpi", "inflation"]
    ].reset_index(drop=True)

    df_macro = df_macro.merge(df_ext, on=["country_code", "year", "month"], how="left")

    print("Merging with territory data...")
    territories_df = pd.DataFrame(TERRITORIES, columns=["territoryid", "territory_name", "country_code", "territory_group"])
    df_result = territories_df.merge(df_macro, on="country_code", how="left")

    FINAL_COLS = [
        "territoryid", "territory_name", "territory_group",
        "country_code", "country_name",
        "date", "year", "month",
        "gdp", "interest_rate", "oil_price", "exchange_rate",
        "income", "population", "cpi", "inflation",
    ]
    df_result = df_result[FINAL_COLS].sort_values(["territoryid", "date"]).reset_index(drop=True)

    print(f"Macro dataset: {len(df_result)} rows, {df_result.isnull().sum().sum()} nulls")

    print("Loading into staging.macro_territory_monthly...")
    engine = get_dwh_engine()
    if "date" in df_result.columns:
        df_result["date"] = df_result["date"].dt.strftime('%Y-%m-%d')
    df_result.to_sql("macro_territory_monthly", engine, schema="staging", if_exists="replace", index=False)
    print(f"Loaded {len(df_result)} rows into staging.macro_territory_monthly")

    print("=== Macro ETL Finished Successfully ===")


if __name__ == "__main__":
    run_macro_etl()
