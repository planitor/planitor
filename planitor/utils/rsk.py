import time

import requests

RSK_DOMAIN = "https://www.rsk.is"
DISCLAIMER_URL = "/notkunarskilmalar/"
MAX_RETRIES = 3


def get_kennitala_from_rsk_search(name, max_retries=MAX_RETRIES):
    """The RSK search either displays results, or if there is only one result you are
    redirected directly to the company page. We can use the Location header to pick up
    the kennitala.

    """
    name = name.lower().rstrip(".").replace("—", "-").replace("–", "-")
    url = "{}/fyrirtaekjaskra/leit?nafn={}".format(RSK_DOMAIN, name.replace(" ", "+"))

    def perform_request(retry):
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers["location"]
            if location == RSK_DOMAIN + DISCLAIMER_URL:
                # Redirected to a disclaimer if we do an identical lookup
                retry = retry + 1
                if retry < max_retries:
                    time.sleep(2 * retry)  # Linearly increasing backoff
                    return perform_request(retry)
                else:
                    return None
            _, kennitala = location.rsplit("/", 1)
            return kennitala

    return perform_request(retry=0)
