__version__ = '0.1.0'

import typing

from webargs import validate

# def use_params(params: dict, *, location: str, **kwargs):
#     '''Endpoint function decorator to be used in place of webargs' `use_kwargs`

#     The dictionary accepted by the decorator, `params`, can take pairs in the same form as
#     the dictionary accepted by webargs' `use_kwargs` (e.g. `'exampleArg': fields.Str()`). However,
#     `params` can also accept pairs in the form `params.<param_func>: {**kwargs}` where "param_func"
#     is one of the parameter functions within the `web.params` module and "**kwargs" includes any
#     keywords accepted by the webargs `Field` returned by "param_func"

#     Args:
#         params: A dictionary with (parameter function: kwarg dictionary) or
#             (parameter name: webargs Field) pairs
#         location: A string indicating where the parameters are located in the request
#         **kwargs: Any keyword arguments that are accepted by webargs' `use_kwargs`
#     '''

#     def param_to_name(param):
#         return param.__name__ if callable(param) else param

#     def kwargs_to_field(param, kwargs):
#         return param(**kwargs) if callable(param) else kwargs

#     params = {param_to_name(p): kwargs_to_field(p, k) for p, k in params.items()}
#     return use_kwargs(params, location=location, **kwargs)


def use_args(*args, **kwargs):
    from webargs.flaskparser import use_args

    def decorator(func):
        func.args_ = args
        func.kwargs_ = kwargs
        inner_decorator = use_args(*args, **kwargs)
        return inner_decorator(func)

    return decorator


def use_kwargs(*args, **kwargs):
    from webargs.flaskparser import use_kwargs, parser

    def decorator(func):
        func.args_ = args
        func.kwargs_ = {**kwargs, "location": kwargs.get("location") or parser.DEFAULT_LOCATION}
        inner_decorator = use_kwargs(*args, **kwargs)
        return inner_decorator(func)

    return decorator


class MultipleOf(validate.Validator):
    """Validator which succeeds if the ``value`` passed to it is
    a multiple of ``multiply``.

    :param multiply: The object to compare to.
    :param error: Error message to raise in case of a validation error.
        Can be interpolated with `{multiply}`.
    """

    default_message = "Must be a multiple of {multiply}."

    def __init__(self, multiply, *, error: typing.Optional[str] = None):
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
