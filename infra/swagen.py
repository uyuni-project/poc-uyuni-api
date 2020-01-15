#!/usr/bin/python3.8

import yaml
import sys
import os
import inspect
import importlib
from xml.dom import minidom
from typing import List, Dict, Any, Tuple, Callable

try:
    import salt
    import salt.modules
except ImportError:
    salt = None

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


class SaltSwagAPI:
    """
    Swagger UI generator for Salt API.
    """
    def __init__(self):
        self.swag: Dict = {}
        self._modules: Dict = {}

    def _preamble(self) -> None:
        """
        _preamble -- generate Swagger UI header.
        """
        self.swag["openapi"] = "3.0.0"
        self.swag["info"] = {
            "title": "Uyuni API",
            "description": "Welcome to the Salt API",
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
                "url": "http://localhost:8080/salt",
                "description": "Salt API, random version",
            }
        ]


    def _index_modules(self):
        """
        _index_modules -- indexes all Salt modules
        """
        m_root = os.path.dirname(salt.modules.__file__)
        for f_name in os.listdir(m_root):
            if f_name in ["__init__.py", "__pycache__"] or os.path.isdir(m_root + "/" + f_name):
                continue
            modname = "salt.modules.{}".format(f_name.split(".")[0])
            try:
                saltmod = importlib.import_module(modname)
                self._modules[modname] = saltmod
            except Exception as exc:
                sys.stderr.write("WARNING: skipping module {}: {}\n".format(modname, exc))

    def _get_module_functions(self, mod_obj) -> List[Tuple]:
        """

        _get_module_functions -- get module-level functions.

        :return: List of tuples, each tuple has two elements: name of the function and function object.
        :rtype: List[Tuple]
        """
        functions:List = []
        for obj_name, obj_val in inspect.getmembers(mod_obj):
            if obj_name.upper() == obj_name or obj_name.startswith("_") or obj_name.endswith("_"):
                continue
            if not inspect.isfunction(obj_val):
                continue

            functions.append((obj_name, obj_val,))

        return functions

    def _describe_path(self, mod_ns: str, func_ns: str, func_obj: Callable):
        sig = inspect.signature(func_obj)
        params:List = []
        for p_name, p_obj in sig.parameters.items():
            in_type: str
            if p_obj.kind == inspect.Parameter.VAR_KEYWORD:
                in_type = "body"
            elif p_name == "args":  # XXX: stupid lousy, bound to a "standard" that they don't have. This needs a better inspection.
                in_type = "body"
            else:
                in_type = "formData"

            s_param: Dict = {
                "name": p_name,
                "in": in_type,
                "type": "string",
                "description": "{} {} parameter".format(p_name, str(p_obj.kind)),
            }
            params.append(s_param)
        api_path: Dict = {
            "post": {
                "description": inspect.getdoc(func_obj),
                "parameters": params,
                "tags": [mod_ns],
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
        path = "/" + "/".join(mod_ns.split(".")[1:] + [func_ns])
        return path, api_path


    def _paths(self):
        """
        _paths -- finds out all REST API paths in all available Salt modules.
        """
        paths: Dict = {}
        for mod_ns, mod_obj in self._modules.items():
            for func_ns, func_obj in self._get_module_functions(mod_obj):
                p_urn, p_obj = self._describe_path(mod_ns, func_ns, func_obj)
                paths[p_urn] = p_obj
        self.swag["paths"] = paths

    def generate(self):
        """
        generate -- generates Swagger UI for Salt API.
        """
        self._index_modules()
        self._preamble()
        self._servers()
        self._paths()

    def render(self) -> str:
        """
        render -- Renders Swagger UI

        :return: Swagger YAML definition
        :rtype: str
        """
        return yaml.dump(self.swag, default_flow_style=False, default_style="")


def main():
    parser = argparse.ArgumentParser(description="Swagger API generator for Uyuni.")
    parser.add_argument("-a", "--apidoc", help="Uyuni Java API docbook", required=False)
    parser.add_argument("-s", "--apisalt", help="Use Salt API modules", required=False, action="store_true")
    parser.add_argument("-p", "--spec", help="XML-RPC API spec", required=False)
    args = parser.parse_args()

    if not args.apidoc and not args.apisalt:
        parser.print_usage()
        print("error: either API docbook or Salt API should be in use")
    elif args.apidoc and args.apisalt:
        parser.print_usage()
        print("error: can process only API docbook or Salt API at a time")
    else:
        if args.apidoc and not args.spec:
            parser.print_usage()
            print("error: XML-RPC spec needs to be specified")
        else:
            try:
                if args.spec and args.apidoc:
                    swag = SwagAPI()
                    swag.load_rpc_spec(args.spec)
                    swag.load_apidoc(args.apidoc)
                    swag.generate()
                else:
                    swag = SaltSwagAPI()
                    swag.generate()
                print(swag.render())
            except Exception as err:
                print(err)
                raise

if __name__ == "__main__":
    main()
