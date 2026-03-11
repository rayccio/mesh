
# 🛡️ ZikoraNode v2 Deployment Guide

ZikoraNode is an enterprise-grade agent orchestrator. Follow this guide to deploy your instance to a production VPS.

## 🚀 Quick Start (Automated)

The easiest way to get ZikoraNode running on a clean Ubuntu 22.04+ VPS:

```bash
# 1. Update and install Docker
sudo apt update && sudo apt install -y docker.io docker-compose

# 2. Clone the repository
git clone https://github.com/your-username/zikoranode.git
cd zikoranode

# 3. Configure your environment
echo "GEMINI_API_KEY=your_actual_key_here" > .env

# 4. Spin up the production container
sudo docker-compose up -d --build
```

---

## 🛠️ Detailed Production Setup

### 1. VPS Requirements
- **OS:** Ubuntu 22.04 LTS (Recommended)
- **RAM:** 1GB Minimum (2GB Recommended)
- **CPU:** 1 Core
- **Disk:** 10GB Free Space

### 2. Environment Configuration
The application uses **Vite** to bundle your environment variables into the static build.
1. Create a `.env` file in the root directory.
2. Add your global key: `GEMINI_API_KEY=AIza...`
3. If you want to use per-agent keys, you can define them directly within the app UI once it is running.

### 3. Domain & SSL (Recommended for Production)
To serve ZikoraNode over HTTPS (port 443), we recommend using **Caddy** or **Certbot**.

**Using Certbot with Nginx (on the host):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 4. Security Best Practices
- **Firewall:** Only keep ports 80, 443, and 22 (SSH) open.
  `sudo ufw allow 80,443,22/tcp && sudo ufw enable`
- **Secrets:** Never commit your `.env` file to version control.
- **UID Isolation:** ZikoraNode simulates UID isolation. Ensure your server user has restricted permissions.

### 5. Managing the Application
- **View Logs:** `sudo docker logs -f zikoranode_app`
- **Stop App:** `sudo docker-compose down`
- **Update App:**
  ```bash
  git pull
  sudo docker-compose up -d --build
  ```

---

## 🏗️ Folder Structure
- `/dist`: Built static assets (after `npm run build`).
- `/nginx.conf`: Directs all traffic to `index.html` (required for React Router).
- `/Dockerfile`: Orchestrates the Node-to-Nginx pipeline.

## 🆘 Troubleshooting
- **404 on Refresh:** Ensure `nginx.conf` includes the `try_files` directive.
- **API Key Not Working:** Verify that the key is correctly set in `.env` *before* running the build stage in Docker.
- **Port 80 Conflict:** Ensure no other web server (like a default Apache) is running on the host.

---
*Maintained by the Zikora Engineering Team.*
