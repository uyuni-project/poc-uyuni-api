"""
RPC Client for REST over XML-RPC.
Author: bo@suse.de
"""
from typing import Optional
import requests


class RESTCall:
    """
    REST call object.
    """
    def __init__(self, url: str, obj: str):
        """
        __init__ constructor

        :param url: URL
        :type url: str
        """
        self.__root = url.strip("/")
        self.__path = [obj]
        self.__xmlrpc_spec = None

    def lock(self) -> None:
        """
        lock is a function that locks all the methods of RESTCall instance.
        """
        for method in RESTCall.__dict__.keys():
            if not method.startswith("_"):
                setattr(self, method, None)

    def set_spec_uri(self, uri: str) -> "RESTCall":
        """
        set_spec sets the XML-RPC spec URI to download it.

        :param uri: URI on the same server to the XML-RPC spec
        :type uri: str
        :return: RESTCall object
        :rtype: RESTCall
        """
        self.__xmlrpc_spec = requests.get("{}/{}".format(self.__root, uri.strip("/")))
        self.lock()

        return self

    def _is_root(self) -> bool:
        """
        is_root tells if the node is Root node.

        :return: True if node is root.
        :rtype: bool
        """
        return self.__root is None

    def __getattr__(self, attr):
        if attr not in self.__dict__ or self.__dict__[attr] is None:
            self.__path.append(attr)

        return self

    def __get_uri(self) -> str:
        """
        __get_uri get URI path.

        :return: URI
        :rtype: str
        """
        return "/".join(self.__path).strip("/")

    def __call__(self, *args, **kwargs):
        """
        __call__ performs an actual REST call via requests
        """
        print("args:", args)
        print("kwargs:", kwargs)
        url = "{}/{}".format(self.__root, self.__get_uri())
        print("URL:", url)


class ServerProxy:
    """
    REST client over XML-RPC.
    """
    SPEC_URI = "/xmlrpc/spec"

    def __init__(self, url: str):
        """
        __init__ of ServerProxy class.

        :param url: URL of the RPC endpoint.
        :type url: str
        """
        self._url = url

    def __getattr__(self, attr):
        return RESTCall(self._url, attr).set_spec_uri(self.SPEC_URI)
