__all__ = ("BaseSourceApiRequestData",)

import abc
import typing as t
from http import HTTPMethod

from app.shared.utils.descriptors import RequiredTypedField


class BaseSourceApiRequestData:
    url = RequiredTypedField(expected_type=str)

    ################################################################################
    class BaseSourceEndpointData(abc.ABC):
        http_method = RequiredTypedField(expected_type=HTTPMethod)

        # `*args: Any, **kwargs: Any` lets each endpoint declare its own
        # keyword-only signature (mypy treats it as a gradual signature)
        @abc.abstractmethod
        def get_url(self, *args: t.Any, **kwargs: t.Any) -> str:
            pass

        @classmethod
        def prepare_params(cls, **kwargs: t.Any) -> dict[str, t.Any]:
            return {key: value for key, value in kwargs.items() if value is not None}

    ################################################################################
