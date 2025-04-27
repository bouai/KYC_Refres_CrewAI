import sqlite3

# Connect to SQLite DB (creates file if not exists)
conn = sqlite3.connect("KYC_DataBase.db")
cursor = conn.cursor()

# Create table with all the fields
cursor.execute("""
CREATE TABLE IF NOT EXISTS OnboardingData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name TEXT,
    document_type TEXT,
    client_identifier TEXT,
    entity_legal_name TEXT,
    date_of_incorporation DATE,
    dba_name TEXT,
    dba_address TEXT,
    phone_number TEXT,
    number_of_employees TEXT,
    number_of_branches TEXT,
    client_regulated BOOLEAN,
    name_of_regulator TEXT,
    id_number TEXT,
    country_issuing_id TEXT,
    id_type TEXT,
    date_of_id_issuance DATE,
    is_payment_intermediary BOOLEAN,
    member_type TEXT,
    member_association TEXT,
    member_role TEXT,
    member_legal_name TEXT,
    member_first_name TEXT,
    member_middle_name TEXT,
    member_last_name TEXT,
    ownership_percentage TEXT,
    identification_number TEXT,
    issuing_country TEXT,
    id_expiry_date DATE,
    identification_type TEXT,
    address_line_1 TEXT,
    address_line_2 TEXT,
    address_country TEXT,
    date_of_birth DATE,
    country_of_citizenship TEXT,
    city_of_birth TEXT,
    country_of_birth TEXT,
    onboarding_created_date DATE,
    onboarding_updated_date DATE
);
""")

# Create KycRefresh table with all existing fields plus new status fields
cursor.execute("""
CREATE TABLE IF NOT EXISTS KycRefreshData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name TEXT,
    document_type TEXT,
    client_identifier TEXT,
    entity_legal_name TEXT,
    date_of_incorporation DATE,
    dba_name TEXT,
    dba_address TEXT,
    phone_number TEXT,
    number_of_employees TEXT,
    number_of_branches TEXT,
    client_regulated BOOLEAN,
    name_of_regulator TEXT,
    id_number TEXT,
    country_issuing_id TEXT,
    id_type TEXT,
    date_of_id_issuance DATE,
    is_payment_intermediary BOOLEAN,
    member_type TEXT,
    member_association TEXT,
    member_role TEXT,
    member_legal_name TEXT,
    member_first_name TEXT,
    member_middle_name TEXT,
    member_last_name TEXT,
    ownership_percentage TEXT,
    identification_number TEXT,
    issuing_country TEXT,
    id_expiry_date DATE,
    identification_type TEXT,
    address_line_1 TEXT,
    address_line_2 TEXT,
    address_country TEXT,
    date_of_birth DATE,
    country_of_citizenship TEXT,
    city_of_birth TEXT,
    country_of_birth TEXT,
    KycRefresh_created_date DATE,
    KycRefresh_updated_date DATE,
    screening_agent_status TEXT,
    outreach_agent_status TEXT,
    research_agent_status TEXT,
    analyst_agent_status TEXT,
    refresh_status TEXT
);
""")

conn.commit()
conn.close()
print("KYC DataBase created successfully.")
