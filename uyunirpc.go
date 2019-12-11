package uyuniapi

import (
	"crypto/tls"
	"fmt"
	"github.com/kolo/xmlrpc"
	"net/http"
	"net/url"
	"strconv"
)

type RPCClient struct {
	conn         *xmlrpc.Client
	user         string
	password     string
	port         int
	host         string
	uri          string
	skipSslCheck bool
	tls          bool
	sid          string
}

// NewRPCClient is a constructor for the RPCClient object
func NewRPCClient(skipSslCheck bool) *RPCClient {
	rpc := new(RPCClient)
	rpc.skipSslCheck = skipSslCheck
	return rpc
}

func (rpc *RPCClient) Connect() *RPCClient {
	if rpc.conn == nil {
		transport := &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: rpc.skipSslCheck,
			},
		}

		rpc.conn, _ = xmlrpc.NewClient(rpc.getURL(), transport)
	}
	return rpc
}

// Construct connection URL
func (rpc *RPCClient) getURL() string {
	u, _ := url.Parse("http://localhost/rpc/api")
	if rpc.tls {
		u.Scheme = "https"
	} else {
		u.Scheme = "http"
	}

	u.Host = rpc.host
	if rpc.port > 0 {
		u.Host += ":" + strconv.Itoa(rpc.port)
	}

	return fmt.Sprint(u)
}

// SetUser sets the username for the authentication
func (rpc *RPCClient) SetUser(user string) *RPCClient {
	rpc.user = user
	return rpc
}

// SetPassword sets the password for the authentication
func (rpc *RPCClient) SetPassword(password string) *RPCClient {
	rpc.password = password
	return rpc
}

// SetPort sets the port for the URL
func (rpc *RPCClient) SetPort(port int) *RPCClient {
	rpc.port = port
	return rpc
}

// SetHost sets the host for the URL
func (rpc *RPCClient) SetHost(host string) *RPCClient {
	rpc.host = host
	return rpc
}

// SetURI sets the URI for the URL
func (rpc *RPCClient) SetURI(uri string) *RPCClient {
	rpc.uri = uri
	return rpc
}

// SetTLS sets the SSL/TLS use and checking its certificate
func (rpc *RPCClient) SetTLS(tls bool, check bool) *RPCClient {
	rpc.tls = tls
	rpc.skipSslCheck = check
	return rpc
}

// Obtain authentication token
func (rpc *RPCClient) authenticate() {
	var err error
	var res interface{}
	if rpc.user != "" && rpc.password != "" {
		res, err = rpc.Call("auth.login", rpc.user, rpc.password)
		if err != nil {
			panic(err)
		} else {
			rpc.sid = res.(string)
		}
	} else {
		panic("No credentials found")
	}
}

// Get current session ID or create new one
func (rpc *RPCClient) getSID() string {
	if rpc.sid == "" {
		rpc.authenticate()
	}

	return rpc.sid
}

// Refresh session ID
func (rpc *RPCClient) refreshSID() string {
	rpc.sid = ""
	return rpc.getSID()
}

// Call XML-RPC on Uyuni side
func (rpc *RPCClient) Call(method string, args ...interface{}) (interface{}, error) {
	var ret interface{}
	err := rpc.conn.Call(method, args, &ret)

	return ret, err
}

/////////////
// Token marker
type RPCSessionToken struct{}

///////////////////////
// XML-RPC mux/demux
type RPCDemux struct {
	clients    map[string]*RPCClient
	vidmanager *VIDManager
}

func NewRPCDemux(vm *VIDManager) *RPCDemux {
	rpmc := new(RPCDemux)
	rpmc.clients = make(map[string]*RPCClient)
	rpmc.vidmanager = vm
	for _, fqdn := range rpmc.vidmanager.GetContextFQDNs() {
		fmt.Println("Registering connection to", fqdn)
		rpmc.clients[fqdn] = NewRPCClient(true).
			SetHost(fqdn).
			SetUser("admin").
			SetPassword("admin").
			SetPort(8000).
			SetTLS(false, false).
			Connect()
	}

	return rpmc
}

// Marker for a token. This is just a dummy type that is used to be a placeholder
// for the real token within the demuxer call.
func (rpmc *RPCDemux) GetSIDMarker() *RPCSessionToken {
	return new(RPCSessionToken)
}

// Call multiple systems at once, aggregate
func (rpmc *RPCDemux) Call(method string, args ...interface{}) (interface{}, error) {
	demux := NewDataAggregator(rpmc.vidmanager)
	for fqdn := range rpmc.clients {
		c_ref := rpmc.clients[fqdn]

		// Inject session ID
		_args := make([]interface{}, 0)
		for _, arg := range args {
			switch arg.(type) {
			case *RPCSessionToken:
				_args = append(_args, c_ref.getSID())
			case int: // This is just a proof of concept for now. Need to find out ID reliably.
				id, ctx := rpmc.vidmanager.ToSystemId(arg.(int))
				if ctx != fqdn {
					_args = nil
					break
				}
				_args = append(_args, id)
			default:
				_args = append(_args, arg)
			}
		}

		if _args == nil {
			continue
		}

		ret, err := c_ref.Call(method, _args...)

		if err != nil {
			panic(err)
		}

		demux.aggregate(fqdn, ret)
	}

	return demux.Multiplex(), nil
}
