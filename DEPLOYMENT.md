# Deploying Leave_TKE to Another Server on the Local Network

This guide explains how to take this project from your development machine and deploy it onto a **separate Linux server** (e.g., Ubuntu server, Debian, Raspberry Pi, or another PC on your LAN) running **Gunicorn** and **systemd**.

---

## Architecture on the Server

```
Any Device on LAN ---> http://<SERVER-IP>:8000 ---> Gunicorn (WSGI) ---> Flask (app.py) ---> SQLite (instance/leave_db.db)
                                                      ^ Managed by systemd
```

---

## Phase 1: On Your Development Machine (Prepare & Send Code)

### Step 1: Commit and push your changes to Git (recommended)
Commit the deployment files created on your local machine:
```bash
git add .gitignore requirements.txt gunicorn.conf.py deploy/ .env.example DEPLOYMENT.md app.py
git commit -m "Add production gunicorn configuration and deployment setup"
git push origin main
```

*(Alternative: If you do not use Git remotes, copy the folder to the server with `scp`:)*
```bash
scp -r ~/Leave_TKE_v1 username@<SERVER-IP>:~/Leave_TKE_v1
```

---

## Phase 2: On the Target Server (Setup & Run)

SSH into your target server:
```bash
ssh username@<SERVER-IP>
```

### Step 1: Install Python prerequisites
Ensure Python 3 and the `venv` module are installed on the server:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### Step 2: Clone or navigate to the project
If using Git:
```bash
git clone <YOUR-REPO-URL> ~/Leave_TKE_v1
cd ~/Leave_TKE_v1
```
*(If you used `scp`, just `cd ~/Leave_TKE_v1`)*

### Step 3: Create a clean virtual environment and install packages
Do not copy your local virtualenv or conda environment; create a fresh one on the server:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the server environment (.env)
Generate a unique secret key for this server:
```bash
cp .env.example .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env
chmod 600 .env
```

### Step 5: Initialize the database and create a manager user
Run `create_user.py` inside the virtual environment:
```bash
python create_user.py
```
*(Follow the prompt to enter the manager username and password)*

### Step 6: Test Gunicorn manually
Verify everything works before setting up background services:
```bash
set -a; source .env; set +a
gunicorn app:app
```
Test from another machine on your LAN by visiting `http://<SERVER-IP>:8000`.
If it loads, press `Ctrl+C` to stop the manual test.

---

## Phase 3: Run as a Background Service (systemd)

To make sure the server restarts the app on reboot and keeps it running:

### Step 1: Customize the service file
The service file is located at `deploy/leave_app.service`.
Update `YOUR_USERNAME` with your actual Linux username on the server (run `whoami` to check):
```bash
sed -i "s/YOUR_USERNAME/$(whoami)/g" deploy/leave_app.service
```

### Step 2: Register and enable the systemd service
```bash
sudo cp deploy/leave_app.service /etc/systemd/system/leave_app.service
sudo systemctl daemon-reload
sudo systemctl enable --now leave_app
```

Check that the service is active and running:
```bash
sudo systemctl status leave_app
```

### Step 3: Open the firewall on the server (if active)
```bash
sudo ufw allow 8000/tcp
```

---

## Phase 4: Accessing from Any Device

Find the server's LAN IP address:
```bash
hostname -I
```
*(Look for an address like `192.168.1.X` or `10.X.X.X`)*

From any PC, phone, or laptop on the same Wi-Fi/local network, open your browser and go to:
```
http://<SERVER-IP>:8000
```

---

## Managing the Service in Production

- **Restart the app** (e.g. after pulling code updates):
  ```bash
  sudo systemctl restart leave_app
  ```
- **View live server logs / access logs**:
  ```bash
  journalctl -u leave_app -f
  ```
- **Stop the app**:
  ```bash
  sudo systemctl stop leave_app
  ```
- **Backup the database**:
  ```bash
  cp ~/Leave_TKE_v1/instance/leave_db.db ~/leave_backup_$(date +%F).db
  ```
  