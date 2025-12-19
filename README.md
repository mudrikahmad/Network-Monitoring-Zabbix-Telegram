# Zabbix to Telegram Real-Time Alert System 🚨

This repository contains a custom **Python Middleware Script** to integrate **Zabbix 6.0 LTS** with **Telegram Bot API**. It enables real-time network attack detection notifications (DDoS/Brute Force) to be sent directly to the administrator's smartphone.

## 📸 Proof of Concept

> _Note: Upload screenshot of the Telegram notification here._ > ![Telegram Notification Example](https://via.placeholder.com/600x400?text=Upload+Your+Screenshot+Here)

## 🛠️ Features

- **Custom Alert Mapping:** Automatically maps Zabbix triggers (e.g., "SYN Flood") to readable attack names.
- **Severity Emojis:** Adds visual indicators (🚨, ⚠️, ℹ️) based on problem severity.
- **Detailed Reporting:** Sends Hostname, Trigger Name, Event ID, and Item Values in a single chat bubble.

## 📋 Prerequisites

- OS: Ubuntu Server 20.04/22.04
- Zabbix Server 6.0 LTS
- Python 3 & PIP
- Python Library: `requests`

```bash
sudo apt install python3-requests
# or
pip3 install requests
```

## ⚙️ Installation & Configuration

1. Script Setup
   Place the zabbix_telegram_alert.py script in the Zabbix AlertScripts directory:

```bash
cd /usr/lib/zabbix/alertscripts/
sudo nano zabbix_telegram_alert.py

# Paste the python code inside and save (Ctrl+O, Enter, Ctrl+X)

sudo chmod +x zabbix_telegram_alert.py
```

2. Zabbix GUI Configuration

**A. Create Media Type**
Go to **Administration > Media types > Create media type**:

- **Name:** Telegram Notif
- **Type:** Script
- **Script name:** `zabbix_telegram_alert.py`
- **Script parameters:**
  - `{ALERT.SENDTO}`
  - `{ALERT.SUBJECT}`
  - `{ALERT.MESSAGE}`

**B. Configure User Media**
Go to **Administration > Users**:

- Select the **Admin** user.
- Go to **Media** tab > **Add**.
- **Type:** Telegram Notif.
- **Send to:** `YOUR_TELEGRAM_CHAT_ID` (e.g., 123456789).

3. Action Template (Crucial!)
   To make sure the script parses the data correctly, configure the Trigger Action message as follows:

Go to Configuration > Actions > Trigger actions > Create action. In the Operations tab, use this template:

Subject:

Problem: {TRIGGER.NAME} on {HOST.NAME}

Message:

```text
Status: {TRIGGER.STATUS}
Host: {HOST.NAME}
Trigger: {TRIGGER.NAME}
Severity: {TRIGGER.SEVERITY}
Event ID: {EVENT.ID}
Zabbix Event Date: {EVENT.DATE}
Zabbix Event Time: {EVENT.TIME}
Item Pemicu: {ITEM.NAME1} ({ITEM.KEY1})
Nilai Item: {ITEM.LASTVALUE1}
Detail Masalah: {EVENT.OPDATA}
Lihat Event: {TRIGGER.URL}
```

## 🚀 Usage

Create a dummy trigger (e.g., High CPU Load or SYN Flood simulation).
Wait for the Zabbix "PROBLEM" status.
You will receive an instant notification on Telegram.
