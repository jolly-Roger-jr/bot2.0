# Инструкция по развертыванию в продакшен

## 1. Подготовка сервера

### Требования:
- Ubuntu 20.04+ / Debian 11+
- Docker и Docker Compose
- Git
- Минимум 1GB RAM, 10GB диска

### Установка зависимостей:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER