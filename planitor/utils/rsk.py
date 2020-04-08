import requests

RSK_DOMAIN = "https://www.rsk.is"


def get_kennitala_from_rsk_search(name):
    """ The RSK search either displays results, or if there is only one result you are
    redirected directly to the company page. We can use the Location header to pick up
    the kennitala.

    """
    name = name.lower().rstrip(".")
    url = "{}/fyrirtaekjaskra/leit?nafn={}".format(RSK_DOMAIN, name.replace(" ", "+"))
    response = requests.get(url, allow_redirects=False)
    if response.status_code == 302:
        location = response.headers["location"]
        _, kennitala = location.rsplit("/", 1)
        return kennitala


unmatched = """
Lota ehf.
Sími hf.
Landslag ehf.
Arkís arkitektar ehf.
Hampiðja hf.
Faxaflóahafnar sf.
Faxaflóahafið sf.
Stika ehf.
Artíka ehf.
Stiki ehf.
Guðmundur Jónasson ehf.
Atelier Arkitektar ehf.
Ark teiknistofa sf.
Gult hús ehf.
Eon arkitektar ehf.
Kanon arkitektar ehf.
Verkís hf.
Límtré Vírnet hf.
Hjólbarðaverkstæði Sigurjóns ehf.
Skólavörðustígur 2 ehf.
Kurt og Pí ehf.
Noland Arkitektar ehf.
Guðjónssonar og félagi ehf.
Arkitektar ehf.
Arkhússins ehf.
Björgun ehf.
Askur Arkitekta ehf.
Yddur arkitektar ehf.
Malbikunarstöð Höfði hf.
Ottó ehf.
Pkdm Arkitektar ehf.
Kamata ehf.
Teiknistofa Storð ehf.
Stáss Design ehf.
Gráberg ehf.
Askur Arkitektar ehf.
Zeppelin ehf.
Zeppelin arkitektar ehf.
Gríma Arkitekta ehf.
On The Olfus ehf.
Teiknistofa Óðinstorgi Hh ehf.
Almennt E slhf.
Noland arkitektar ehf.
Kristið Ragnarssonar arkitekt ehf.
Teiknistofa Stika ehf.
Studio Grandi ehf.
Þingvangur ehf.
Eignatorg ehf.
Stéttafélag ehf.
Krads ehf.
Verksýn ehf.
Landsbanki hf.
Reitir ehf.
Sjónvers ehf.
Kvika ehf.
Eflu ehf.
Mítas ehf.
Fasteignafélag Langeyri ehf.
Íshamrar ehf.
Fjarðarafl ehf.
Urban arkitektar ehf.
Íþök fasteignir ehf.
Askur arkitektar ehf.
Úti og inni sf.
Argos ehf.
Arkitektar Laugavegi 164 ehf.
Róbertssonar fyrir Airmango ehf.
Arkís Arkitektar ehf.
Vsó ráðgjöf ehf.
Pl ehf.
Tannheils ehf.
Dyrhólma ehf.
Hraunhólmi ehf.
Bílaleiga Ísak ehf.
Ívar Hauksson ehf.
Perla Properties ehf.
Karl Mikla ehf.
Gríma arkitektar ehf.
Steinbrekka ehf.
Mannvirkjameistari ehf.
101 fasteignir ehf.
55 ehf.
Arkitektar Laugavegur 164 ehf.
Og ehf.
Mansard teiknistofa ehf.
Andrúm arkitektar ehf.
Bréf Studio Grandi ehf.
Klettur ehf.""".splitlines()

if __name__ == "__main__":
    import time

    for name in unmatched:
        name = name.strip(" \r")
        if not name:
            continue
        kennitala = get_kennitala_from_rsk_search(name)
        time.sleep(2)
        if kennitala:
            print("{}: {}".format(kennitala, name))
