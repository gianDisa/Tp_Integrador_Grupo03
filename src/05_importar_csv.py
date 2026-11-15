import csv
import getpass
import requests
from tabulate import tabulate

BASE_URL = "http://localhost:58000/api/v1"


def obtener_ticket(username: str, password: str) -> str:
    url = f"{BASE_URL}/ticket"
    headers = {"Content-Type": "application/json"}
    payload = {"username": username, "password": password}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()["response"]["serviceTicket"]


def consultar_endpoint(ruta: str, ticket: str) -> list:
    url = f"{BASE_URL}/{ruta}"
    headers = {
        "X-Auth-Token": ticket,
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("response", [])


def main():
    print("=== Exportador de Inventario de Red y Hosts (Grupo 3) ===")
    user_input = input("Usuario del Network Controller [cisco]: ").strip()
    username = user_input if user_input else "cisco"
    password = getpass.getpass("Contraseña del Network Controller: ")

    try:
        ticket = obtener_ticket(username, password)
        dispositivos = consultar_endpoint("network-device", ticket)
        hosts = consultar_endpoint("host", ticket)
    except requests.exceptions.RequestException as exc:
        print(f"\n[ERROR] No se pudo conectar con el Network Controller: {exc}")
        return

    filas = []

    for dev in dispositivos:
        filas.append({
            "Categoria": "Dispositivo de Red",
            "Nombre / Hostname": dev.get("hostname") or "Sin nombre",
            "Tipo / Plataforma": dev.get("type") or dev.get("platformId") or "N/A",
            "Direccion IP": dev.get("managementIpAddress") or "N/A",
            "Direccion MAC": dev.get("macAddress") or "N/A",
            "Estado / Enlace": dev.get("collectionStatus") or "N/A",
        })

    for host in hosts:
        filas.append({
            "Categoria": "Host Final",
            "Nombre / Hostname": host.get("hostName") or host.get("hostType") or "Host",
            "Tipo / Plataforma": host.get("hostType") or "End Device",
            "Direccion IP": host.get("hostIp") or "N/A",
            "Direccion MAC": host.get("hostMac") or "N/A",
            "Estado / Enlace": f"Conectado a {host.get('connectedNetworkDeviceName', 'N/A')} ({host.get('connectedInterfaceName', 'N/A')})",
        })

    if not filas:
        print("\nNo se encontraron dispositivos ni hosts en el controlador.")
        return

    print("\n" + tabulate(filas, headers="keys", tablefmt="grid"))

    archivo_csv = "inventario_red.csv"
    campos = [
        "Categoria",
        "Nombre / Hostname",
        "Tipo / Plataforma",
        "Direccion IP",
        "Direccion MAC",
        "Estado / Enlace",
    ]
    with open(archivo_csv, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        writer.writeheader()
        writer.writerows(filas)

    print(f"\n[OK] Inventario exportado correctamente a '{archivo_csv}' ({len(filas)} registros).")


if __name__ == "__main__":
    main()