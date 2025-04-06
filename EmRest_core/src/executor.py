import sys
from logging import getLogger
from typing import Tuple, Union, Optional

import requests
from requests.exceptions import ConnectionError

from src.rest import Method, ContentType

_logger = getLogger(__name__)


class Auth:
    def __init__(self, header_auth: Optional[dict] = None,
                 query_auth: Optional[dict] = None):
        self.header_auth = header_auth
        self.query_auth = query_auth

    def __call__(self, r):
        if self.header_auth is not None:
            for k, v in self.header_auth.items():
                r.headers[k] = v
        if self.query_auth is not None:
            for k, v in self.query_auth.items():
                r.params[k] = v
        return r


class RestRequest:
    UNEXPECTED = 700

    def __init__(self, auth: Auth = None):
        self.auth: Auth = auth

    @staticmethod
    def validate(verb: Method, url: str, headers: dict, **kwargs):
        """
        verify requests
        """
        if url is None or url == "":
            raise ValueError("Url cannot be null")
        if verb in [Method.POST, Method.PUT] and "body" not in kwargs:
            raise ValueError(f"{verb}: body cannot be null")
        if "body" in kwargs and "files" in kwargs:
            raise ValueError("body and files cannot be set at the same time")

    def send(self, verb: Method, url: str, headers: dict, **kwargs) -> Tuple[int, Union[str, dict]]:
        self.validate(verb, url, headers, **kwargs)

        def send_request():
            if verb in [Method.POST, Method.PUT] and kwargs.get("body", None) is not None:
                status_code, response_content = self.send_request_with_content(verb, url, headers, self.auth, **kwargs)
            elif verb is Method.PATCH:
                status_code, response_content = self.send_request_with_content(verb, url, headers, self.auth, **kwargs)
            else:
                status_code, response_content = self.send_request(verb, url, headers, self.auth, **kwargs)
            return status_code, response_content

        try:
            sc, resp = send_request()
        except ConnectionError as e:
            _logger.error(f"ConnectionError: {e}")
            sys.exit(1)
        except Exception as e:
            _logger.error(f"{verb.value}:{url} {type(e)} {e}")
            try:
                sc, resp = send_request()
            except Exception as e:
                _logger.error(f"Try again: {verb.value}:{url} {e}")
                sc, resp = self.UNEXPECTED, {}

        _logger.debug(f"{verb.value}:{url} {sc}, {resp}, Request Data: {kwargs}")
        return sc, resp

    @staticmethod
    def send_request_with_content(method: Method, url: str, headers: dict, auth: Optional[Auth], **kwargs) \
            -> Tuple[int, Union[str, dict]]:
        content_type = kwargs.get("ContentType", ContentType.JSON)
        # Set Content-Type
        headers["Content-Type"] = content_type.value

        if "json" in content_type.value.lower():
            response = requests.request(method=method.value, url=url, headers=headers, params=kwargs.get("query", None),
                                        json=kwargs.get("body", None), files=kwargs.get("files", None), timeout=10,
                                        auth=auth)
        else:
            response = requests.request(method=method.value, url=url, headers=headers, params=kwargs.get("query", None),
                                        data=kwargs.get("body", None), files=kwargs.get("files", None), timeout=10,
                                        auth=auth)

        return RestRequest.get_response_info(response)

    @staticmethod
    def send_request(verb: Method, url, headers, auth, **kwargs) -> Tuple[int, Union[str, dict]]:
        feedback = requests.request(method=verb.value, url=url, headers=headers, params=kwargs.get("query", None),
                                    timeout=10, auth=auth)
        return RestRequest.get_response_info(feedback)

    @staticmethod
    def get_response_info(feedback: requests.Response) -> Tuple[int, Union[str, dict]]:
        status_code = feedback.status_code
        try:
            response = feedback.json()
        except requests.exceptions.JSONDecodeError:
            # logger.error("Response is not a JSON object: " + feedback.text)
            response = feedback.text
        return status_code, response
