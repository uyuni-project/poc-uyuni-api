package main

import (
	"github.com/isbm/uyuni-api"
	"github.com/urfave/cli/v2"
	"log"
	"os"
)

func contextRun(ctx *cli.Context) error {
	hdl := uyuniapi.NewUyuniXMLRPCHandler()
	hdl.SetMethodMap(ctx.String("rpcspec"))

	cfg := uyuniapi.NewAPIConfig(ctx.String("config"))

	rpc := uyuniapi.NewRPCServer()
	rpc.AddHandler(hdl)
	rpc.Setup(cfg).Start()

	return nil
}

func main() {
	app := &cli.App{
		Version: "0.1 Alpha",
		Name:    "mgr-api",
		Usage:   "Uyuni API Microgateway",
		Action:  contextRun,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:    "rpcspec",
				Aliases: []string{"s"},
				Value:   "/etc/rhn/mgr-api.spec.conf",
				Usage:   "XML-RPC method specifications for Uyuni",
			},
			&cli.StringFlag{
				Name:    "config",
				Aliases: []string{"c"},
				Value:   "/etc/rhn/mgr-api.conf",
				Usage:   "full configuration of the gateway",
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
