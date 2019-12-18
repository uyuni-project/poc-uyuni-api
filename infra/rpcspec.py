"""
XML-RPC spec generator.
2nd approach by parsing Java code only (not taking to the consideration @xmlrpc* tags)
"""
from typing import List, Mapping
from xml.dom import minidom
import os
import re
import argparse


class APISource:
    def __init__(self, namespace: str, path: str):
        self.namespace = namespace
        self.path = path


class APIGen:
    """
    Generator of the API specs
    """
    NAMESPACE = "com/redhat/rhn/frontend/xmlrpc"
    NS_DECLARATION = "code/src/com/redhat/rhn/frontend/xmlrpc/handler-manifest.xml"

    def __init__(self):
        self.sources: List = []
        self.nsmap = {}
        self.spec = {}
        self._re_generics = re.compile("<.*?>")
        self._re_arr = re.compile("\[.*?\]")
        self._re_func = re.compile("\(.*")
        self._re_despace = re.compile("\s+")

    def scan(self, path: str) -> None:
        """
        Scan Java sources for XML-RPC specifications
        """
        if not self.nsmap:
            nsdoc = minidom.parse("/" + path.strip("/") + "/" + self.NS_DECLARATION)
            for template_node in nsdoc.getElementsByTagName("template"):
                self.nsmap[template_node.getAttribute("classname")] = template_node.getAttribute("name")

        for fname in os.listdir(path):
            fname = os.path.join(path, fname)
            if os.path.isdir(fname):
                self.scan(fname)
            if not fname.endswith(".java"):
                continue

            if self.is_rpc_endpoint(fname):
                namespace = self.path_to_namespace(fname)
                if namespace:
                    self.sources.append(APISource(namespace=namespace, path=fname))

    def is_rpc_endpoint(self, path: str) -> bool:
        """
        Determine if the given source is XML-RPC endpoint.

        :param path: Path to the Java source file.
        :returns: True, if given source code is XML-RPC endpoint.
        """
        if self.NAMESPACE not in path:
            return False

        if "/test/" in path:
            return False

        return True

    def path_to_namespace(self, path: str) -> str:
        """
        Get a namespace.
        """
        jclass = (APIGen.NAMESPACE + path.split(APIGen.NAMESPACE)[-1].replace(".java", "")).replace("/", ".")
        return self.nsmap.get(jclass, "")

    def generate(self):
        """
        Generate YAML.
        """
        data = []
        for src in self.sources:
            # self._get_src_spec(src)  # Doc is very inaccurate :-(
            data.append(CodeSpec(src).spec)

        print("# Automatically generated specs")
        print("# XML-RPC calls:", len(data))
        print()
        print("xmlrpc:")
        for ns in data:
            for f_ns in ns:
                for namespace in f_ns:
                    print("  -", namespace)
                    for arg in f_ns[namespace]:
                        for arg_name, arg_value in arg.items():
                            print("    - {}: {}".format(arg_name, arg_value))
                    print()


class CodeSpec:
    """
    Get codespec from the Java source file.
    """
    def __init__(self, source: APISource):
        self.spec = []
        self.src = source
        self._funcs = []
        self._re_kg = re.compile("<.*?>+|\[.*?\]+")

        self.get_src_codespec()

    def generate(self):
        """
        Generate codespec.

        [
            "namespace.function": {
                [
                    {"argname": "type"},
                ]
            }
        ]
        """

    def _parse_func(self, data: str):
        """
        Parse function:
          - Name of the function
          - Arg names
          - Arg types
        """
        class Funcdata:
            namespace = self.src.namespace
            def __init__(self):
                self.method = ""
                self.args = []
                self._re_gs = re.compile("<.*?>+")

            def parse_params(self, data: str):
                """
                Parse Java code parameters.
                """
                tokens = []
                op = 0
                buff = ""
                for c in data:
                    buff += c
                    if c in ["<", "["]:
                        op += 1
                    if c in [">", "]"]:
                        op -= 1
                    if c == "," and not op:
                        tokens.append(buff.strip(",").replace(",", "::").replace("final ", ""))
                        buff = ""
                tokens.append(buff)
                for kwset in tokens:
                    kwtype, kwname = kwset.strip().rsplit(" ", 1)
                    self.add_arg(self.convert_type(kwtype), kwname)

            def convert_type(self, ptype: str):
                """
                Convert type from Java to spec
                """
                # TODO: Add generics for nested types (this is a chunk of work!)
                remap = {
                    "integer": "int",
                    "date": "datetime",
                    "boolean": "bool",
                }
                ptype = self._re_gs.sub("", ptype).lower()
                return remap.get(ptype, ptype)

            def add_arg(self, ptype, pname):
                if ptype == "user":
                    pname = "sessionKey"
                    ptype = "string"

                self.args.append({pname: ptype})

            def get(self):
                assert self.method != ""
                return {"{}.{}".format(self.namespace, self.method): self.args}

        fdata = Funcdata()
        fdata.parse_params(data.split("(")[-1].split(")")[0])

        m_data = list(filter(None, self._re_kg.sub("", data.split("(")[0]).split(" ")))
        assert len(m_data) == 3, "M_data is not length of 3" + str(m_data)
        fdata.method = m_data[-1]

        return fdata

    def get_src_codespec(self) -> List[str]:
        """
        Parse Java source code directly.
        {
            "namespace.function": {
                [
                    {"argname": "type"},
                ]
            }
        }
        """
        tag = "@xmlrpc.param"
        funcbuff = []
        p = False
        with open(self.src.path, "r") as fh:
            for src_line in fh.readlines():
                src_line = src_line.strip()

                if tag in src_line:
                    p = True
                    continue

                if src_line.startswith("public ") and p:
                    funcbuff.append(src_line)

                if funcbuff:
                    if src_line != funcbuff[-1]:
                        funcbuff.append(src_line)

                if funcbuff and ")" in src_line:
                    func = self._parse_func(" ".join(funcbuff))
                    self.spec.append(func.get())
                    funcbuff = []
                    p = False

def main():
    parser = argparse.ArgumentParser(description="XML-RPC API spec generator.")
    parser.add_argument("--source", help="Uyuni Java source code")
    args = parser.parse_args()

    if not args.source:
        parser.print_usage()
    else:
        try:
            apigen = APIGen()
            apigen.scan(args.source)
            apigen.generate()
        except Exception as err:
            print(err)
            raise


if __name__ == "__main__":
    main()
