import requests

RSK_DOMAIN = "https://www.rsk.is"


def get_kennitala_from_rsk_search(name):
    """ The RSK search either displays results, or if there is only one result you are
    redirected directly to the company page. We can use the Location header to pick up
    the kennitala.

    """
    name = name.lower().rstrip(".").replace("—", "-").replace("–", "-")
    url = "{}/fyrirtaekjaskra/leit?nafn={}".format(RSK_DOMAIN, name.replace(" ", "+"))
    response = requests.get(url, allow_redirects=False)
    if response.status_code == 302:
        location = response.headers["location"]
        _, kennitala = location.rsplit("/", 1)
        return kennitala
