FROM caddy:2
COPY Caddyfile /etc/caddy/Caddyfile
VOLUME /var/www
EXPOSE 80 443

ARG WEB_USERNAME
ARG WEB_PASSWORD

RUN echo $WEB_PASSWORD > /tmp/test

RUN echo $WEB_USERNAME $(caddy hash-password --plaintext "$WEB_PASSWORD") >> /etc/caddy/basicauth.conf

RUN cat /etc/caddy/basicauth.conf

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]