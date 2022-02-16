from typing import Optional, Union
from webargs import validate


class MultipleOf(validate.Validator):
    """Validator which succeeds if the ``value`` passed to it is a multiple of ``multiply``

    Args:
        multiply: The object to compare to
        error: Error message to raise in case of a validation error. Can be interpolated with `{multiply}`
    """

    default_message = "Must be a multiple of {multiply}."

    def __init__(self, multiply: Union[int, float], *, error: Optional[str] = None):
        if multiply <= 0: raise ValueError("'multiply' argument of MultipleOf constructor must be a positive number!")
        self.multiply = multiply
        self.error = error or self.default_message  # type: str

    def _repr_args(self) -> str:
        return f"multiply={self.multiply!r}"

    def _format_error(self, value: validate._T) -> str:
        return self.error.format(input=value, multiply=self.multiply)

    def __call__(self, value: validate._T) -> validate._T:
        if self.multiply % value != 0:
            raise validate.ValidationError(self._format_error(value))
        return value
