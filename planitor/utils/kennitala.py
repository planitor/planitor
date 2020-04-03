"""Icelandic national registry codes made easy"""
import re
import random
from datetime import date, timedelta

__author__ = "Jakub Owczarski"
__version__ = "0.1.3"
__license__ = "MIT"


class Kennitala:
    """Icelandic national registry codes made easy"""

    def __init__(self, kennitala):
        self.kennitala = kennitala

    def __str__(self):
        if not self.validate():
            return "Invalid kennitala"
        return self.kennitala

    class Invalid(Exception):
        """Kennitala is not valid"""

    _age_prefix = {"8": "18", "9": "19", "0": "20"}
    _age_postfix = {v: k for k, v in _age_prefix.items()}

    @staticmethod
    def _compute_checkdigit(kennitala):
        """Computes checkdigit for (not necessarily complete) kennitala.
        Raises ValueError if random portion of kennitala is invalid.
        """
        multipliers = (3, 2, 7, 6, 5, 4, 3, 2)
        summed = 0
        for idx, multiplier in enumerate(multipliers):
            digit = int(kennitala[idx])
            summed += multiplier * digit

        mod = summed % 11
        if mod == 0:
            return "0"

        checkdigit = 11 - (summed % 11)
        if checkdigit == 10:
            raise ValueError

        return str(checkdigit)

    def _extract_date_parts(self):
        """Returns year, month and day from the kennitala"""
        age_prefix = Kennitala._age_prefix[self.kennitala[-1]]

        day = int(self.kennitala[:2])
        month = int(self.kennitala[2:4])
        year = int(age_prefix + self.kennitala[4:6])

        if 41 <= day <= 71:
            day = day - 40

        return year, month, day

    @staticmethod
    def generate(birth_date, person=True):
        """Returns valid kennitala for a given birth_date.
        If person is True it's personal kennitala
        otherwise it's company kennitala.
        """
        full_year = str(birth_date.year)
        year = full_year[-2:]
        age_postfix = Kennitala._age_postfix[full_year[:2]]
        month = str(birth_date.month).rjust(2, "0")
        if person:
            day = str(birth_date.day).rjust(2, "0")
        else:
            day = str(birth_date.day + 40)

        kennitala = None

        def get_rand():
            return random.randint(20, 99)

        rnd = get_rand()

        while kennitala is None:
            try_kennitala = day + month + year + str(rnd)
            try:
                checkdigit = Kennitala._compute_checkdigit(try_kennitala)
                kennitala = try_kennitala
            except ValueError:
                rnd = get_rand()

        kt_no = kennitala + checkdigit + age_postfix
        return kt_no

    @staticmethod
    def random(start=None, end=None, person=True):
        """Generate random kennitala for given date range.
        Default range is [1900-01-01, today] inclusive.
        This is pretty memory intensive for large ranges.
        """
        start = start or date(1900, 1, 1)
        end = end or date.today()

        if start > end:
            raise ValueError("Start must not be > end")
        if start == end:
            return Kennitala.generate(start)
        days = (end - start).days
        birth_date = start + timedelta(days=random.choice(range(days + 1)))
        return Kennitala.generate(birth_date, person)

    @staticmethod
    def is_valid(kennitala):
        """Returns True if kenntiala is valid, False otherwise"""
        return Kennitala(kennitala).validate()

    @staticmethod
    def is_personal(kennitala):
        """Returns True if kennitala is personal, False if company
        or Raises Kennitala.Invalid.
        """
        return Kennitala(kennitala).is_person()

    @staticmethod
    def to_date(kennitala):
        """Returns birth date or raises Kennitala.Invalid"""
        return Kennitala(kennitala).get_birth_date()

    def validate(self):
        """Returns True if kennitala is valid, False otherwise"""
        if not self.kennitala:
            return False

        pattern = r"\d{6}\-?\d{4}"
        if not re.match(pattern, self.kennitala):
            return False

        kennitala = self.kennitala.replace("-", "")

        if not kennitala[-1] in Kennitala._age_prefix:
            return False

        year, month, day = self._extract_date_parts()

        try:
            date(year, month, day)
            checkdigit = Kennitala._compute_checkdigit(kennitala)
            return kennitala[-2] == checkdigit
        except ValueError:
            return False

    def get_birth_date(self):
        """Return birth date or raise Kennitala.Invalid"""
        if not self.validate():
            raise Kennitala.Invalid()

        year, month, day = self._extract_date_parts()
        return date(year, month, day)

    def is_person(self):
        """Returns True if kennitala belongs to person.
        False if belongs to company.
        or Raises Kennitala.Invalid.
        """
        if not self.validate():
            raise Kennitala.Invalid

        return int(self.kennitala[0]) <= 3

    def only_digits(self):
        """Returns kennitala without '-' or raises Kennitala.Invalid"""
        if not self.validate():
            raise Kennitala.Invalid

        return self.kennitala.replace("-", "")

    def with_dash(self):
        """Returns kennitala with dash after date part.
        Raises Kennitala.Invalid if invalid.
        """
        if not self.validate():
            raise Kennitala.Invalid
        if "-" in self.kennitala:
            return self.kennitala
        return "{0}-{1}".format(self.kennitala[:6], self.kennitala[6:])
