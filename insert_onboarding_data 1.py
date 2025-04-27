import sqlite3
import pandas as pd
from datetime import datetime

# Read CSV file
df = pd.read_csv('Data/onboardingData.csv')  # Replace with your CSV file path

# Add today's date for created and updated dates
today = datetime.now().date()
df['onboarding_created_date'] = today
df['onboarding_updated_date'] = today

# Connect to the database
conn = sqlite3.connect('KYC_DataBase.db')
cursor = conn.cursor()

# Convert dataframe to list of tuples
columns = df.columns.tolist()
values = [tuple(row) for row in df.values]

# Generate the INSERT statement
placeholders = ','.join(['?' for _ in columns])
columns_str = ','.join(columns)
insert_query = f"INSERT INTO OnboardingData ({columns_str}) VALUES ({placeholders})"

# Insert the data
try:
    cursor.executemany(insert_query, values)
    conn.commit()
    print(f"Successfully inserted {len(values)} records into OnboardingData table")
except sqlite3.Error as e:
    print(f"Error inserting data: {e}")
finally:
    conn.close()

# Close the database connection
