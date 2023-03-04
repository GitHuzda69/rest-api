import mysql.connector

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "python"
)

if db.is_connected():
    print("Connected")