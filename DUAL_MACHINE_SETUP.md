# Dual Machine Setup - Development + Backend Server

## 🎯 Objetivo
Separar desenvolvimento (testing, IDE) do backend (containers rodando 24/7) para:
- Evitar sobrecarga térmica no PC principal
- Testes isolados sem overhead dos serviços
- Backend sempre disponível na rede para integração
- Desenvolvimento mais rápido e estável

---

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────┐          ┌──────────────────────────┐
│   PC Principal (Desktop)    │          │  Notebook/Server         │
│   i5-10400F / 16GB RAM      │◄────────►│  (Qualquer config)       │
├─────────────────────────────┤   LAN    ├──────────────────────────┤
│ - IDE (VSCode, PyCharm)     │  WiFi/   │ - Docker Backend (66     │
│ - Git                       │  Ethernet│   containers)            │
│ - Testes locais (pytest)    │          │ - Kafka, Redis, RabbitMQ │
│ - Claude Code               │          │ - PostgreSQL, Qdrant     │
│ - Browser/UI Development    │          │ - Grafana, Prometheus    │
│                             │          │                          │
│ Apenas containers de TESTE  │          │ Serviços SEMPRE rodando  │
│ (quando necessário)         │          │ (backend completo)       │
└─────────────────────────────┘          └──────────────────────────┘
         🖥️ Development                        🖥️ Backend Server
```

---

## 💻 Requisitos do Notebook/Server

### Mínimo Recomendado:
- **CPU:** Dual-core (i3, Ryzen 3) ou melhor
- **RAM:** 8 GB (12-16 GB ideal)
- **Storage:** 128 GB SSD
- **Rede:** Ethernet ou WiFi estável
- **OS:** Linux (Ubuntu Server, Debian) ou qualquer distro headless

### Configuração Ideal:
- **CPU:** Quad-core (i5, Ryzen 5)
- **RAM:** 16 GB
- **Storage:** 256 GB SSD
- **Rede:** Ethernet 1 Gbps
- **Ventilação:** Adequada (base refrigerada ou elevada)

**Observação:** Pode ser um notebook antigo que não serve mais para uso diário!

---

## 🚀 Setup do Backend Server (Notebook)

### 1. Instalação Base
```bash
# Ubuntu Server 22.04 LTS (headless)
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Ferramentas de monitoramento
sudo apt install htop iotop sysstat lm-sensors -y
sudo sensors-detect --auto
```

### 2. Configurar IP Estático (opcional mas recomendado)
```bash
# Editar netplan
sudo nano /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:  # ou seu interface (veja com 'ip a')
      dhcp4: no
      addresses:
        - 192.168.1.100/24  # Escolha um IP livre na sua rede
      gateway4: 192.168.1.1  # Gateway do seu roteador
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

```bash
sudo netplan apply
```

### 3. Clonar Projeto
```bash
cd ~
git clone https://github.com/JuanCS-Dev/V-rtice.git vertice-backend
cd vertice-backend

# Configurar Git
git config --global user.name "Vertice Backend"
git config --global user.email "juan.brainfarma@gmail.com"
```

### 4. Configurar Variáveis de Ambiente
```bash
# Copiar exemplo
cp .env.example .env

# Editar para produção/server
nano .env
```

**Importante:** Ajustar para permitir conexões externas:
```env
# Binding
REDIS_HOST=0.0.0.0
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://192.168.1.100:9092  # IP do notebook
POSTGRES_HOST=0.0.0.0

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000

# Grafana
GRAFANA_HOST=0.0.0.0
```

### 5. Subir Backend Completo
```bash
# Primeira vez (pode demorar)
docker compose up -d

# Verificar
docker ps
docker stats --no-stream

# Logs
docker compose logs -f --tail=50
```

### 6. Configurar Auto-Start (systemd)
```bash
# Criar service
sudo nano /etc/systemd/system/vertice-backend.service
```

```ini
[Unit]
Description=Vertice Backend Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/juan/vertice-backend
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=juan

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable vertice-backend
sudo systemctl start vertice-backend
sudo systemctl status vertice-backend
```

### 7. Monitoramento Remoto
```bash
# Instalar SSH se não tiver
sudo apt install openssh-server -y
sudo systemctl enable ssh

# Configurar firewall (UFW)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8000/tcp    # API Gateway
sudo ufw allow 3000/tcp    # Grafana
sudo ufw allow 9092/tcp    # Kafka
sudo ufw allow 6379/tcp    # Redis
sudo ufw allow 5432/tcp    # PostgreSQL
sudo ufw allow 6333/tcp    # Qdrant
sudo ufw enable
```

---

## 🖥️ Setup do PC Principal (Development)

### 1. Configurar Acesso ao Backend
```bash
# Adicionar ao /etc/hosts
sudo nano /etc/hosts
```

```
192.168.1.100  vertice-backend  # IP do notebook
```

### 2. Variáveis de Ambiente para Desenvolvimento
```bash
# .env.development (criar novo)
nano .env.development
```

```env
# Apontar para servidor remoto
REDIS_HOST=vertice-backend
REDIS_PORT=6379

KAFKA_BOOTSTRAP_SERVERS=vertice-backend:9092

POSTGRES_HOST=vertice-backend
POSTGRES_PORT=5432

QDRANT_HOST=vertice-backend
QDRANT_PORT=6333

API_GATEWAY_URL=http://vertice-backend:8000

GRAFANA_URL=http://vertice-backend:3000

# Backend rodando remotamente
BACKEND_MODE=remote
```

### 3. Rodar Testes Localmente
```bash
# Usar .env.development
export $(cat .env.development | xargs)

# Rodar testes (conectam no backend remoto)
cd backend/services/maximus_core_service
pytest tests/ -v

# Desenvolvimento local
python -m uvicorn main:app --reload
# (conecta nos serviços do notebook)
```

### 4. Scripts para Gerenciamento Remoto
```bash
# scripts/remote-backend.sh
nano scripts/remote-backend.sh
```

```bash
#!/bin/bash
BACKEND_IP="192.168.1.100"
BACKEND_USER="juan"

case "$1" in
  status)
    ssh $BACKEND_USER@$BACKEND_IP "cd vertice-backend && docker ps"
    ;;
  stats)
    ssh $BACKEND_USER@$BACKEND_IP "docker stats --no-stream"
    ;;
  logs)
    ssh $BACKEND_USER@$BACKEND_IP "cd vertice-backend && docker compose logs -f --tail=50 ${2:-}"
    ;;
  restart)
    ssh $BACKEND_USER@$BACKEND_IP "cd vertice-backend && docker compose restart ${2:-}"
    ;;
  pull)
    ssh $BACKEND_USER@$BACKEND_IP "cd vertice-backend && git pull && docker compose up -d --build"
    ;;
  temp)
    ssh $BACKEND_USER@$BACKEND_IP "sensors | grep -E 'Package|Composite|temp1'"
    ;;
  health)
    ssh $BACKEND_USER@$BACKEND_IP "cd vertice-backend && ./scripts/health-check.sh"
    ;;
  ssh)
    ssh $BACKEND_USER@$BACKEND_IP
    ;;
  *)
    echo "Usage: $0 {status|stats|logs|restart|pull|temp|health|ssh} [service-name]"
    ;;
esac
```

```bash
chmod +x scripts/remote-backend.sh
```

**Uso:**
```bash
./scripts/remote-backend.sh status    # Ver containers rodando
./scripts/remote-backend.sh stats     # Recursos
./scripts/remote-backend.sh logs kafka # Logs de um serviço
./scripts/remote-backend.sh temp      # Temperatura
./scripts/remote-backend.sh pull      # Git pull e rebuild
./scripts/remote-backend.sh ssh       # SSH direto
```

---

## 📊 Monitoramento

### No Notebook (Backend Server)
```bash
# Terminal watch
watch -n 2 'docker stats --no-stream; echo "---"; sensors | grep -E "Package|Composite"'

# Ou instalar Glances
sudo apt install glances -y
glances
```

### No PC Principal (via Browser)
- **Grafana:** http://vertice-backend:3000
- **Qdrant Dashboard:** http://vertice-backend:6333/dashboard

### Alertas (opcional)
Configurar Prometheus + Alertmanager para notificações via Telegram/Email se:
- CPU > 80%
- RAM > 90%
- Temperatura > 70°C
- Container down

---

## 🔧 Workflow de Desenvolvimento

### Cenário 1: Desenvolvimento de Feature
```bash
# PC Principal
cd vertice-dev
git checkout -b feature/new-thing

# Editar código
code backend/services/maximus_core_service/

# Testar localmente (usa backend remoto)
export $(cat .env.development | xargs)
pytest tests/unit/

# Commit
git add .
git commit -m "feat: new thing"
git push

# Deploy no servidor
./scripts/remote-backend.sh pull
```

### Cenário 2: Testes de Integração
```bash
# PC Principal - Apenas roda os testes
cd backend/services/maximus_core_service
pytest tests/integration/ -v

# Backend está sempre rodando no notebook
# Sem necessidade de subir/derrubar containers
```

### Cenário 3: Debugging
```bash
# Ver logs em tempo real
./scripts/remote-backend.sh logs maximus-core

# SSH para investigar
./scripts/remote-backend.sh ssh
# Dentro do servidor:
docker exec -it maximus-core bash
```

### Cenário 4: Manutenção
```bash
# Reiniciar um serviço problemático
./scripts/remote-backend.sh restart maximus-core

# Verificar saúde
./scripts/remote-backend.sh health

# Temperatura
./scripts/remote-backend.sh temp
```

---

## 💰 Custo/Benefício

### Antes (Single Machine)
- ❌ 66 containers no PC principal
- ❌ Load 5.46 (91% saturação)
- ❌ CPU 65°C / NVMe 62.9°C
- ❌ Testes lentos (competição por recursos)
- ❌ Instabilidade / travamentos
- ❌ Impossível usar o PC durante testes

### Depois (Dual Machine)
- ✅ PC principal limpo (só IDE + testes)
- ✅ Load < 2.0 (trabalho normal)
- ✅ Temperaturas normais (~45°C)
- ✅ Backend sempre disponível
- ✅ Testes rápidos (sem overhead)
- ✅ Desenvolvimento fluido
- ✅ Pode usar PC enquanto testa

**Investimento:** Notebook usado (R$ 500-1500) ou reutilizar um antigo

---

## 🎓 Alternativas

### Opção 1: Cloud (mais caro)
- AWS EC2 t3.medium: ~$30/mês
- DigitalOcean Droplet 4GB: ~$24/mês
- **Prós:** Sempre online, IP público
- **Contras:** Custo recorrente, latência

### Opção 2: Raspberry Pi 4 (8GB)
- **Custo:** ~R$ 800-1200
- **Prós:** Baixo consumo, silencioso
- **Contras:** ARM (algumas imagens podem não funcionar), menos RAM

### Opção 3: Mini PC usado
- **Custo:** ~R$ 1000-2000
- **Prós:** x86, baixo consumo, compacto
- **Contras:** Mais caro que notebook usado

### Opção 4: Notebook Antigo (RECOMENDADO)
- **Custo:** R$ 500-1500 ou GRÁTIS se tiver um parado
- **Prós:** Já tem bateria (UPS grátis), tela (debug), barato
- **Contras:** Pode esquentar (resolver com base refrigerada)

---

## ✅ Checklist de Setup

### Notebook/Server
- [ ] Ubuntu Server instalado
- [ ] Docker + Docker Compose instalado
- [ ] IP estático configurado (ou anotar IP DHCP)
- [ ] Projeto clonado
- [ ] `.env` configurado para bind 0.0.0.0
- [ ] `docker compose up -d` funcionando
- [ ] Firewall (UFW) configurado
- [ ] SSH habilitado
- [ ] Systemd service configurado (auto-start)
- [ ] Monitoramento básico (htop, sensors)

### PC Principal
- [ ] `/etc/hosts` com IP do backend
- [ ] `.env.development` criado
- [ ] SSH key configurado (passwordless)
- [ ] `scripts/remote-backend.sh` criado e testado
- [ ] Teste de conexão: `ping vertice-backend`
- [ ] Teste de serviço: `curl http://vertice-backend:8000/health`
- [ ] Pytest rodando com backend remoto

---

## 🚨 Troubleshooting

### Backend não responde
```bash
# Verificar se está rodando
./scripts/remote-backend.sh status

# Verificar firewall
ssh juan@vertice-backend "sudo ufw status"

# Testar conectividade
ping vertice-backend
telnet vertice-backend 8000
```

### Containers travando no notebook
```bash
# SSH no servidor
ssh juan@vertice-backend

# Verificar recursos
htop
docker stats

# Reiniciar problemáticos
docker restart maximus-core

# Último caso: reiniciar tudo
docker compose down && docker compose up -d
```

### Notebook superaquecendo
```bash
# Verificar temperatura
ssh juan@vertice-backend sensors

# Limitar recursos se necessário
# Editar docker-compose.yml com deploy.resources.limits

# Considerar:
# - Base refrigerada
# - Elevar o notebook (melhor ventilação)
# - Limpar ventoinha
# - Pasta térmica nova
```

---

## 📝 Conclusão

Setup dual-machine é **altamente recomendado** para projetos com muitos microserviços:

1. **Libera PC principal** para desenvolvimento
2. **Backend sempre disponível** (sem subir/derrubar)
3. **Testes mais rápidos** (sem competição de recursos)
4. **Melhor experiência** de desenvolvimento
5. **Custo baixo** (notebook usado ou antigo)

**Próximo passo:** Comprar/reutilizar notebook e seguir checklist de setup!

---

**Generated:** 2025-10-21
**Author:** Claude Code (Vertice Project)
