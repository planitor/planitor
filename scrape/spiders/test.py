import pprint
from parsel import Selector
from scrape.spiders.reykjavik_skipulagsrad import parse_minute_el

html = """<li>
<div class="field field-name-field-heiti-dagskrarlidar field-type-text-long field-label-hidden">
<div class="field-items">
<div class="field-item even">
<p>Heklureitur - Laugavegur 168 og 170-174, nýtt deiliskipulag&nbsp;&nbsp; &nbsp; (01.242)&nbsp;&nbsp; &nbsp;Mál nr. SN190730<br>
600169-5139 Hekla hf., Pósthólf 5310, 125 Reykjavík<br>
560997-3109 Yrki arkitektar ehf, Mýrargötu 26, 101 Reykjavík</p>

<p>Lögð fram umsókn Yrki arkitekta ehf. dags. 9. desember 2019 um nýtt deiliskipulag
fyrir Lóðirnar að Laugavegi 168 og 170-174, Heklureitur. Í tillögunni felst að
lóðinni Laugavegur 170-174 verði skipt í tvennt og vestari hluti hennar verði
lóðirnar Laugavegur 170 og 172. Lóðirnar nr. 168 og 172 verði nýttar undir allt að
250 íbúðir. Valkvæð heimild er um að lóðin nr. 168 verði nýtt undir gististarfsemi.
Eystri hluti lóðarinnar Laugavegur 170-174 verður Laugavegur 174. Heimilt verðu að
auka byggingarmagn á lóðinni, byggja þrjár hæðir ofan á núverandi byggingar og byggja
við 3. hæð norðurhliðar núverandi álmu við Laugaveg. Nýju hæðirnar og viðbyggingin eru
undir atvinnustarfsemi. Valkvæð heimild er um að nýja byggingarmagnið verði nýtt undir
allt að 90 íbúðir. Gert er ráð fyrir sex hæða bílgeymsluhúsi og núverandi byggingar verða
nýttar undir atvinnustarfsemi. Á öllum lóðum er gert ráð fyrir verslun og þjónustu á
jarðhæð, samkvæmt uppdr. Yrki arkitekta ehf. dags. 10. janúar 2020. Einnig er lögð fram
umsögn skipulagsfulltrúa dags. 2. júlí 2020.</p>

<p>
Samþykkt, með fjórum greiddum atkvæðum, fulltrúa Samfylkingarinnar, Viðreisnar og
Pírata, að synja beiðni um breytingu á deiliskipulagi með vísun til umsagnar
skipulagsfulltrúa dags. 2. júlí 2020. Fulltrúar Sjálfstæðisflokksins sitja hjá.<br>
Vísað til borgarráðs.</p>
<p>Fulltrúar Sjálfstæðisflokksins leggja fram svohljóðandi bókun:</p>
<p>Skipulag Heklureits er algeru uppnámi en meira en þrjú ár eru síðan borgin gerði viljayfirlýsingu um uppbyggingu á reitnum. Samskipti borgarinnar við þróunaraðila hafa verið stirð og lítil. Nú er borgin að hafna hugmyndum lóðarhafa og uppbygging sett enn frekar á ís.&nbsp;</p>
<p>Áheyrnarfulltrúi Miðflokksins leggur fram svohljóðandi bókun:</p>
<p>Að hafna þessari umsókn á breytingu á deiliskipulagi á Heklureit er valdníðsla stjórnvaldsins Reykjavíkurborgar á hendur einkaaðila gæti hugsanlega verið brot á eignarétti og yfirráðum eigna í þessu tilfelli lóðar. Í borgarráði þann 25. júní sl. var afturkölluð viljayfirlýsing frá 3. maí 2017 um samstarf milli borgarinnar og Heklu hf. vegna fyrirhugaðs flutnings fyrirtækisins í Suður Mjódd og þróun lóða félagsins við Laugaveg, samhliða flutningi á starfsemi þess. Afturköllunin var ákveðin í ljósi þess að samþykktar voru breyttar skipulagsáætlanir fyrir lóðir Heklu hf að Laugavegi og af því að ekki voru skilgreind ákvæði um uppbyggingarhraða í Suður Mjódd innan 2 ára frá undirritun viljayfirlýsingarinnar. Engin niðurstaða er því í málinu, nema sú að málið er á byrjunarreit og er til þess fallin að hrekja fyrirtækið úr borginni. Þetta mál er dæmalaust klúður að hálfu borgarinnar.&nbsp;</p>
<p>Fulltrúar Samfylkingarinnar, Viðreisnar og Pírata leggja fram svohljóðandi gagnbókun:</p>
<p>Sveitarfélög fara með ábyrgð á skipulagi alls lands innan sinna marka. Umrædd lóð er á lykilsvæði á nýjum þróunarás og fyrsta áfanga borgarlínu og því mikilvægt að vel til takist. Uppbyggingin þarf að taka mið af aðalskipulagi og framtíðaruppbyggingu innan borgarinnar. Það er ekki valdníðsla að samþykkja ekki allar hugmyndir sem koma frá lóðarhöfum heldur ábyrgð yfirvalda að skipuleggja byggt umhverfi á sjálfbæran hátt með þarfir núverandi og komandi kynslóðir í huga.</p>
<p>Björn Ingi Edvardsson verkefnastjóri tekur sæti á fundinum undir þessum lið.</p>
</div>
</div>
</div>
<p>Fylgigögn
</p><ul><li><img class="file-icon" alt="PDF icon" title="application/pdf" src="/modules/file/icons/application-pdf.png"><a href="https://fundur.reykjavik.is/sites/default/files/agenda-items/heklureitur_-_laugavegur_168_og_170-174.pdf" type="application/pdf; length=52462763" title="heklureitur_-_laugavegur_168_og_170-174.pdf">Heklureitur - Laugavegur 168 og 170-174</a></li>
</ul></li>"""

if __name__ == "__main__":
    pprint.pprint(parse_minute_el(1, Selector(html)))
