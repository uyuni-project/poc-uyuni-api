package uyuniapi

import (
	"github.com/gin-gonic/gin"
	"github.com/go-yaml/yaml"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
)

/*
Uyuni XML-RPC Specifications handler.
Used by XML-RPC to REST translator library on the client side.
*/

type UyuniXMLRPCSpecHandler struct {
	baseURI    string
	handlerURI string
	rpc        *RPCServer
	methodmap  map[string][]map[string][]map[string]string
}

func NewUyuniXMLRPCSpecHandler(methodmap map[string][]map[string][]map[string]string) *UyuniXMLRPCSpecHandler {
	h := new(UyuniXMLRPCSpecHandler)
	h.methodmap = methodmap
	h.baseURI = "/uyuni-spec"
	h.handlerURI = h.baseURI + "/*spec"
	return h
}

// Return supported methods for the proxy handler
func (h *UyuniXMLRPCSpecHandler) GetHTTPMethods() []string {
	return []string{"GET"}
}

func (h *UyuniXMLRPCSpecHandler) Bind(server *RPCServer) {
	h.rpc = server
}

func (h *UyuniXMLRPCSpecHandler) GetHandlerUri() string {
	return h.handlerURI
}

func (h *UyuniXMLRPCSpecHandler) getRPCSpec() map[string][]map[string][]map[string]string {
	return h.methodmap
}

func (h *UyuniXMLRPCSpecHandler) Handler(context *gin.Context) {
	method := strings.ReplaceAll(strings.TrimLeft(context.Param("spec"), "/"), "/", ".")
	switch method {
	case "xmlrpc":
		context.YAML(200, h.getRPCSpec())
	default:
		context.YAML(http.StatusBadRequest, gin.H{"error": "Method does not exists"})
	}
}

/*
Uyuni XML-RPC Handler for handling
all the XML-RPC methods to the REST protocol.
*/

type UyuniXMLRPCHandler struct {
	baseURI    string
	handlerURI string
	methodMap  map[string][]map[string][]map[string]string
	rpc        *RPCServer
}

func NewUyuniXMLRPCHandler() *UyuniXMLRPCHandler {
	h := new(UyuniXMLRPCHandler)
	h.baseURI = "/uyuni"
	h.handlerURI = h.baseURI + "/*method"

	return h
}

// Return supported methods for the proxy handler
func (h *UyuniXMLRPCHandler) GetHTTPMethods() []string {
	return []string{"GET", "POST"}
}

func (h *UyuniXMLRPCHandler) Bind(server *RPCServer) {
	h.rpc = server
}

func (h *UyuniXMLRPCHandler) GetHandlerUri() string {
	return h.handlerURI
}

func (h *UyuniXMLRPCHandler) GetMethodSpec() map[string][]map[string][]map[string]string {
	return h.methodMap
}

// Get methods map
func (h *UyuniXMLRPCHandler) getMethodMap(method string) []map[string]string {
	xmlrpcTree, exists := h.methodMap["xmlrpc"]
	if !exists {
		panic("XML-RPC spec is missing")
	}

	for _, xmap := range xmlrpcTree {
		for mName, mArgs := range xmap {
			if mName == method {
				return mArgs
			}
		}
	}
	return nil
}

// SetMethodMap loads YAML spec of all XML-RPC API of Uyuni server
// to support keyword arguments alongside positional parameters
func (h *UyuniXMLRPCHandler) SetMethodMap(path string) {
	fh, err := os.Open(path)
	if err != nil {
		panic("Error open XML-RPC map:" + err.Error())
	}
	defer fh.Close()
	mapBytes, err := ioutil.ReadAll(fh)
	if err != nil {
		panic("Error reading XML-RPC map:" + err.Error())
	}

	if err := yaml.Unmarshal(mapBytes, &h.methodMap); err != nil {
		panic("Error parsing XML-RPC map:" + err.Error())
	}
}

// Realign arguments for XML-RPC endpoint
func (h *UyuniXMLRPCHandler) queryToArgs(method string, args url.Values) []interface{} {
	paramOrder := h.getMethodMap(method)

	params := make([]interface{}, 0)
	for _, argname := range paramOrder {
		for pName := range argname {
			if pName == "sessionKey" { // XXX: This relies on spec, needs config or optionals (e.g. pName in array of those names)
				params = append(params, h.rpc.mux.GetSIDMarker())
			} else {
				params = append(params, h.cast(argname[pName], args.Get(pName)))
			}
		}
	}

	if len(params) != len(args) {
		panic("Method " + method + " has missing or too much parameters.")
	}

	return params
}

// Cast GET/POST types
func (h *UyuniXMLRPCHandler) cast(ptype string, value string) interface{} {
	var param interface{}
	switch ptype {
	case "int":
		v, err := strconv.Atoi(value)
		if err != nil {
			param = value
		} else {
			param = v
		}
	case "datetime":
		param = value // todo
	default:
		param = value
	}

	return param
}

// Handle XML-RPC methods via REST
func (h *UyuniXMLRPCHandler) Handler(context *gin.Context) {
	method := strings.ReplaceAll(strings.TrimLeft(context.Param("method"), "/"), "/", ".")
	var params []interface{}
	switch context.Request.Method {
	case http.MethodGet:
		params = h.queryToArgs(method, context.Request.URL.Query())
	case http.MethodPost:
		err := context.Request.ParseForm()
		if err != nil {
			panic("Unable to parse data from the form")
		}
		params = h.queryToArgs(method, context.Request.PostForm)
	default:
		panic("Method " + context.Request.Method + " is not supported")
	}

	out, err := h.rpc.mux.Call(method, params...)

	if err != nil {
		panic(err)
	}

	context.JSON(200, out)
}
