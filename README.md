# Archived project

If you want to resume work, please contact us at https://lists.opensuse.org/archives/list/devel@lists.uyuni-project.org/ or https://gitter.im/uyuni-project/devel

<p><img src="https://img.shields.io/badge/EXPERIMENTAL-WIP-red" /></p>

# Uyuni API Gateway

This is an **experimental** API Gateway implementation for Uyuni Project and/or SUSE Manager. Built on top of [Gin Gonic](https://github.com/gin-gonic).

This project provides the following:

- On-the-fly translation from XML-RPC to REST (and vice versa)
- Swagger UI generation for Uyuni Server or SUSE Manager API (via REST)
- Python drop-in replacement for `xmlrpclib`.

## Project Status

Bleeding alpha with unfinished parts. PRs welcome!

More-less stable:

- The plain XML-RPC part should work.

Needs to be still done/finished:

- REST returns `nil` instead of an empty array, if such happens on Uyuni Server. This causes backward-incompatibility crashes for 3rd party software, such as Spacecmd.

- REST does not yet support method overloading. This should be done by type detection on the API signatures.
