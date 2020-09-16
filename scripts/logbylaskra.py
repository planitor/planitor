import csv
import sqlite3
from io import TextIOWrapper
from urllib.request import urlopen

DBNAME = "logbylaskra.db"

"""
The source file has header top line and every line has confusing headers

"Lögbýlaskrá 2019";
"0000 Reykjavíkurborg";
"Svfél.";
"Heiti lögbýlislis";
"Landnúmer";
"Eyðibýli";
"Eigandi / ÁbúandiEigandi / Ábúandi";
"Nafn";
"0000";
"Arnarholt";
125651;
"nei";
"E";
"Reykjavíkurborg"

"""

LOGBYLASKRA_LINK = (
    "https://opingogn.is/dataset/a5c31d0f-9639-4bdc-beb3-298b2165e1ee"
    "/resource/821c80b9-8d10-4fcc-9b10-b7023634f55a/download/report-2019.csv"
)

SOURCE_COLUMNS = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    "sveitarfelag",
    "name",
    "landnr",
    "abandoned",
    "category",  # E eigandi, Á ábúandi
    "owner",
]

DESTINATION_COLUMNS = SOURCE_COLUMNS[-6:]


def insert_row(row, dbconn):
    c = dbconn.cursor()
    c.execute("INSERT INTO logbylaskra VALUES (?,?,?,?,?,?,?)", row)


def create_db(path):
    dbconn = sqlite3.connect(path)

    create_table_sql = """
    CREATE TABLE logbylaskra (
        id INTEGER UNIQUE PRIMARY KEY NOT NULL,
        landnr INTEGER,
        sveitarfelag INTEGER,
        name TEXT,
        abandoned BOOL,
        category TEXT,
        owner TEXT
    );
    """

    dbconn.cursor().execute(create_table_sql)
    return dbconn


def read_rows(fp):
    reader = csv.reader(fp, delimiter=";")
    for i, row in enumerate(reader):
        sveitarfelag, name, landnr, abandoned, category, owner = row[
            -6:
        ]  # See `SOURCE_COLUMNS`
        landnr = int(landnr)
        abandoned = abandoned != "nei"
        yield i, landnr, sveitarfelag, name, abandoned, category, owner


def get_rows():
    with urlopen(LOGBYLASKRA_LINK) as fp:
        with TextIOWrapper(fp, "latin-1") as fp:
            for row in read_rows(fp):
                yield row


if __name__ == "__main__":
    dbconn = create_db("logbylaskra.db")
    for row in get_rows():
        insert_row(row, dbconn)
        dbconn.commit()
