import json
import os
from planitor.models import Meeting, Minute

finished = """borgarrad-3417.json
skipulagsrad-636.json
skipulagsrad-266.json
skipulagsrad-289.json
byggingarfulltrui-458.json
skipulagsrad-323.json
borgarrad-3552.json
byggingarfulltrui-771.json
borgarrad-3381.json
byggingarfulltrui-634.json
skipulagsrad-231.json
borgarstjorn-1823.json
skipulagsrad-661.json
borgarrad-3440.json
byggingarfulltrui-819.json
borgarrad-3505.json
skipulagsrad-374.json
skipulagsrad-724.json
byggingarfulltrui-376.json
byggingarfulltrui-726.json
byggingarfulltrui-663.json
byggingarfulltrui-399.json
borgarrad-3293.json
borgarrad-3339.json
borgarstjorn-1659.json
borgarrad-3456.json
skipulagsrad-677.json
borgarstjorn-1835.json
skipulagsrad-227.json
byggingarfulltrui-419.json
skipulagsrad-698.json
skipulagsrad-362.json
borgarrad-3513.json
byggingarfulltrui-730.json
byggingarfulltrui-360.json
borgarrad-3285.json
byggingarfulltrui-675.json
skipulagsrad-270.json""".splitlines()


def main(db):
    for filename in os.listdir("../hfjfix/dumps")[::-1]:
        if filename in finished:
            print("Skipping", filename)
            continue
        with open(f"../hfjfix/dumps/{filename}") as fp:
            item = json.loads(fp.read())

        url = item["url"]
        minutes = item["minutes"]
        meeting = db.query(Meeting).filter(Meeting.url == url).first()
        if meeting is None:
            print("Could not find", url)
            continue
        for minute in minutes:
            db_minute = (
                db.query(Minute)
                .filter(Minute.meeting == meeting, Minute.serial == minute["serial"])
                .first()
            )
            if db_minute is None:
                continue
            db_minute.remarks = minute["remarks"]
            db_minute.inquiry = minute["inquiry"]
            db.add(db_minute)
        db.commit()
        print("Updated:", filename, meeting.url)


if __name__ == "__main__":
    from planitor.database import db_context

    with db_context() as db:
        main(db)
