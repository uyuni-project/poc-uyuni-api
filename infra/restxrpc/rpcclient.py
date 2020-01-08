"""
Drop-in replacement RPC Client for REST over XML-RPC.

Usage is to just change a usual import like this:

    from xmlrpc.client import ServerProxy

To this:

    from restxrpc.rpcclient import ServerProxy


Additionally, set the URL for XML-RPC specs download, e.g.:

    ServerProxy.set_specs_url("http://myhost:8080/xmlrpcspecs")


Author: bo@suse.de
"""
from typing import Optional, Dict
import datetime
import requests
import yaml


class RESTCall:
    """
    REST call object.
    """
    _TYPEMAP = {
        "string": str,
        "int": int,
        "bool": bool,
        "datetime": datetime.datetime  # ??
    }

    def __init__(self, url: str, obj: str):
        """
        __init__ constructor

        :param url: URL
        :type url: str
        """
        self._root = url.strip("/")
        self._path = [obj]
        self._xmlrpc_spec = None

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
        self._xmlrpc_spec = requests.get("{}/{}".format(self.__root, uri.strip("/")))
        self.lock()

        return self

    def _is_root(self) -> bool:
        """
        is_root tells if the node is Root node.

        :return: True if node is root.
        :rtype: bool
        """
        return self._root is None

    def __getattr__(self, attr):
        if attr not in self.__dict__: # or self.__dict__[attr] is None:
            self._path.append(attr)
        return self

    def _get_uri(self) -> str:
        """
        _get_uri get URI path.

        :return: URI
        :rtype: str
        """
        return "/".join(self._path).strip("/")

    def _get_namespace(self) -> str:
        """
        _get_namespace get namespace path of the current function

        :return: XML-RPC namespace.
        :rtype: str
        """
        return ".".join(self._path).strip(".")

    def _get_func_spec(self) -> str:
        """
        _get_func_spec get path as an XMl-RPC namespace and resolves function spec

        :return: namespace path
        :rtype: str
        """
        spec = None
        ns = self._get_namespace()
        for spec_ns in self._xmlrpc_spec:
            if ns in spec_ns:
                spec = spec_ns[ns]
                break
        return spec

    def _map_parameters(self, *args) -> Dict:
        """
        _map_parameters maps parameters of the XML-RPC to the REST according to the spec.

        :return: Data mapping
        :rtype: Dict
        """
        spec = self._get_func_spec()
        assert len(spec) == len(args), "Invalid parameters for the function {}: given: {}, expected: {}".format(
            self._get_namespace(), args, ", ".join(['"{}" ({})'.format(list(item.keys())[0],
                                                                       list(item.values())[0]) for item in spec]))
        kwargs = {}
        for arg_ntp, arg_val in zip(spec, args):
            arg_name, arg_type = tuple(arg_ntp.items())[0]
            e_arg_type = self._TYPEMAP.get(arg_type, str)
            assert isinstance(arg_val, e_arg_type), "Argument {} has wrong type. Expected {}, got {}.".format(
                arg_val, e_arg_type.__name__, type(arg_val).__name__
            )
            kwargs[arg_name] = arg_val

        return kwargs

    def __call__(self, *args, **kwargs):
        """
        __call__ performs an actual REST call via requests
        """
        return requests.post("{}/{}".format(self._root, self._get_uri()),
                             data=self._map_parameters(*args)).json()


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
