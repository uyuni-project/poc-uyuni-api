package main

import (
	"github.com/isbm/uyuni-api"
)

func main() {
	hdl := uyuniapi.NewUyuniXMLRPCHandler()
	hdl.SetMethodMap("mgr-api.spec.conf")

	cfg := uyuniapi.NewAPIConfig("mgr-api.conf")

	rpc := uyuniapi.NewRPCServer()
	rpc.AddHandler(hdl)
	rpc.Setup(cfg).Start()
}
