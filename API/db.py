import sqlite3

conn = sqlite3.connect("cleansing.sqlite")

cursor = conn.cursor()

sql_text = """ CREATE TABLE text_cleansing (
    id integer PRIMARY KEY,
    input_text text,
    text_cleansing text
)"""

sql_abusive = """CREATE TABLE abusive(
    ABUSIVE text
)"""

sql_alay = """CREATE TABLE replace_alay(
    ALAY text,
    TIDAK_ALAY text
)"""

cursor.execute("DROP TABLE IF EXISTS abusive")
cursor.execute("DROP TABLE IF EXISTS text_cleansing")
cursor.execute("DROP TABLE IF EXISTS replace_alay")
cursor.execute("DROP TABLE IF EXISTS tweet_cleansing")
cursor.execute(sql_text)
#cursor.execute(sql_abusive)
#cursor.execute(sql_alay)
