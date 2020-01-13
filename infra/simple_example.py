#!/usr/bin/python3.8

from restxrpc import rpcclient as client

c = client.ServerProxy("http://localhost:8080/uyuni")
token = "some-bogus-token"

out = []
for system in c.system.listSystems(token):
    out.append("-" * 80)
    out.append("Hostname: {} ({})".format(system["name"], system["last_checkin"]))

    nfo = c.system.getDetails(token, system["id"])
    out.append("\tEntitlements:")
    out.append("\t  - {}".format(nfo["base_entitlement"]))
    for ent in nfo["addon_entitlements"]:
        out.append("\t  -".format(ent))

    net = c.system.getNetwork(token, system["id"])
    out.append("\tNetwork:")
    out.append("\t  - IPv4: {}, IPv6: {} ({})".format(net["ip"], net["ip6"], net["hostname"]))

    out.append("\tAvailable Channels (all):")
    for ch in c.system.listSubscribableBaseChannels(token, system["id"]) + c.system.listSubscribableChildChannels(token, system["id"]):
        out.append("\t  - {} ({})".format(ch["name"], ch["label"]))

    out.append("\tSubscribed to:")
    for ch in c.system.listSubscribedChildChannels(token, system["id"]):
        out.append("\t  - {} ({}), {}/{}. {}".format(ch["name"], ch["label"], ch["arch_name"], ch["arch_label"], ch["summary"]))
        out.append("\t    Sources:")
        for src in ch["contentSources"]:
            out.append("\t    - {} at {}".format(src["label"], src["sourceUrl"]))

# After logging is done
for l in out:
    print(l)
