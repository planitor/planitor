import pprint

import requests
from parsel import Selector
from sqlalchemy.orm import contains_eager

from scrape.spiders.reykjavik_skipulagsrad import parse_minute_el

html = """<li>
<div class="field field-name-field-heiti-dagskrarlidar field-type-text-long field-label-hidden">
<div class="field-items">
<div class="field-item even">
<p>Hopp rafskútuleiga, &nbsp;&nbsp; &nbsp; &nbsp;&nbsp; &nbsp;Mál nr. US200204</p>
<p>Eyþór Máni Steinarsson og Ægir Þorsteinsson frá Hopp segja frá reynslunni af starfinu og tölfræði um notkun flotans.</p>
<p>Fulltrúar Samfylkingarinnar, Viðreisnar og Pírata leggja fram svohljóðandi bókun:</p>
<p>Meirihlutinn fagnar fjölbreyttum ferðamátum og tók nýrri tækni fagnandi þegar
rafskútur bættust í flóru vistvænna samgagna. Borgin hefur markvisst byggt upp
innviði fyrir samgönguhjólreiðar á síðustu árum og mun vera áframhaldandi samhliða
uppbyggingu borgalínu. Það verður gert með nýrri hjólreiðaáætlun, sem nú þegar er hafin vinna við. Kannanir er sýna fram á mikla fjölgun virkra notenda á hjólastígum borgarinnar. Við mætum auknum fjölda þeirra sem nýta sér virka ferðamáta ekki með boðum og bönnum heldur með betri innviðum og aukinni fjárfestingu.</p>
<p>Áheyrnarfulltrúi Flokks fólksins leggur fram svohljóðandi bókun:</p>
<p>Gríðarleg fjölgun er á notkun slíkrar hjóla. Fulltrúi Flokks fólksins hefur áhyggjur af slysum sem hafa orðið á þessum hjólum og kunna að verða. Nú þegar hafa verið skráð nokkur slys. Fulltrúi Flokks fólksins hefur áhyggjur af þróuninni í ljósi reynslu annarra þjóða. Velta má fyrir sér hvort skipulagsyfirvöld Reykjavíkurborgar, ásamt rafskútuleigum hafi unnið með og verið í samvinnu við samgöngustofu og lögreglu um þessi mál? Rafhjólin eru komin til að vera, ekki er um það deilt. Samkvæmt umferðarlögum mega „rafhlaupahjól eingöngu vera á gangstéttum og göngustígum, ekki á götum. Gangandi vegfarendur eiga alltaf réttinn á gangstéttum eða göngustígum. Hjólreiðamaður eða sá sem er á rafmagnshlaupahjóli á að víkja fyrir gangandi vegfarenda. Þá er hjálmaskylda fyrir alla undir 16 ára aldri. Einnig er bannað að keyra á þeim undir áhrifum áfengis“. Borgaryfirvöld eiga að gera allt sem í þeirra valdi stendur til að upplýsa um þessar reglur. Einnig er það á herðum skipulagsyfirvalda að sjá til þess að innviðir séu tilbúnir til að taka við þessari miklu fjölgun rafskútna/hjóla og að allar merkingar og skilti séu í lagi. Fulltrúi Flokks fólksins veltir fyrir sér hvort byrjað hafi verið á öfugum enda?</p>
<p>Eyþór Máni Steinarsson og Ægir Þorsteinsson frá Hopp tekur sæti á fundinum undir þessum lið.</p>
</div>
</div>
</div>
</li>"""


def get_rescraped_items(minutes):
    meeting = minutes[0].meeting
    text = requests.get(meeting.url).text
    for i, el in enumerate(Selector(text=text).css(".agenda-items>ol>li")):
        item = parse_minute_el(i + 1, el)
        for minute in minutes:
            if minute.case.serial == item["case_serial"]:
                yield item, minute


def fix_minutes():
    from planitor.database import db_context
    from planitor.models import Meeting, Minute
    from planitor.postprocess import get_subjects

    with db_context() as db:
        minutes = (
            db.query(Minute)
            .join(Meeting)
            .join(Minute.case)
            .options(contains_eager(Minute.case))
            .filter(Minute.meeting_id == 1072)
        )
        for item, minute in get_rescraped_items(minutes):
            for response in minute.responses:
                headline, contents = item["responses"][response.order]
                response.headline = headline
                response.contents = contents
                response.subjects = get_subjects(headline)
                db.add(response)
                db.commit()
            minute.inquiry = item["inquiry"]
            minute.remarks = item["remarks"]
            db.add(minute)
            db.commit()


if __name__ == "__main__":
    # pprint.pprint(parse_minute_el(1, Selector(html)))
    fix_minutes()
