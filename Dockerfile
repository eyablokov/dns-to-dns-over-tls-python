FROM python:latest

# ENV DNS_SERVER_IP 1.1.1.1
# ENV DNS_SERVER_PORT 853
# ENV DNS_SERVER_NAME cloudflare-dns.com
# ENV CA_PATH /etc/ssl/certs/ca-certificates.crt
# ENV LISTENING_SOCKET_IP 0.0.0.0
# ENV LISTENING_SOCKET_PORT 35353

ADD . /proxy
WORKDIR /proxy

EXPOSE 35353
EXPOSE 853

ENTRYPOINT [ "python", "./proxy.py" ]