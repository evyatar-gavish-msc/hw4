import json
import re
import sys
import time
from pathlib import Path

import requests


PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE4 = {"type": "bulldog"}

PET1_TYPE1 = {"name": "Lander", "birthdate": "14-05-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}


def base_url(store_num: int) -> str:
    if store_num == 1:
        return "http://localhost:5001"
    if store_num == 2:
        return "http://localhost:5002"
    raise ValueError("store_num must be 1 or 2")


def wait_for_service(url: str, timeout_s: int = 60) -> None:
    deadline = time.time() + timeout_s
    last_exc = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 400, 404, 405, 415):
                return
        except Exception as e:  # noqa: BLE001
            last_exc = e
        time.sleep(1)
    raise RuntimeError(f"Service not reachable at {url} (last_exc={last_exc})")


def seed_data() -> None:
    wait_for_service(f"{base_url(1)}/pet-types")
    wait_for_service(f"{base_url(2)}/pet-types")

    # create pet types (same as in pytest steps 1-2)
    r1 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE1, timeout=10)
    r2 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE2, timeout=10)
    r3 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE3, timeout=10)

    r4 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE1, timeout=10)
    r5 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE2, timeout=10)
    r6 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE4, timeout=10)

    for r in (r1, r2, r3, r4, r5, r6):
        if r.status_code != 201:
            raise RuntimeError(f"Seed failed creating pet-type: {r.status_code} {r.text}")

    id_1 = r1.json()["id"]
    id_2 = r2.json()["id"]
    id_3 = r3.json()["id"]
    id_4 = r4.json()["id"]
    id_5 = r5.json()["id"]
    id_6 = r6.json()["id"]

    # create pets
    posts = [
        (1, id_1, PET1_TYPE1),
        (1, id_1, PET2_TYPE1),
        (1, id_3, PET5_TYPE3),
        (1, id_3, PET6_TYPE3),
        (2, id_4, PET3_TYPE1),
        (2, id_5, PET4_TYPE2),
        (2, id_6, PET7_TYPE4),
        (2, id_6, PET8_TYPE4),
    ]
    for store, pid, payload in posts:
        r = requests.post(f"{base_url(store)}/pet-types/{pid}/pets", json=payload, timeout=10)
        if r.status_code != 201:
            raise RuntimeError(f"Seed failed creating pet: {r.status_code} {r.text}")


QUERY_RE = re.compile(r"^\s*query:\s*([12])\s*,\s*([^;]+)\s*;\s*$")
PURCHASE_RE = re.compile(r"^\s*purchase:\s*(\{.*\})\s*;\s*$")


def write_entry(out: Path, status_code: int, payload) -> None:
    with out.open("a", encoding="utf-8") as f:
        f.write(f"{status_code}\n")
        if payload is None:
            f.write("NONE\n")
        else:
            f.write(json.dumps(payload, indent=2, ensure_ascii=False))
            f.write("\n")
        f.write(";\n")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    query_path = repo_root / "query.txt"
    response_path = repo_root / "response.txt"
    response_path.write_text("", encoding="utf-8")

    seed_data()

    if not query_path.exists():
        return 0

    for line in query_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        m = QUERY_RE.match(line)
        if m:
            store_num = int(m.group(1))
            query_string = m.group(2).strip()
            url = f"{base_url(store_num)}/pet-types?{query_string}"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    write_entry(response_path, r.status_code, r.json())
                else:
                    write_entry(response_path, r.status_code, None)
            except Exception:
                write_entry(response_path, 500, None)
            continue

        m = PURCHASE_RE.match(line)
        if m:
            payload_raw = m.group(1)
            try:
                payload = json.loads(payload_raw)
            except Exception:  # noqa: BLE001
                write_entry(response_path, 400, None)
                continue

            try:
                r = requests.post("http://localhost:5003/purchases", json=payload, timeout=10)
                if r.status_code == 201:
                    write_entry(response_path, r.status_code, r.json())
                else:
                    write_entry(response_path, r.status_code, None)
            except Exception:  # noqa: BLE001
                write_entry(response_path, 500, None)
            continue

        # Unknown line format
        write_entry(response_path, 400, None)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())