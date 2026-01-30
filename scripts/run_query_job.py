import json
import time

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


def base_url(store_num):
    if store_num == 1:
        return "http://localhost:5001"
    if store_num == 2:
        return "http://localhost:5002"
    raise ValueError("store_num must be 1 or 2")


def wait_for_service(url, timeout_s=60):
    deadline = time.time() + timeout_s
    last_exc = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 400, 404, 405, 415):
                return
        except Exception as e:
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


def write_entry(f, status_code, payload):
    f.write(f"{status_code}\n")
    if payload is None:
        f.write("NONE\n")
    else:
        f.write(json.dumps(payload, indent=2, ensure_ascii=False))
        f.write("\n")
    f.write(";\n")


def main():
    query_path = "query.txt"
    response_path = "response.txt"

    with open(response_path, "w", encoding="utf-8") as f:
        pass

    seed_data()

    try:
        with open(query_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return 0

    with open(response_path, "a", encoding="utf-8") as out:
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("query:"):
                # format: query: <store>,<query-string>;
                if not line.endswith(";"):
                    write_entry(out, 400, None)
                    continue

                body = line[len("query:") : -1].strip()
                if "," not in body:
                    write_entry(out, 400, None)
                    continue

                store_str, query_string = body.split(",", 1)
                store_str = store_str.strip()
                query_string = query_string.strip()
                if store_str not in ("1", "2"):
                    write_entry(out, 400, None)
                    continue

                url = f"{base_url(int(store_str))}/pet-types?{query_string}"
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        write_entry(out, r.status_code, r.json())
                    else:
                        write_entry(out, r.status_code, None)
                except Exception:
                    write_entry(out, 500, None)
                continue

            if line.startswith("purchase:"):
                # format: purchase: <json>;
                if not line.endswith(";"):
                    write_entry(out, 400, None)
                    continue

                payload_raw = line[len("purchase:") : -1].strip()
                try:
                    payload = json.loads(payload_raw)
                except Exception:
                    write_entry(out, 400, None)
                    continue

                try:
                    r = requests.post("http://localhost:5003/purchases", json=payload, timeout=10)
                    if r.status_code == 201:
                        write_entry(out, r.status_code, r.json())
                    else:
                        write_entry(out, r.status_code, None)
                except Exception:
                    write_entry(out, 500, None)
                continue

            # Unknown line
            write_entry(out, 400, None)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())