package uyuniapi

import "github.com/gin-gonic/gin"

type RPCServer struct {
	vdm    *VIDManager
	mux    *RPCDemux
	router *gin.Engine
	setup  bool
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

//func (srv *RPCServer) AddHandler(uri string, handler gin.HandlerFunc) {
//	srv.router.Any(uri, handler)
//}

func (srv *RPCServer) AddHandler(handler UyuniRPCHandler) {
	handler.Bind(srv)
	srv.router.Any(handler.GetHandlerUri(), handler.Handler)
}

// Setup is to update configuration of the server
func (srv *RPCServer) Setup(config interface{}) *RPCServer {
	if !srv.setup {
		// Add sources
		srv.vdm.AddContext("localhost")

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
