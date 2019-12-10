package main

import (
	"fmt"
	"github.com/isbm/uyuni-api"
)

func main() {
	vm := uyuniapi.NewVIDManager()
	vm.AddContext("localhost")

	mux := uyuniapi.NewRPCDemux(vm)
	data, _ := mux.Call("systems.listSystems", mux.GetSIDMarker())

	fmt.Println(data)
}
