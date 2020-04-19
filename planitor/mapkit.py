import datetime as dt

import jwt


def get_token(private_key):

    epoch = dt.datetime.utcfromtimestamp(0)
    time_iat = (dt.datetime.utcnow() - epoch).total_seconds()
    time_expt = time_iat + 15552000  # 180 days

    key_id = "9827345QC8"
    team_id = "RDC8539AWM"

    private_key = ("-----BEGIN PRIVATE KEY-----\n{}\n-----END PRIVATE KEY-----").format(
        private_key
    )

    return jwt.encode(
        {
            "iss": team_id,
            "iat": int(time_iat),
            "exp": int(time_expt),
            # "origin": "http://barmahlid.solberg.is:5000",
        },
        key=private_key,
        algorithm="ES256",
        headers={"kid": key_id, "typ": "JWT", "alg": "ES256"},
    )
