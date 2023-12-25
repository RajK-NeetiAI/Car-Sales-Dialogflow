import sqlite3
from datetime import datetime

conn = sqlite3.connect("test.db")

conn.execute('''CREATE TABLE IF NOT EXISTS CHATHISTORY
         (ID INTEGER PRIMARY KEY AUTOINCREMENT,
         QUERY TEXT NOT NULL,
         RESPONSE TEXT NOT NULL,
         SESSIONID TEXT NOT NULL,
         CREATEDAT TEXT NOT NULL);''')


def add_conversation(query: str, response: str, session_id: str) -> None:
    created_at = datetime.now()
    conn.execute(
        f"INSERT INTO CHATHISTORY (QUERY, RESPONSE, SESSIONID, CREATEDAT) \
VALUES ('{query}', '{response}', '{session_id}', '{created_at}');")
    conn.commit()
    print('Conversation added.')
