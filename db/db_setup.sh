#!/usr/bin/env bash
set -euo pipefail

# Variables
PG_USER="608project"
PG_PASS="608project"
PG_VOLUME="pgdata_608project"
CONTAINER_NAME="postgres_608project"
PG_IMAGE="postgres:latest"
HOST_PORT=5432
CONTAINER_PORT=5432

# 1. Install Docker
echo "Using apt-get to install Docker..."
apt-get update
apt-get install -y \
ca-certificates \
curl \
gnupg \
lsb-release
# Add Docker’s official GPG key and repo
curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | \
gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
$(lsb_release -cs) stable" | \
tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io


# 2. Enable and start Docker service
echo "Enabling and starting Docker..."
systemctl enable docker
systemctl start docker

# 3. Create a Docker volume for persistence
echo "Creating Docker volume '${PG_VOLUME}'..."
docker volume create "${PG_VOLUME}"

# 4. Run PostgreSQL container
echo "Running Postgres container '${CONTAINER_NAME}'..."
# Remove any existing container with the same name
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
  echo "Container ${CONTAINER_NAME} already exists. Stopping and removing it..."
  docker stop "${CONTAINER_NAME}" && docker rm "${CONTAINER_NAME}"
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  -e POSTGRES_USER="${PG_USER}" \
  -e POSTGRES_PASSWORD="${PG_PASS}" \
  -v "${PG_VOLUME}":/var/lib/postgresql/data \
  -p "${HOST_PORT}":"${CONTAINER_PORT}" \
  "${PG_IMAGE}"

echo "✅ Done! Postgres is running on port ${HOST_PORT}, with user/password '${PG_USER}'."
