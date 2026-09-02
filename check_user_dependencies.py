from database.connection import engine
from sqlalchemy import text

TEST_USER_IDS = (10, 11, 12, 13)

with engine.begin() as connection:
    result = connection.execute(
        text("DELETE FROM users WHERE user_id IN :user_ids").bindparams(
            __import__("sqlalchemy").bindparam(
                "user_ids",
                expanding=True
            )
        ),
        {"user_ids": TEST_USER_IDS},
    )

    print("USERS DELETED:", result.rowcount)