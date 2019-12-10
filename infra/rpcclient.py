#!/usr/bin/python3

import xmlrpc.client

conn = xmlrpc.client.ServerProxy("http://localhost:8000/rpc/api")
print(conn.systems.listSystems("token"))
print(conn.systems.getDetails("token", 1000010000))
