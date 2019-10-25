# DNS to DNS over TLS proxy

## Implementation

This is a simple proxy that listens to TCP on a socket, forwards the bytes received to a remote server, and returns the answer through the socket. It uses only the Python 3 standard library. It can handle one DNS query at a time. By default, it listens on `0.0.0.0:35353` and sends DNS queries to Cloudflare. The listening address and port and the DNS server that should be used to forward the queries are configurable using environment variables. Here are the options that are configurable and their default values:

```bash
DNS_SERVER_IP = 1.1.1.1
DNS_SERVER_PORT = 853
DNS_SERVER_NAME = cloudflare-dns.com
CA_PATH = /etc/ssl/certs/ca-certificates.crt
LISTENING_SOCKET_IP = 0.0.0.0
LISTENING_SOCKET_PORT = 35353
```

## How to run

Unarchive this project:

Bring it up using Docker Compose from the directory where you cloned the source code:

```bash
docker build -f ./Dockerfile -t dns-proxy .
```

Run the image:

```bash
docker run --rm -d -p 35353:35353 -p 853:853 dns-proxy
```

Test it with `dig`:

```bash
dig @localhost -p 35353 +tcp google.com
```

## Improvements

- First of all, to use this kind of service in production, it is desirable to have true multithreading. This service should be written in a language with better support for that, like Go. It is possible to handle threading in Python, but the performance will be inferior. (see [GIL](https://wiki.python.org/moin/GlobalInterpreterLock)).
- Implement a way of handling multiple requests at a time.
- Implement a UDP listener.
- Implement a caching layer.
- Implement tests.
- Validate requests to make sure they are DNS requests.
- Implement redundancy for the upstream DNS servers. We should be able to send the request to another server if the first is unavailable, or better yet, send the request to the server with the shortest response time.

## Considering a microservice architecture; how would you see this the dns to dns-over-tls proxy used

There are three main scenarios where this can be used:

- This proxy be deployed as a service on its own behind a load balancer. Other microservices send their DNS queries to this proxy.
- If you have your microservices running as containers over a managed host, you can deploy the proxy to each undelying host, making it transparent to the other containers.
- You can integrate the proxy on each individual microservice container or instance.

## What are the security concerns for this kind of service

### Security concerns particular to this implementation

- There is no validation to ensure only real DNS queries are being forwarded.
- By default, listens on all networks (`0.0.0.0`). This should be changed to the intended network in each case.
- Affected by vulnerabilities in the `python:latest` Docker container. We should use a custom hardened container.
- There is no insurance that only the intended clients can use this service. This can be addressed in the environment where the container is deployed. For example, we would want it to be on a private subnet that can only be accessed by the intended clients with proper security groups configured and outbound traffic going through a NAT gateway.

### Some security concerns raised by the IETF

A quote from [draft-ietf-dprive-dns-over-tls-05](https://tools.ietf.org/id/draft-ietf-dprive-dns-over-tls-05.html):

- There are known attacks on TLS, such as person-in-the-middle and protocol downgrade. These are general attacks on TLS and not specific to DNS-over-TLS; please refer to the TLS RFCs for discussion of these security issues. Clients and servers MUST adhere to the TLS implementation recommendations and security considerations of [RFC7525](https://tools.ietf.org/html/rfc7525) or its successor. DNS clients keeping track of servers known to support TLS enables clients to detect downgrade attacks. For servers with no connection history and no apparent support for TLS, depending on their Privacy Profile and privacy requirements, clients may choose to (a) try another server when available, (b) continue without TLS, or (c) refuse to forward the query.
- Middleboxes [RFC3234](http://tools.ietf.org/html/rfc3234) are present in some networks and have been known to interfere with normal DNS resolution. Use of a designated port for DNS-over-TLS should avoid such interference. In general, clients that attempt TLS and fail can either fall back on unencrypted DNS, or wait and retry later, depending on their Privacy Profile and privacy requirements.
- Any DNS protocol interactions performed in the clear can be modified by a person-in-the-middle attacker. For example, unencrypted queries and responses might take place over port 53 between a client and server. For this reason, clients MAY discard cached information about server capabilities advertised in clear text.
- This document does not itself specify ideas to resist known traffic analysis or side channel leaks. Even with encrypted messages, a well-positioned party may be able to glean certain details from an analysis of message timings and sizes. Clients and servers may consider the use of a padding method to address privacy leakage due to message sizes. [I-D.edns0-padding](http://tools.ietf.org/html/draft-mayrhofer-edns0-padding-01)
