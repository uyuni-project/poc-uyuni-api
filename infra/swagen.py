#!/usr/bin/python3.8

import yaml
from xml.dom import minidom
from typing import List, Dict, Any, Tuple

import argparse

class MethodType:
    def __init__(self, src: Dict):
        self.namespace:str = ""
        self.params:Dict = {}
        self._to_type(src)

    def _to_type(self, src: Dict):
        """
        _to_type -- convert to the type of this instance.

        :param src: source of the method map
        :type src: Dict
        """
        keys = list(src.keys())
        assert len(keys) == 1, "Wrong namespace object: {}".format(src)
        self.namespace = keys[0]
        self.params = src[self.namespace]

    def get_urn(self) -> str:
        """
        get_urn -- get URN of the API call

        :return: URN
        :rtype: str
        """
        return "/" + "/".join(self.namespace.split("."))


class SwagAPI:
    def __init__(self):
        """
        __init__ -- constructor
        """
        self.swag: Dict = {}
        self._apidoc = None
        self._spec = {}

    def load_rpc_spec(self, path: str) -> None:
        """
        load_rpc_spec -- load XML-RPC API spec

        :param path: path to the generated XML-RPC API spec
        :type path: str
        """
        with open(path) as rpcspec:
            self._spec = yaml.load(rpcspec)["xmlrpc"]

    def load_apidoc(self, path: str) -> None:
        """
        load_apidoc -- load APIDoc XML file

        :param path: path to the generated APIDoc XML output
        :type path: str
        """
        self._apidoc = minidom.parse(file=open(path))

    def _preamble(self) -> None:
        """
        _preamble -- generate Swagger UI header.
        """
        self.swag["openapi"] = "3.0.0"
        self.swag["info"] = {
            "title": "Uyuni API",
            "description": "Welcome to the Uyuni API. By using the included API calls,"
                "you can more easily automate many of the tasks you perform everyday. All API calls are grouped by common functionality.",
                "version": "0.1.9"
        }

    def _servers(self) -> None:
        """
        _servers -- generate list of servers to serve stubs.
        This, however, should be a placeholder for the template.
        API Gateway should place here server name dynamically.
        """
        self.swag["servers"] = [
            {
                "url": "http://localhost:8080/uyuni",
                "description": "Uyuni API, version 4",
            }
        ]

    def _paths(self) -> None:
        """
        _paths -- generate API calls, grouped by tags. Method GET.
        """
        self.swag["paths"] = {}
        for src in self._spec:
            path, p_descr = self._describe_path(src)
            self.swag["paths"][path] = p_descr

    def _describe_path(self, src: Dict) -> Tuple[str, Dict]:
        mod = MethodType(src)

        params = []
        for p in mod.params:
            p_name, p_type = list(p.items())[0]
            param = {
                "name": p_name,
                "in": "query",
                "type": p_type,
                "description": "{} of type {}".format(p_name, p_type)
            }
            params.append(param)

        api_path: Dict = {
            "get": {
                "parameters": params,
                "responses": {
                    '200': {
                        "description": "",
                        "content": {
                            "application/json": {
                                "schema": {}
                            }
                        }
                    },
                }
            }
        }
        return mod.get_urn(), api_path

    def _path_GET(self, src) -> None:
        """
        _path_GET -- generate GET path.
        """
        print(src.namespace)

    def generate(self) -> None:
        """
        generate -- generate Swagger UI YAML specifications
        """
        self.swag.clear()
        self._preamble()
        self._servers()
        self._paths()

    def render(self) -> Any:
        """
        render -- render Swagger API

        :return: string
        :rtype: str
        """
        return yaml.dump(self.swag, default_flow_style=False, default_style="")


def main():
    parser = argparse.ArgumentParser(description="Swagger API generator for Uyuni.")
    parser.add_argument("-a", "--apidoc", help="Uyuni Java API docume", required=True)
    parser.add_argument("-p", "--spec", help="XML-RPC API spec map", required=True)
    args = parser.parse_args()

    try:
        swag = SwagAPI()
        swag.load_rpc_spec(args.spec)
        swag.load_apidoc(args.apidoc)
        swag.generate()
        print(swag.render())
    except Exception as err:
        print(err)
        raise

if __name__ == "__main__":
    main()
