#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import requests
# import json # Tidak dipakai langsung, requests handle JSON payload
from datetime import datetime

# --- KONFIGURASI WAJIB ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
# --- AKHIR KONFIGURASI WAJIB ---

# --- KONFIGURASI OPSIONAL ---
ATTACK_MAPPING = {
    "Ping Flood Detected": "Ping Flood (ICMP)",
    "SYN Flood Attack": "SYN Flood (TCP)",
    "UDP Flood Detected": "UDP Flood",
    "High ICMP Ping Loss": "Potensi Serangan ICMP/Network Issue",
    "Too many failed login attempts": "Brute Force Login Attempt"
    # Tambahkan mapping lain sesuai dengan nama trigger deteksi serangan Anda
}

SEVERITY_EMOJI = {
    "Not classified": "ℹ️",
    "Information": "ℹ️",
    "Warning": "⚠️",
    "Average": "🟡",
    "High": "🟠",
    "Disaster": "🛑"
}
DEFAULT_EMOJI = "🚨"
# --- AKHIR KONFIGURASI OPSIONAL ---

def send_telegram_message(chat_id, message_text):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Pesan berhasil dikirim ke Chat ID {chat_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengirim pesan ke Telegram: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error tidak terduga saat mengirim pesan: {e}", file=sys.stderr)
        return False

def format_attack_detection_message(zabbix_subject, zabbix_message):
    """
    Memformat pesan notifikasi deteksi serangan (Problem) yang akan dikirim ke Telegram.
    """
    script_process_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Waktu script ini memproses
    
    trigger_name_clean = zabbix_subject
    host_name = "N/A"
    severity_level = "Not classified"
    item_value = "N/A"
    event_id = "N/A"
    zabbix_event_time = "N/A (Pastikan {EVENT.TIME} ada di message Zabbix Action)" # Default
    zabbix_event_date = "N/A (Pastikan {EVENT.DATE} ada di message Zabbix Action)" # Default
    
    if ":" in zabbix_subject:
        parts = zabbix_subject.split(":", 1)
        if len(parts) > 1:
            trigger_name_clean = parts[1].strip()
            if " on " in trigger_name_clean:
                name_host_parts = trigger_name_clean.rsplit(" on ", 1)
                trigger_name_clean = name_host_parts[0]
                if len(name_host_parts) > 1:
                    host_name = name_host_parts[1]
            
    # Parsing informasi dari message Zabbix.
    # SANGAT PENTING: Custom message di Zabbix Action dengan Zabbix Macro.
    # Contoh baris yang bisa ada di zabbix_message (dari Zabbix Action):
    # Host: {HOST.NAME}
    # Trigger: {TRIGGER.NAME}
    # Severity: {TRIGGER.SEVERITY}
    # Value: {ITEM.LASTVALUE}
    # Event ID: {EVENT.ID}
    # Zabbix Event Time: {EVENT.TIME}
    # Zabbix Event Date: {EVENT.DATE}
    for line in zabbix_message.splitlines():
        if line.startswith("Host:"):
            host_name = line.split(":", 1)[1].strip()
        elif line.startswith("Trigger:"):
             trigger_name_from_msg = line.split(":", 1)[1].strip()
             if trigger_name_from_msg:
                 trigger_name_clean = trigger_name_from_msg
        elif line.startswith("Severity:"):
            severity_level = line.split(":", 1)[1].strip()
        elif line.startswith("Value:") or line.startswith("Item value:"): # Menyesuaikan dengan contoh ITEM.LASTVALUE
            item_value = line.split(":", 1)[1].strip()
        elif line.startswith("Event ID:"):
            event_id = line.split(":", 1)[1].strip()
        elif line.startswith("Zabbix Event Time:"): # Harus sesuai dengan yang di Zabbix Action
            zabbix_event_time = line.split(":", 1)[1].strip()
        elif line.startswith("Zabbix Event Date:"): # Harus sesuai dengan yang di Zabbix Action
            zabbix_event_date = line.split(":", 1)[1].strip()

    detected_attack_type = None
    for attack_key, attack_name in ATTACK_MAPPING.items():
        if attack_key.lower() in trigger_name_clean.lower():
            detected_attack_type = attack_name
            break
            
    emoji = SEVERITY_EMOJI.get(severity_level, DEFAULT_EMOJI)

    if detected_attack_type:
        title = f"{emoji} <b>ALARM SERANGAN TERDETEKSI: {detected_attack_type}</b> {emoji}"
    else:
        title = f"{emoji} <b>MASALAH TERDETEKSI (ZABBIX)</b> {emoji}"
        
    message_lines = [
        title,
        f"<b>Host Terkena:</b> {host_name}",
        f"<b>Nama Trigger:</b> {trigger_name_clean}",
        f"<b>Level Severity:</b> {severity_level}",
    ]
    if item_value != "N/A":
        message_lines.append(f"<b>Nilai Item Pemicu:</b> {item_value}")
    
    message_lines.extend([
        f"<b>ID Event Zabbix:</b> {event_id}",
        f"<b>Waktu Deteksi Zabbix:</b> {zabbix_event_date} {zabbix_event_time}",
        f"<b>Waktu Notifikasi Diproses:</b> {script_process_time}", # Waktu script ini jalan
        "",
        "<b>Detail Pesan dari Zabbix:</b>",
        f"<pre>{zabbix_message}</pre>" # Gunakan <pre> untuk menjaga format pesan asli
    ])
    
    return "\n".join(message_lines)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Penggunaan: script_telegram.py <ChatID> <Subject> <Message>", file=sys.stderr)
        sys.exit(1)
        
    chat_id = sys.argv[1]
    subject = sys.argv[2] # {ALERT.SUBJECT}
    message_body = sys.argv[3] # {ALERT.MESSAGE}
    
    # Hanya proses jika ini adalah notifikasi PROBLEM (serangan terdeteksi)
    # Zabbix default subject: "Problem: Trigger name"
    if subject.lower().startswith("problem:"):
        print(f"Menerima notifikasi PROBLEM: {subject}")
        formatted_message = format_attack_detection_message(subject, message_body)
        send_telegram_message(chat_id, formatted_message)
    else:
        # Jika bukan "Problem:", abaikan atau log saja (tidak mengirim ke Telegram)
        # Ini berguna jika Zabbix Action mungkin masih mengirim update atau recovery
        # tapi Anda hanya ingin notifikasi problem.
        print(f"Menerima notifikasi non-PROBLEM (Subject: {subject}). Pesan tidak dikirim ke Telegram.", file=sys.stderr)
        # Jika Anda benar-benar YAKIN Zabbix Action HANYA akan mengirim PROBLEM,
        # blok 'else' ini bisa dihilangkan dan pemanggilan format_attack_detection_message
        # bisa dilakukan tanpa pengecekan subject.
        # Namun, lebih aman untuk tetap ada filter.
        sys.exit(0) # Keluar dengan sukses karena memang tidak ada yang perlu dikirim