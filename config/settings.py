import os
from dotenv import load_dotenv
from configparser import SectionProxy




load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY= os.getenv("SECRET_KEY")

DATABASE_URL = "postgresql://devstormk: Moneymaker1121*$@beacon-database.cefowseme3pk.us-east-1.rds.amazonaws.com"



