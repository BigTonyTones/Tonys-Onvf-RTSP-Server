# Reverse Proxy Setup for HTTPS

This guide covers setting up HTTPS for the web UI using common reverse proxies.

**Important**: The reverse proxy only handles the **web UI** (default port 5552). RTSP streams (port 8554) and ONVIF services use their own protocols and are **not proxied** through the web server. Clients connect directly to these services.

## Nginx

### Basic Configuration

```nginx
server {
    listen 80;
    server_name onvif.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name onvif.example.com;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5552;
        proxy_http_version 1.1;

        # WebSocket support (required for HLS.js live streaming)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-lived connections
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

### With Basic Authentication

```nginx
server {
    listen 443 ssl http2;
    server_name onvif.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Basic auth (generate with: htpasswd -c /etc/nginx/.htpasswd username)
    auth_basic "ONVIF Server";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:5552;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Generate the password file:
```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

---

## Traefik (v2/v3)

### Docker Compose Labels

Add these labels to your ONVIF server container in `docker-compose.yml`:

```yaml
services:
  onvif-server:
    image: your-onvif-image
    labels:
      - "traefik.enable=true"
      # HTTP to HTTPS redirect
      - "traefik.http.middlewares.onvif-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.onvif-http.rule=Host(`onvif.example.com`)"
      - "traefik.http.routers.onvif-http.entrypoints=web"
      - "traefik.http.routers.onvif-http.middlewares=onvif-https-redirect"
      # HTTPS router
      - "traefik.http.routers.onvif.rule=Host(`onvif.example.com`)"
      - "traefik.http.routers.onvif.entrypoints=websecure"
      - "traefik.http.routers.onvif.tls=true"
      - "traefik.http.routers.onvif.tls.certresolver=letsencrypt"
      - "traefik.http.services.onvif.loadbalancer.server.port=5552"
    networks:
      - traefik
```

### Traefik Static Configuration

Ensure your Traefik instance has Let's Encrypt configured:

```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    exposedByDefault: false
```

**Note**: RTSP ports (8554) must be exposed separately and are not handled by Traefik's HTTP routing. Use TCP routing if needed, but RTSP clients typically connect directly.

---

## Caddy

Caddy automatically provisions SSL certificates via Let's Encrypt.

### Caddyfile

```caddyfile
onvif.example.com {
    reverse_proxy localhost:5552
}
```

That's it. Caddy handles:
- Automatic HTTPS certificate from Let's Encrypt
- HTTP to HTTPS redirect
- Certificate renewal

### With Basic Authentication

```caddyfile
onvif.example.com {
    basicauth {
        # Generate hash with: caddy hash-password
        admin $2a$14$your_hashed_password_here
    }
    reverse_proxy localhost:5552
}
```

Generate password hash:
```bash
caddy hash-password
```

---

## Important Caveats

1. **RTSP is not proxied**: RTSP streams run on port 8554 (by default) and use the RTSP protocol, not HTTP. Clients (NVRs, VLC, etc.) connect directly to the RTSP port. The reverse proxy only secures the web dashboard.

2. **ONVIF services are not proxied**: Each virtual camera has its own ONVIF port. These SOAP-based services are accessed directly by NVRs during camera discovery and configuration.

3. **WebSocket support is required**: The HLS.js video player in the web UI uses WebSocket connections for live streaming previews. Ensure your proxy configuration includes WebSocket upgrade headers.

4. **Internal network recommended**: Since RTSP and ONVIF cannot be easily secured via the reverse proxy, this application is best suited for internal/trusted networks. If external access is required, consider VPN access instead of exposing RTSP ports.

5. **Port configuration**: If you run the web UI on a different port (e.g., `--port 8080`), update the `proxy_pass` or `reverse_proxy` directives accordingly.
