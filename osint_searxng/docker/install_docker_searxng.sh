#!/bin/sh

if docker ps -a --format '{{.Names}}' | grep -qx 'searxng-valkey'; then
    echo "searxng already installed"

else

    docker compose up -d
    
    until curl -sf http://127.0.0.1:8888/ > /dev/null; do
        sleep 2
    done
    
    echo "SearXNG configuration."
    docker compose stop
    
    # Add json capability to searxng
    cat >> ./core-config/settings.yml <<'EOF'
    
search:
  formats:
    - html
    - json
EOF

fi

docker compose up -d
echo "SearXNG ready."
