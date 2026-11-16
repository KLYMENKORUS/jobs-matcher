__all__ = ("HtmlFormatter",)

import typing as t


class HtmlFormatter:

    @staticmethod
    def _put_in_tag(*, tag: str, text: str) -> str:
        return f"<{tag}>{text}</{tag}>"

    @classmethod
    def bold(cls, *, text: t.Any) -> str:
        return cls._put_in_tag(tag="b", text=str(text))

    @classmethod
    def italic(cls, *, text: t.Any) -> str:
        return cls._put_in_tag(tag="i", text=str(text))

    @classmethod
    def code(cls, *, text: t.Any) -> str:
        return cls._put_in_tag(tag="code", text=str(text))

    @classmethod
    def code_block(cls, *, text: t.Any) -> str:
        return cls._put_in_tag(
            tag="pre", text=f"<code class='language-python'>{text}</code>"
        )

    @classmethod
    def spoiler(cls, *, text: t.Any) -> str:
        return cls._put_in_tag(tag="tg-spoiler", text=str(text))

    @classmethod
    def link(cls, *, url: str, text: t.Any) -> str:
        return f"<a href='{url}'>{text}</a>"
