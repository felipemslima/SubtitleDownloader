# Instrucoes Para Subir o Web App na Nuvem

Este guia descreve como publicar o Subtitle Downloader Web em uma instancia Ubuntu, como Oracle Always Free, na mesma maquina onde ja existe outro servico.

O caminho recomendado para testar primeiro e **sem Docker**:

- Flask backend rodando com Gunicorn e systemd;
- React frontend compilado com Vite e servido pelo Nginx;
- Nginx fazendo proxy de `/api` para o Flask;
- systemd iniciando o backend junto com a instancia;
- Nginx iniciando automaticamente junto com o sistema.
- usuario acessando pela porta padrao HTTP, ou seja, `http://IP_DA_INSTANCIA/`.

O web app atual nao usa ADB e nao le pastas locais do servidor. O usuario seleciona videos no navegador, o frontend envia apenas nomes/metadados, e o backend retorna um ZIP com legendas.

## Objetivo Nesta Maquina

Como esta instancia ja roda o servidor de licencas do PDD na porta `8000`, a forma mais simples de colocar este segundo servico no ar e:

- manter o PDD License Server como esta, em `0.0.0.0:8000`;
- rodar o backend do Subtitle Downloader apenas localmente em `127.0.0.1:5000`;
- usar Nginx escutando a porta publica `80`;
- servir o frontend em `http://IP_DA_INSTANCIA/`;
- encaminhar chamadas de `http://IP_DA_INSTANCIA/api/...` para `http://127.0.0.1:5000/api/...`.

Assim o usuario final acessa apenas:

```text
http://IP_DA_INSTANCIA/
```

Nao exponha publicamente as portas `5000`, `5173`, `4173`, `7001` ou `7002` para este app. Em producao, deixe exposta apenas a porta `80` e, depois, `443` quando configurar HTTPS.

## Deploy Rapido na Mesma VM Sem Docker

Use esta secao se voce quer apenas colocar no ar do jeito mais simples possivel.

### 1. Liberar porta 80

No painel da Oracle, na Security List ou NSG da VCN, adicione:

```text
Stateless: No
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 80
Description: HTTP
```

Na VM:

```bash
sudo ufw allow 80/tcp || true
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
```

### 2. Instalar pacotes

```bash
sudo apt update
sudo apt install -y git nginx python3 python3-venv python3-pip curl rsync
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3. Colocar o projeto em `/opt/subtitle-downloader`

Se for clonar do Git:

```bash
sudo mkdir -p /opt/subtitle-downloader
sudo chown -R "$USER:$USER" /opt/subtitle-downloader
git clone URL_DO_REPOSITORIO /opt/subtitle-downloader
```

Se voce for enviar os arquivos manualmente, envie a pasta do projeto para:

```text
/opt/subtitle-downloader
```

Depois:

```bash
cd /opt/subtitle-downloader
```

### 4. Criar `.env`

```bash
cat > /opt/subtitle-downloader/.env <<'EOF'
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
VITE_API_LOCAL_BASE_URL=/api
EOF
```

### 5. Instalar backend

```bash
cd /opt/subtitle-downloader
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 6. Criar servico systemd do backend

```bash
sudo tee /etc/systemd/system/subtitle-downloader-backend.service > /dev/null <<'EOF'
[Unit]
Description=Subtitle Downloader Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/opt/subtitle-downloader/backend
EnvironmentFile=/opt/subtitle-downloader/.env
ExecStart=/opt/subtitle-downloader/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Se a instancia usa outro usuario, como `opc`, edite o arquivo:

```bash
sudo nano /etc/systemd/system/subtitle-downloader-backend.service
```

e troque:

```ini
User=ubuntu
```

por:

```ini
User=opc
```

Ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable subtitle-downloader-backend
sudo systemctl start subtitle-downloader-backend
sudo systemctl status subtitle-downloader-backend
```

Teste local:

```bash
curl http://127.0.0.1:5000/api/health
```

### 7. Buildar frontend

```bash
cd /opt/subtitle-downloader/frontend
npm install
npm run build
sudo mkdir -p /var/www/subtitle-downloader
sudo rsync -a --delete dist/ /var/www/subtitle-downloader/
sudo chown -R www-data:www-data /var/www/subtitle-downloader
```

### 8. Configurar Nginx na porta 80

```bash
sudo tee /etc/nginx/sites-available/subtitle-downloader > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/subtitle-downloader;
    index index.html;

    client_max_body_size 100m;

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
```

Desative o site padrao do Nginx, se existir, e ative este:

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/subtitle-downloader /etc/nginx/sites-enabled/subtitle-downloader
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx
```

### 9. Testar

Na VM:

```bash
curl http://127.0.0.1/api/health
```

No navegador:

```text
http://IP_DA_INSTANCIA/
```

Se a API responder localmente mas o navegador nao abrir, confira:

```bash
sudo systemctl status nginx
sudo systemctl status subtitle-downloader-backend
sudo journalctl -u subtitle-downloader-backend -n 80 --no-pager
sudo tail -80 /var/log/nginx/error.log
```

### 10. Atualizar depois

```bash
cd /opt/subtitle-downloader
git pull

source venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
npm run build
sudo rsync -a --delete dist/ /var/www/subtitle-downloader/

sudo systemctl restart subtitle-downloader-backend
sudo systemctl reload nginx
```

## Variaveis de Ambiente

Na nuvem, use uma configuracao parecida com esta no arquivo `.env` da raiz do projeto:

```env
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

VITE_DEV_HOST=127.0.0.1
VITE_DEV_PORT=5173
VITE_PREVIEW_HOST=127.0.0.1
VITE_PREVIEW_PORT=4173

VITE_API_LOCAL_BASE_URL=/api
```

Para producao com Nginx, `VITE_API_LOCAL_BASE_URL=/api` e o melhor valor, porque o navegador chama a API no mesmo dominio do site.

## Checklist Oracle Cloud

Antes de instalar o app:

1. No painel da Oracle, libere as portas necessarias na Security List ou NSG da VCN.
2. Para site publico com Nginx, libere pelo menos:
   - TCP `80`;
   - TCP `443`, quando configurar HTTPS.
3. No Ubuntu, confira o firewall local:

```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

Se voce for testar sem dominio e sem Nginx, tambem pode liberar portas temporarias como `5173` e `5000`, mas para producao prefira expor apenas `80/443`.

## Instalacao Como App no Chrome Android

O frontend e um PWA. No Chrome Android, ele pode aparecer com a opcao **Instalar app** quando:

- o site esta em HTTPS, ou em `localhost` durante desenvolvimento;
- o arquivo `manifest.webmanifest` esta acessivel;
- o `sw.js` esta acessivel na raiz do site;
- os icones em `/icons/` carregam corretamente;
- o app foi aberto pelo menos uma vez no Chrome.

Em producao, configure HTTPS com Certbot. Sem HTTPS, o Chrome normalmente nao mostra a opcao de instalacao em Android.

Depois do deploy, teste:

```bash
curl -I https://legendas.seudominio.com/manifest.webmanifest
curl -I https://legendas.seudominio.com/sw.js
curl -I https://legendas.seudominio.com/icons/icon-192.png
```

No Android, abra o site no Chrome e procure:

```text
Menu de tres pontos -> Instalar app
```

## Deploy Sem Docker

### 1. Instalar pacotes do sistema

```bash
sudo apt update
sudo apt install -y git nginx python3 python3-venv python3-pip curl
```

Instale Node.js. Uma opcao comum e usar NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

### 2. Baixar ou atualizar o projeto

Use `/opt/subtitle-downloader` como diretorio do app:

```bash
sudo mkdir -p /opt/subtitle-downloader
sudo chown -R "$USER:$USER" /opt/subtitle-downloader
```

Se for clonar do Git:

```bash
git clone URL_DO_REPOSITORIO /opt/subtitle-downloader
cd /opt/subtitle-downloader
```

Se o projeto ja existir:

```bash
cd /opt/subtitle-downloader
git pull
```

### 3. Criar o `.env`

```bash
cd /opt/subtitle-downloader
cp .env.example .env
nano .env
```

Conteudo recomendado:

```env
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
VITE_API_LOCAL_BASE_URL=/api
```

### 4. Configurar o backend Flask

```bash
cd /opt/subtitle-downloader
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Teste manualmente:

```bash
cd /opt/subtitle-downloader/backend
/opt/subtitle-downloader/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
```

Em outro terminal:

```bash
curl http://127.0.0.1:5000/api/health
```

Se responder `ok`, pare o Gunicorn com `Ctrl+C`.

### 5. Criar servico systemd do backend

Crie o arquivo:

```bash
sudo nano /etc/systemd/system/subtitle-downloader-backend.service
```

Conteudo:

```ini
[Unit]
Description=Subtitle Downloader Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/opt/subtitle-downloader/backend
EnvironmentFile=/opt/subtitle-downloader/.env
ExecStart=/opt/subtitle-downloader/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Se seu usuario nao for `ubuntu`, troque `User=ubuntu` pelo usuario correto.

Ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable subtitle-downloader-backend
sudo systemctl start subtitle-downloader-backend
sudo systemctl status subtitle-downloader-backend
```

Logs:

```bash
journalctl -u subtitle-downloader-backend -f
```

### 6. Build do frontend React

```bash
cd /opt/subtitle-downloader/frontend
npm install
npm run build
```

Copie o build para uma pasta servida pelo Nginx:

```bash
sudo mkdir -p /var/www/subtitle-downloader
sudo rsync -a --delete dist/ /var/www/subtitle-downloader/
sudo chown -R www-data:www-data /var/www/subtitle-downloader
```

### 7. Configurar Nginx

Se voce tiver um dominio ou subdominio, por exemplo `legendas.seudominio.com`, crie um server block proprio.

```bash
sudo nano /etc/nginx/sites-available/subtitle-downloader
```

Conteudo:

```nginx
server {
    listen 80;
    server_name legendas.seudominio.com;

    root /var/www/subtitle-downloader;
    index index.html;

    client_max_body_size 10m;

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Ative:

```bash
sudo ln -s /etc/nginx/sites-available/subtitle-downloader /etc/nginx/sites-enabled/subtitle-downloader
sudo nginx -t
sudo systemctl reload nginx
```

Se voce ainda nao tem dominio, pode testar com IP trocando:

```nginx
server_name _;
```

Mas se ja existe outro site na mesma maquina usando `server_name _`, prefira usar um subdominio para evitar conflito.

### 8. HTTPS com Certbot

Depois que o DNS do subdominio apontar para a instancia:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d legendas.seudominio.com
```

O Certbot ajusta o Nginx e configura renovacao automatica.

### 9. Atualizar o app depois

```bash
cd /opt/subtitle-downloader
git pull

source venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
npm run build
sudo rsync -a --delete dist/ /var/www/subtitle-downloader/

sudo systemctl restart subtitle-downloader-backend
sudo systemctl reload nginx
```

## Rodar Sem Docker Apenas Para Teste

Use isso se quiser testar rapido sem Nginx.

No `.env`:

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
VITE_DEV_HOST=0.0.0.0
VITE_DEV_PORT=5173
VITE_API_LOCAL_BASE_URL=http://IP_DA_INSTANCIA:5000/api
```

Terminal 1:

```bash
cd /opt/subtitle-downloader/backend
source ../venv/bin/activate
python app.py
```

Terminal 2:

```bash
cd /opt/subtitle-downloader/frontend
npm run dev
```

Acesse:

```text
http://IP_DA_INSTANCIA:5173
```

Esse modo e simples, mas nao e ideal para producao, porque expoe o servidor dev do Vite e o Flask diretamente.

## Deploy Com Docker

O projeto ja possui `docker-compose.yml`, `backend/dockerfile` e `frontend/dockerfile`. O compose atual e mais voltado para desenvolvimento, porque o frontend roda `npm run dev`.

### 1. Instalar Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Saia e entre novamente no SSH para o grupo `docker` valer.

### 2. Configurar `.env`

Para compose de desenvolvimento:

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
VITE_API_LOCAL_BASE_URL=http://IP_DA_INSTANCIA:7001/api
```

### 3. Subir

```bash
cd /opt/subtitle-downloader
docker compose up --build -d
docker compose ps
```

URLs:

```text
Frontend: http://IP_DA_INSTANCIA:7002
Backend:  http://IP_DA_INSTANCIA:7001/api/health
```

Logs:

```bash
docker compose logs -f
```

Parar:

```bash
docker compose down
```

### 4. Iniciar Docker junto com a instancia

O Docker normalmente ja inicia com o sistema. Confira:

```bash
sudo systemctl enable docker
```

Para garantir que o compose suba junto com a instancia, crie:

```bash
sudo nano /etc/systemd/system/subtitle-downloader-compose.service
```

Conteudo:

```ini
[Unit]
Description=Subtitle Downloader Docker Compose
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/subtitle-downloader
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable subtitle-downloader-compose
sudo systemctl start subtitle-downloader-compose
```

## Observacoes Para Mesma Maquina Com Outro Servico

- Se seu servidor de licenciamento ja usa Nginx, adicione este app como outro `server_name`, preferencialmente em subdominio separado.
- Evite expor `5000`, `5173`, `7001` ou `7002` publicamente em producao.
- Use Nginx na frente e exponha apenas `80/443`.
- Se quiser publicar em um caminho como `/legendas/` em vez de subdominio, o frontend precisa ser ajustado para base path no Vite. O caminho mais simples e usar subdominio.
