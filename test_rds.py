import psycopg2
import boto3

import psycopg2

conn = psycopg2.connect(
    host="beacon-database.cefowseme3pk.us-east-1.rds.amazonaws.com",
    dbname="your_db",
    user="your_user",
    password="your_password",
    sslmode="verify-full",
    sslrootcert="global-bundle.pem"
)
