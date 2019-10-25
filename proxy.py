#!/usr/bin/env python3
""" DNS to DNS over TLS proxy. """

import os
import socket
import ssl
import sys


def query_dns_over_tls(server_ip, server_port, server_name, ca_path, query):
    """ Queries the given DNS server over TLS & returns response. """
    # create stream type socket
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.settimeout(10)
    except socket.error as error:
        print("TCP socket connection error: {}".format(error), file=sys.stderr)
        tcp_socket.disconnect()

    # wrap the socket in TLS context
    try:
        context = ssl.create_default_context()
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(ca_path)
    except ssl.SSLError as error:
        print("SSL error: {}".format(error.reason), file=sys.stderr)

    # connect to the remote server over TLS
    try:
        wrapped_socket = context.wrap_socket(tcp_socket, server_hostname=server_ip)
        wrapped_socket.connect((server_ip, server_port))
    except socket.timeout:
        print("Timeout connecting to the remote DNS server.", file=sys.stderr)
        wrapped_socket.disconnect()

    # verify hostname
    try:
        ssl.match_hostname(wrapped_socket.getpeercert(), server_name)
    except ssl.CertificateError as error:
        print("Certificate error: {}. Could not verify server name.".format(error), file=sys.stderr)

    # send DNS query & return the result
    wrapped_socket.send(query)
    result = wrapped_socket.recv(1024)
    return result


def main():
    """ Creates a TCP listening socket.
        DNS information was taken from https://developers.cloudflare.com/1.1.1.1/dns-over-tls/ """

    dns_server_ip = os.getenv('DNS_SERVER_IP', '1.1.1.1')
    dns_server_port = int(os.getenv('DNS_SERVER_PORT', '853'))
    dns_server_name = os.getenv('DNS_SERVER_NAME', 'cloudflare-dns.com')
    ca_path = os.getenv('CA_PATH', '/etc/ssl/certs/ca-certificates.crt')
    listening_socket_ip = os.getenv('LISTENING_SOCKET_IP', '0.0.0.0')
    listening_socket_port = int(os.getenv('LISTENING_SOCKET_PORT', '35353'))

    try:
        with open(ca_path):
            pass
    except IOError:
        print("Unable to open file: {}".format(ca_path), file=sys.stderr)
        sys.exit(1)

    try:
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening_socket.bind((listening_socket_ip, listening_socket_port))
        listening_socket.listen(5)
        while True:
            conn, address = listening_socket.accept()
            data = conn.recv(1024)
            result = query_dns_over_tls(
                dns_server_ip, dns_server_port, dns_server_name, ca_path, data)
            conn.sendto(result, address)
    except TypeError as error:
        print("TypeError: {}.".format(error), file=sys.stderr)
    except socket.error as error:
        print("Error establishing listening socket: {}".format(error), file=sys.stderr)
    finally:
        listening_socket.close()


if __name__ == '__main__':
    main()
