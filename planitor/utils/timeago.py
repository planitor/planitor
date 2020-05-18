import datetime as dt


def pluralized(count, singular, plural):
    if count == 1:
        return singular
    return plural


def timeago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = dt.datetime.now()
    if type(time) is int:
        diff = now - dt.datetime.fromtimestamp(time)
    elif isinstance(time, dt.datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

    def formatter(count, singular, plural):
        return singular.format(count) if count == 1 else plural.format(count)

    if day_diff == 0:
        if second_diff < 10:
            return "Rétt í þessu"
        if second_diff < 60:
            return formatter(
                int(second_diff), "Fyrir {} sekúndu síðan", "Fyrir {} sekúndum síðan"
            )
        if second_diff < 120:
            return "Fyrir um mínútu síðan"
        if second_diff < 3600:
            return formatter(
                int(second_diff / 60), "Fyrir {} mínútu síðan", "Fyrir {} mínútum síðan"
            )
        if second_diff < 7200:
            return "Fyrir um klukkutíma síðan"
        if second_diff < 86400:
            return formatter(
                int(second_diff / 3600),
                "Fyrir {} klukkutíma síðan",
                "Fyrir {} klukkutímum síðan",
            )
    if day_diff == 1:
        return "Í gær"
    if day_diff < 7:
        return formatter(int(day_diff), "Fyrir {} degi síðan", "Fyrir {} dögum síðan",)
    if day_diff < 31:
        return formatter(
            int(day_diff / 7), "Fyrir {} viku síðan", "Fyrir {} vikum síðan",
        )
    if day_diff < 365:
        return formatter(
            int(day_diff / 30), "Fyrir {} mánuði síðan", "Fyrir {} mánuðum síðan",
        )
    return formatter(int(day_diff / 365), "Fyrir {} ári síðan", "Fyrir {} árum síðan",)
