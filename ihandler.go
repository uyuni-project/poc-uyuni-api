package uyuniapi

import (
	"github.com/gin-gonic/gin"
)

type UyuniRPCHandler interface {
	Handler(context *gin.Context)
	Bind(server *RPCServer)
	GetHandlerUri() string
	GetHTTPMethods() []string
}
