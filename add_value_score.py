import sqlite3

# Path to your SQLite database
db_path = 'listings.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# SQL query to add the 'value_score' column
# Assuming 'value_score' is a numeric type, change the type if needed
alter_table_query = "ALTER TABLE listings ADD COLUMN value_score_percentile INTEGER"

# Execute the SQL command
cursor.execute(alter_table_query)

# Commit the changes in the database
conn.commit()

# Close the database connection
conn.close()

print("Column 'value_score' added successfully.")
