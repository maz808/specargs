from http import HTTPStatus
from typing import Any, Union

from attrs import define, field


@define
class ViewResponse:
    '''An object used for specifying the data and status code returned by a view function/method
    
    This class should be used when returning a non-default status code from a view function/method.
    '''
    data: Any
    status_code: HTTPStatus = field(converter=HTTPStatus, default=HTTPStatus.OK)

    def __init__(self, data: Any, status_code: Union[HTTPStatus, int]):
        '''Initializes a :class:`~specargs.Response` object
        
        Args:
            data: The data to be returned in the response. May be serialized depending on whether/how the returning
                view function/method has been decorated with :func:`~specargs.use_response`
            status_code: The status code of the response
        '''
        self.__attrs_init__(data, status_code)
