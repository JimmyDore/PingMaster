# Guide de Migration/Installation VPS - PingMaster

## 1. Configuration Initiale du VPS

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx

# Ajout de l'utilisateur au groupe docker
sudo usermod -aG docker $USER
```

## 2. Configuration SSH pour GitHub Actions

```bash
# Générer une clé SSH pour GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions
# Ne pas mettre de passphrase

# Ajouter aux clés autorisées
cat ~/.ssh/github-actions.pub >> ~/.ssh/authorized_keys

# Copier la clé privée (à mettre dans GitHub Secrets)
cat ~/.ssh/github-actions
```

## 3. Configuration Nginx

```bash
# Créer la configuration
sudo nano /etc/nginx/sites-available/api.conf
```

```nginx:/etc/nginx/sites-available/api.conf
server {
    listen 80;
    server_name pingmaster.jimmydore.fr jimmydore.fr;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activer la configuration
sudo ln -s /etc/nginx/sites-available/api.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optionnel
sudo nginx -t
sudo systemctl restart nginx
```

## 4. Configuration SSL avec Certbot

```bash
# Obtenir le certificat SSL
sudo certbot --nginx -d pingmaster.jimmydore.fr -d jimmydore.fr

# Vérifier le renouvellement automatique
sudo certbot renew --dry-run
```

## 5. Configuration du Pare-feu (UFW)

```bash
# Configuration des règles de base
sudo ufw allow ssh        # Port 22
sudo ufw allow http      # Port 80
sudo ufw allow https     # Port 443

# Activer le pare-feu
sudo ufw enable

# Vérifier le statut
sudo ufw status verbose
```

## 6. Configuration GitHub

Dans votre repo GitHub, ajouter ces secrets (Settings > Secrets and variables > Actions) :
- `VPS_HOST` : votre domaine ou IP
- `VPS_USERNAME` : votre utilisateur VPS
- `VPS_SSH_KEY` : la clé privée SSH générée précédemment

## 7. Commandes de Maintenance

### Docker
```bash
# Voir les conteneurs
docker ps -a

# Logs en temps réel
docker-compose -f ~/pingmaster/docker-compose.prod.yml logs -f

# Redémarrer l'API
docker-compose -f ~/pingmaster/docker-compose.prod.yml restart

# Nettoyer les ressources inutilisées
docker system prune -f

# Voir l'utilisation des ressources
docker stats
```

### Nginx
```bash
# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

### SSL/Certbot
```bash
# Vérifier les certificats
sudo certbot certificates

# Renouveler manuellement
sudo certbot renew
```

## 8. Structure des Fichiers Importante

```
~/pingmaster/
├── Dockerfile
├── docker-compose.prod.yml
├── requirements.txt
├── pyproject.toml
├── pytest.ini
└── app/
    ├── __init__.py
    ├── main.py
    └── [autres fichiers de l'application]
```

## 9. DNS Configuration

Chez votre registrar DNS, configurer :
- Type A : `pingmaster.jimmydore.fr` → IP_DU_VPS
- Type A : `jimmydore.fr` → IP_DU_VPS

## 10. Vérifications Post-Installation

```bash
# Vérifier le statut des services
systemctl status nginx
docker ps
sudo ufw status

# Tester l'API
curl -I https://pingmaster.jimmydore.fr
```

## Notes Importantes
- Toujours sauvegarder les fichiers `.env.prod` et autres fichiers de configuration sensibles
- Vérifier les permissions des fichiers et dossiers
- Garder une copie des certificats SSL si nécessaire
- Le déploiement se fait automatiquement via GitHub Actions sur push sur la branche main