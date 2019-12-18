#!/usr/bin/python3.8

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import datetime


def list_systems(session):
    return [
        {
            "id": 1000010000,
            "name": "foo.acme.com",
            "last_checkin": datetime.datetime.now(),
            "last_boot": datetime.datetime.now(),
            "created": datetime.datetime.now(),
        },
        {
            "id": 1000010001,
            "name": "bar.acme.com",
            "last_checkin": datetime.datetime.now(),
            "last_boot": datetime.datetime.now(),
            "created": datetime.datetime.now(),
        },
        {
            "id": 1000010002,
            "name": "spam.acme.com",
            "last_checkin": datetime.datetime.now(),
            "last_boot": datetime.datetime.now(),
            "created": datetime.datetime.now(),
        },
    ]

def get_details(sesssion, serverid):
    servers = {
        1000010000: "foo.acme.com",
        1000010001: "bar.acme.com",
        1000010002: "spam.acme.com",
    }

    return {
        "id": serverid,
        "profile_name": servers[serverid] + " profile",
        "base_entitlement": servers[serverid] + " entitlement",
        "addon_entitlements": ["one", "two"], "auto_update": True, "release": "4AS",
        "address1": "", "address2": "", "city": "", "state": "", "country": "",
        "building": "", "room": "", "rack": "",
        "description": servers[serverid] + " machine",
        "hostname": servers[serverid],
        "last_boot": datetime.datetime.now(),
        "osa_status": 'unknown', "lock_status": False, "virtualization": "",
    }

def auth(login, password):
    return "42"

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/rpc/api',)

with SimpleXMLRPCServer(('localhost', 8000),
                        requestHandler=RequestHandler) as server:
    server.register_function(list_systems, "system.listSystems")
    server.register_function(get_details, "system.getDetails")
    server.register_function(auth, "auth.login")

    print("Starting server...")
    server.serve_forever()

