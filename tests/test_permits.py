import decimal

from planitor import permits
from planitor.models import Minute

D = decimal.Decimal


def test_get_area_from_minute_excludes_b_rymi():
    inquiry = """Sótt er um leyfi til að byggja tveggja hæða tvíbýlishús úr steinsteyptum einingum á lóð nr. 6 við Gefjunarbrunn.
Útskrift úr gerðabók embættisafgreiðslufundar skipulagsfulltrúa frá 3. júlí 2020 fylgir erindi, ásamt umsögn skipulagsfulltrúa dags. 3. júlí 2020. Einnig fylgir bréf skipulagsfulltrúa dags. 6. júlí 2020.
Stærð, A-rými: 230 ferm., 767,8 rúmm.
B-rými: 49,2 ferm.
Gjald kr. 11.200 """
    minute = Minute(inquiry=inquiry)
    assert permits.PermitMinute(minute).area_added == D("230.0")


def test_get_area_from_minute():
    inquiry = """Sótt er um leyfi til þess að breyta innra skipulagi á 2. hæð og bæta við glugga til austurs,  og byggja einnar hæða viðbyggingu, gangrými, sem tengir saman hús á lóðum nr. 24 - 26 við skrifstofu- og verslunarhús á lóð nr. 22 við Grensásveg.
Útskrift úr gerðabók embættisafgreiðslufundar skipulagsfulltrúa frá 3. júlí 2020 fylgir erindi, ásamt bréfi skipulagsfulltrúa dags. 6. júlí 2020.
Erindi fylgir samþykki eigenda húss nr. 22-26, dags. 11. maí 2020.
Útskrift úr gerðabók embættisafgreiðslufundar skipulagsfulltrúa frá 4. september 2020 fylgir erindi, ásamt bréfi skipulagsfulltrúa dags. 8. september 2020.
Erindi var grenndarkynnt fyrir hagsmunaaðilum að Grensásvegi 24 og 26. Lagt var fram samþykki eiganda Grensásvegs 24 og 26, dags. 11. maí 2020.
Stækkun: 16.1 ferm., 46.4 rúmm.
Gjald kr. 11.200"""
    minute = Minute(inquiry=inquiry)
    assert permits.PermitMinute(minute).area_added == D("16.1")


def test_get_area_from_minute_with_totals_ignored():
    inquiry = """Sótt er um leyfi til að byggja viðbyggingu sem hýsa mun vöru- og frystigeymslu ásamt tengigangi vestan við kjötvinnslu á byggingareit B á lóð 125744 Saltvík.
Erindi fylgir minnisblað um brunavarnir dags. 19. október 2020.
Stækkun: 2.366,2 ferm., 17.768,3 rúmm.
Eftir stækkun, A-rými: 8.685,3 ferm., 48.683,6 rúmm.,
B-rými: 178,8 ferm., 861,8 rúmm.
Samtals: 8.864,1 ferm., 48.925,4 rúmm.
Gjald kr. 11.200 """
    minute = Minute(inquiry=inquiry)
    assert permits.PermitMinute(minute).area_added == D("2366.2")
