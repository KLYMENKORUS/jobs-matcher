__all__ = (
    "RequiredField",
    "RequiredTypedField",
    "BaseAttributeAccessor",
    "P",
    "TypeFunction",
)

import functools
import typing as t

P = t.ParamSpec("P")
TypeFunction = t.Callable[..., t.Any]


class BaseAttributeAccessor[T]:
    """
    Base for method decorators that need the bound instance (`self.instance`).

    `T` is the decorated coroutine's return type, so callers keep a typed result.
    """

    def __init__(self, function: t.Callable[..., t.Awaitable[T]]) -> None:
        # ------------------------------------------------------------------------ #
        functools.update_wrapper(wrapper=self, wrapped=function)
        # ------------------------------------------------------------------------ #
        self.function: t.Callable[..., t.Awaitable[T]] = function
        # ------------------------------------------------------------------------ #
        self.instance: t.Any | None = None
        # ------------------------------------------------------------------------ #

    async def __call__(self, *args: t.Any, **kwargs: t.Any) -> T:
        raise NotImplementedError

    def __get__(self, instance: t.Any, owner: type[t.Any] | None = None) -> t.Self:
        if instance is None:
            return self
        bound: t.Callable[..., t.Awaitable[T]] = self.function.__get__(
            instance, owner
        )
        (new_instance := self.__class__(bound)).instance = instance
        return new_instance


class RequiredField:
    def __init__(self) -> None:
        # ------------------------------------------------------------------------ #
        self._private_name: str | None = None
        # ------------------------------------------------------------------------ #

    def __set_name__(self, owner: type[t.Any], name: str) -> None:
        self._private_name = name

    def __get__(self, instance: t.Any, owner: type[t.Any] | None = None) -> t.Any:
        if instance is None:
            return self
        if (value := instance.__dict__.get(self._private_name)) is None:
            raise AttributeError(
                f"The required field '{self._private_name}' is not set."
            )
        return value

    def __set__(self, instance: t.Any, value: t.Any) -> None:
        instance.__dict__[self._private_name] = value


class RequiredTypedField[T](RequiredField):
    """
    `RequiredField` that also checks the type on assignment.

    Declare it unannotated — `search = RequiredTypedField(expected_type=Search)` —
    and type checkers read `obj.search` as `Search`.
    """

    # `| Callable[..., T]` lets abstract classes through (mypy `type-abstract`)
    # while still inferring `T` from the argument
    def __init__(self, *, expected_type: type[T] | t.Callable[..., T]) -> None:
        super().__init__()
        # ------------------------------------------------------------------------ #
        self._expected_type: type[t.Any] = t.cast(type[t.Any], expected_type)
        # ------------------------------------------------------------------------ #

    @t.overload
    def __get__(
        self, instance: None, owner: type[t.Any] | None = None
    ) -> t.Self: ...

    @t.overload
    def __get__(self, instance: object, owner: type[t.Any] | None = None) -> T: ...

    def __get__(self, instance: t.Any, owner: type[t.Any] | None = None) -> t.Any:
        return super().__get__(instance, owner)

    def __set__(self, instance: t.Any, value: T) -> None:
        if not isinstance(value, self._expected_type):
            raise TypeError(
                f"Expected value of type '{self._expected_type.__name__}' for field "
                f"'{self._private_name}', got '{type(value).__name__}' instead."
            )
        super().__set__(instance, value)
