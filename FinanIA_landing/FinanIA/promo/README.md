# FinanIA — Landing de Oferta (estática)

Site estático: HTML + React (via CDN/Babel) + CSS + imagens. **Não precisa de build** — basta servir os arquivos.

## Arquivos
- `Promo.html` — página (abra como `index` no servidor)
- `*.jsx` — componentes React (carregados pelo Babel no navegador)
- `*.css` — estilos
- `*.png`, `*.svg` — imagens/logos

---

## 1. Subir pro Git

```bash
cd promo
git init
git add .
git commit -m "FinanIA landing de oferta"
git branch -M main
git remote add origin git@github.com:SEU_USUARIO/finania-landing.git
git push -u origin main
```

---

## 2. Publicar na VPS

### Opção A — clonar direto na VPS
```bash
ssh usuario@SEU_IP
sudo mkdir -p /var/www/finania
sudo chown -R $USER:$USER /var/www/finania
git clone git@github.com:SEU_USUARIO/finania-landing.git /var/www/finania
```

### Atualizar depois de mudanças
```bash
cd /var/www/finania && git pull
```

---

## 3. Nginx

Crie `/etc/nginx/sites-available/finania`:

```nginx
server {
    listen 80;
    server_name finania.pro www.finania.pro;
    root /var/www/finania;

    # Promo.html como página inicial
    index Promo.html;
    location / {
        try_files $uri $uri/ /Promo.html;
    }

    # cache de assets estáticos
    location ~* \.(png|svg|jpg|jpeg|css|js|jsx|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Ative e recarregue:
```bash
sudo ln -s /etc/nginx/sites-available/finania /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### HTTPS (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d finania.pro -d www.finania.pro
```

---

## Notas
- O vídeo do YouTube exige **incorporação ativada** no YouTube Studio, senão dá erro 153.
- Para servir como `index.html` em vez de `Promo.html`, basta renomear o arquivo ou ajustar o `index` no Nginx.
