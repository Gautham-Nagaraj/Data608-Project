# 1. setup docker
sudo apt update
sudo apt upgrade -y

sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y


# 2. setup docker-compose
sudo apt-get update
sudo apt  install docker-compose -y
# 3 install psql client
sudo apt-get install postgresql-client -y
# 3. run database
sudo docker-compose up -d db
# 3.1 wait for db to be ready
sleep 10
# 4 install python
sudo apt-get install python3-pip python3-venv -y
# 4.1 install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
# 5 install dependencies
uv sync
# 6. run migrations
uv run alembic upgrade head
# 7. install admin credentials
PGPASSWORD="ChangeMe123!" psql -h localhost -U stockroulette_user -d postgres -f db/init.sql
