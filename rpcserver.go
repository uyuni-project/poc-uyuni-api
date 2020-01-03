package uyuniapi

import (
	"github.com/gin-gonic/gin"
)

type RPCServer struct {
	vdm    *VIDManager
	mux    *RPCDemux
	router *gin.Engine
	setup  bool
	cfg    *APIConfig
}

// Constructor
func NewRPCServer() *RPCServer {
	srv := new(RPCServer)
	srv.vdm = NewVIDManager()
	srv.mux = NewRPCDemux(srv.vdm)
	gin.SetMode(gin.DebugMode)
	srv.router = gin.New()
	srv.setup = false

	return srv
}

func (srv *RPCServer) AddHandler(handler UyuniRPCHandler) {
	handler.Bind(srv)
	for _, httpMethod := range handler.GetHTTPMethods() {
		var reg func(string, ...gin.HandlerFunc) gin.IRoutes
		switch httpMethod {
		case "POST":
			reg = srv.router.POST
		case "GET":
			reg = srv.router.GET
		default:
			reg = srv.router.Any
		}
		reg(handler.GetHandlerUri(), handler.Handler)
	}
}

// Setup is to update configuration of the server
func (srv *RPCServer) Setup(config *APIConfig) *RPCServer {
	if !srv.setup {
		srv.cfg = config

		// Add context sources
		for fqdn := range srv.cfg.GetHosts("uyuni") {
			srv.vdm.AddContext(fqdn)
		}

		srv.mux.SetConfig(srv.cfg).ReloadVIDManager()

		// Basic router middleware setup
		srv.router.Use(gin.Logger())
		srv.router.Use(gin.Recovery())
		srv.setup = true
	}

	return srv
}

func (srv *RPCServer) Start() {
	if !srv.setup {
		panic("Setup first!")
	}

	err := srv.router.Run(":8080")
	if err != nil {
		panic(err)
	}
}
