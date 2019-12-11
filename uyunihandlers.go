package uyuniapi

import (
	"fmt"
	"github.com/davecgh/go-spew/spew"
	"github.com/gin-gonic/gin"
	"github.com/go-yaml/yaml"
	"io/ioutil"
	"net/url"
	"os"
	"strings"
)

type UyuniRPCHandler interface {
	Handler(context *gin.Context)
	Bind(server *RPCServer)
	GetHandlerUri() string
}

type UyuniXMLRPCHandler struct {
	baseURI    string
	handlerURI string
	methodMap  map[string]map[string][]string
	rpc        *RPCServer
}

func NewUyuniXMLRPCHandler() *UyuniXMLRPCHandler {
	h := new(UyuniXMLRPCHandler)
	h.baseURI = "/uyuni"
	h.handlerURI = h.baseURI + "/*method"

	return h
}

func (h *UyuniXMLRPCHandler) Bind(server *RPCServer) {
	h.rpc = server
}

func (h *UyuniXMLRPCHandler) GetHandlerUri() string {
	return h.handlerURI
}

// Get methods map
func (h *UyuniXMLRPCHandler) getMethodMap() map[string][]string {
	return h.methodMap["xmlrpc"]
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
	spew.Dump(h.methodMap)
}

// Realign arguments for XML-RPC endpoint
func (h *UyuniXMLRPCHandler) queryToArgs(method string, args url.Values) []interface{} {
	paramOrder, exists := h.getMethodMap()[method]
	if !exists {
		panic("Method " + method + " is not declared in argmap.")
	}
	params := make([]interface{}, 0)

	for _, argname := range paramOrder {
		param, exists := args[argname]
		if !exists {
			panic("Method " + method + " has no parameter " + argname)
		}
		params = append(params, param)
	}

	if len(params) != len(args) {
		panic("Method " + method + " has missing or too much parameters.")
	}

	return params
}

// Handle XML-RPC methods via REST
func (h *UyuniXMLRPCHandler) Handler(context *gin.Context) {
	method := strings.ReplaceAll(strings.TrimLeft(context.Param("method"), "/"), "/", ".")
	args := context.Request.URL.Query()

	fmt.Println("\n\n\nMethod:", method)
	fmt.Println("Arguments:")
	spew.Dump(args)

	fmt.Println("Parameters:")
	spew.Dump(h.queryToArgs(method, args))

	context.JSON(200, gin.H{"foo": "bar"})
}
