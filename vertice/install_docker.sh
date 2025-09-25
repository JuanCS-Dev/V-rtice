# Passo 1: Remover a configuração de repositório errada que criamos antes
sudo rm /etc/apt/sources.list.d/docker.list

# Passo 2: Adicionar a chave de segurança do Docker (se já não foi feito, não há problema em rodar de novo)
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Passo 3: Configurar o repositório correto, FORÇANDO o uso do 'noble' (Ubuntu 24.04)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  noble stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Passo 4: Instalar o Docker Engine (agora vai funcionar)
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "✅ Docker instalado com sucesso!"
