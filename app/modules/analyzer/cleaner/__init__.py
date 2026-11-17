__all__ = ("TextCleaner",)

import html
import re
import typing as t


class TextCleaner:
    """
    Squeezes texts before they go to the AI: the CV is sent with every vacancy,
    so every line cut from it is saved on each request.

    - CV: contacts (email, phone, links) are dropped - they cost tokens, say
      nothing about the fit and should not leave the server;
    - vacancy: html leftovers are dropped;
    - both: bullets, repeated spaces / lines and empty lines are dropped, the
      text is cut on a line boundary.
    """
    _FLAGS: t.Final[re.RegexFlag] = re.IGNORECASE | re.VERBOSE

    # "Email:", "Tel.", ... in front of a contact go together with it
    _LABEL: t.Final[str] = r"""
        (?:
            \b
            (?: e-?mail | phone | tel | mob(?:ile)? | linkedin | github
              | telegram | skype | пошта | телефон | тел )
            \.? [ \t]* :? [ \t]*
        )?
    """
    _EMAIL: t.Final[re.Pattern[str]] = re.compile(
        pattern=_LABEL + r"""
            [\w.+-]+            # local part
            @
            [\w-]+              # domain
            (?: \.[\w-]+ )+     # .com, .com.ua, ...
        """,
        flags=_FLAGS,
    )
    _URL: t.Final[re.Pattern[str]] = re.compile(
        pattern=_LABEL + r"""
            (?:
                https?://
              | www\.
              | \b (?: linkedin\.com | github\.com | gitlab\.com | t\.me ) /  # no scheme
            )
            \S*
        """,
        flags=_FLAGS,
    )
    _PHONE: t.Final[re.Pattern[str]] = re.compile(
        pattern=_LABEL + r"""
            \+? \(?
            \d
            [\d \t()-]{8,}      # no dots: 01.2019 - 05.2021 is never a phone;
                                # no newlines: never glued to the next line
            \d
        """,
        flags=_FLAGS,
    )
    _MIN_PHONE_DIGITS: t.Final[int] = 10

    # block tags end a line, inline ones (<b>, <a>, ...) only separate words
    _HTML_BLOCK_TAG: t.Final[re.Pattern[str]] = re.compile(
        pattern=r"""
            </?
            (?: p | br | div | li | ul | ol | tr | h[1-6] ) \b
            [^>]*
            >
        """,
        flags=_FLAGS,
    )
    _HTML_TAG: t.Final[re.Pattern[str]] = re.compile(r" < [^>]+ > ", _FLAGS)
    # leading list markers: spaces, bullets, stars and dashes
    _BULLET: t.Final[re.Pattern[str]] = re.compile(r" ^ [\s•●▪◦·○■□►✓✔*–—-]+ ", _FLAGS)
    # spaces, tabs and non-breaking spaces
    _SPACES: t.Final[re.Pattern[str]] = re.compile(r" [ \t ]+ ", _FLAGS)

    @classmethod
    def clean_cv(cls, text: str, *, max_chars: int) -> str:
        text = cls._EMAIL.sub(" ", text)
        text = cls._URL.sub(" ", text)
        text = cls._PHONE.sub(cls._drop_phone, text)
        return cls._squeeze(text, max_chars=max_chars)

    @classmethod
    def clean_vacancy(cls, text: str, *, max_chars: int) -> str:
        text = cls._HTML_BLOCK_TAG.sub("\n", html.unescape(text))
        text = cls._HTML_TAG.sub(" ", text)
        return cls._squeeze(text, max_chars=max_chars)

    @classmethod
    def _drop_phone(cls, match: re.Match[str]) -> str:
        digits: int = sum(char.isdigit() for char in match.group())
        return " " if digits >= cls._MIN_PHONE_DIGITS else match.group()

    @classmethod
    def _squeeze(cls, text: str, *, max_chars: int) -> str:
        lines: list[str] = []
        for raw in text.splitlines():
            line: str = cls._SPACES.sub(" ", cls._BULLET.sub("", raw)).strip(" ,;|")
            if any(char.isalnum() for char in line) and line not in lines:
                lines.append(line)

        result: str = "\n".join(lines)
        if len(result) <= max_chars:
            return result

        cut: str = result[:max_chars]
        return cut[: cut.rfind("\n")] if "\n" in cut else cut
