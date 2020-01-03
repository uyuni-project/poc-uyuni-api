package uyuniapi

import (
	"github.com/go-yaml/yaml"
	"io/ioutil"
	"os"
)

type configLayout struct {
	Context struct {
		Http_address string
		Uyuni        struct {
			Default map[string]interface{}
			Hosts   map[string]map[string]interface{}
		}
	}
}

type APIConfig struct {
	config       configLayout
	DEFAULT_ADDR string
}

func NewAPIConfig(path string) *APIConfig {
	cfg := new(APIConfig)
	cfg.DEFAULT_ADDR = ":8080"
	cfg.config = configLayout{}
	cfg.readConfig(path)

	return cfg
}

func (cfg *APIConfig) readConfig(path string) {
	fh, err := os.Open(path)
	if err != nil {
		panic("Error open configuration:" + err.Error())
	}
	defer fh.Close()
	mapBytes, err := ioutil.ReadAll(fh)
	if err != nil {
		panic("Error reading configuration:" + err.Error())
	}

	if err := yaml.Unmarshal(mapBytes, &cfg.config); err != nil {
		panic("Error parsing configuration:" + err.Error())
	}
}

// TODO: Get default hosts by area. Currently only one area is there: Uyuni
func (cfg *APIConfig) GetHosts(area string) map[string]map[string]interface{} {
	return cfg.config.Context.Uyuni.Hosts
}

// TODO: Get default setup by area. Currently only one area is there: Uyuni
func (cfg *APIConfig) GetDefaultSetup(area string) map[string]interface{} {
	return cfg.config.Context.Uyuni.Default
}

// Get reference server configuration
func (cfg *APIConfig) GetRefServerConfig(fqdn string) map[string]interface{} {
	serverConf := cfg.config.Context.Uyuni.Default
	if localConfig, exists := cfg.config.Context.Uyuni.Hosts[fqdn]; exists {
		for k, v := range localConfig {
			serverConf[k] = v
		}
	} else {
		panic("No host is configured as " + fqdn) // This actually should not happen, as fqdn should come from the Hosts variable anyway
	}

	return serverConf
}

// Get HTTP server address to run on
func (cfg *APIConfig) GetHTTPAddress() string {
	if cfg.config.Context.Http_address == "" {
		return cfg.DEFAULT_ADDR
	} else {
		return cfg.config.Context.Http_address
	}
}
