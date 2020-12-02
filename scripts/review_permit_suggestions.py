from typing import Iterator, Tuple, Optional
import typer
from tabulate import tabulate

from planitor.models import Minute, Meeting
from planitor.permits import PermitMinute
from planitor.database import db_context


headers = ["id", "address", "added", "subtracted", "building", "permit", "url"]
RowType = Tuple[int, str, Optional[float], Optional[float], str, str, str]


def rows(offset: int, limit: int) -> Iterator[RowType]:
    with db_context() as db:
        query = (
            db.query(Minute)
            .join(Meeting)
            .filter(Minute.remarks.op("~")("160 ?/ ?2010"))
            .order_by(Meeting.start.desc())
            .offset(offset)
            .limit(limit)
        )
        for minute in query:
            pm = PermitMinute(minute)
            area_added, area_subtracted = pm.get_area()
            building_type = pm.get_building_type()
            permit_type = pm.get_permit_type()

            if not any((area_added, area_subtracted, building_type, permit_type)):
                continue

            yield (
                minute.id,
                minute.case.iceaddr,
                area_added,
                area_subtracted,
                (building_type.value.label if building_type else ""),
                (permit_type.value.label if permit_type else ""),
                f"http://localhost:5000/minutes/{minute.id}",
            )


def main(offset: int = 0, limit: int = 100):
    print(tabulate(list(rows(offset, limit)), headers=headers))


if __name__ == "__main__":
    typer.run(main)
