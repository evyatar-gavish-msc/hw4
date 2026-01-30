import time

import requests


PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE1_VAL = {
    "type": "Golden Retriever",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": [],
    "lifespan": 12,
}

PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE2_VAL = {
    "type": "Australian Shepherd",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Loyal", "outgoing", "and", "friendly"],
    "lifespan": 15,
}

PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE3_VAL = {
    "type": "Abyssinian",
    "family": "Felidae",
    "genus": "Felis",
    "attributes": ["Intelligent", "and", "curious"],
    "lifespan": 13,
}

PET_TYPE4 = {"type": "bulldog"}
PET_TYPE4_VAL = {
    "type": "bulldog",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Gentle", "calm", "and", "affectionate"],
    "lifespan": None,
}

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


def test_assn4_flow():
    # make sure both stores are up
    wait_for_service(f"{base_url(1)}/pet-types")
    wait_for_service(f"{base_url(2)}/pet-types")

    # create pet types in both stores
    r1 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE1, timeout=10)
    r2 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE2, timeout=10)
    r3 = requests.post(f"{base_url(1)}/pet-types", json=PET_TYPE3, timeout=10)

    r4 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE1, timeout=10)
    r5 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE2, timeout=10)
    r6 = requests.post(f"{base_url(2)}/pet-types", json=PET_TYPE4, timeout=10)

    for r in (r1, r2, r3, r4, r5, r6):
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"

    p1 = r1.json()
    p2 = r2.json()
    p3 = r3.json()
    p4 = r4.json()
    p5 = r5.json()
    p6 = r6.json()

    ids_store1 = [p1["id"], p2["id"], p3["id"]]
    ids_store2 = [p4["id"], p5["id"], p6["id"]]
    assert len(set(ids_store1)) == 3
    assert len(set(ids_store2)) == 3

    # family and genus must match the expected values
    assert p1["family"] == PET_TYPE1_VAL["family"] and p1["genus"] == PET_TYPE1_VAL["genus"]
    assert p2["family"] == PET_TYPE2_VAL["family"] and p2["genus"] == PET_TYPE2_VAL["genus"]
    assert p3["family"] == PET_TYPE3_VAL["family"] and p3["genus"] == PET_TYPE3_VAL["genus"]
    assert p4["family"] == PET_TYPE1_VAL["family"] and p4["genus"] == PET_TYPE1_VAL["genus"]
    assert p5["family"] == PET_TYPE2_VAL["family"] and p5["genus"] == PET_TYPE2_VAL["genus"]
    assert p6["family"] == PET_TYPE4_VAL["family"] and p6["genus"] == PET_TYPE4_VAL["genus"]

    id_1, id_2, id_3 = ids_store1
    id_4, id_5, id_6 = ids_store2

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
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"

    # GET /pet-types/{id_2} from store #1 must match PET_TYPE2_VAL fields
    r = requests.get(f"{base_url(1)}/pet-types/{id_2}", timeout=10)
    assert r.status_code == 200
    body = r.json()
    for k, v in PET_TYPE2_VAL.items():
        assert body.get(k) == v, f"Field mismatch for {k}: expected {v}, got {body.get(k)}"

    # GET /pet-types/{id_6}/pets from store #2 contains pets with expected fields
    r = requests.get(f"{base_url(2)}/pet-types/{id_6}/pets", timeout=10)
    assert r.status_code == 200
    pets = r.json()
    assert isinstance(pets, list)

    by_name = {p.get("name"): p for p in pets}
    assert PET7_TYPE4["name"] in by_name
    assert PET8_TYPE4["name"] in by_name
    assert by_name[PET7_TYPE4["name"]].get("birthdate") == PET7_TYPE4["birthdate"]
    assert by_name[PET8_TYPE4["name"]].get("birthdate") == PET8_TYPE4["birthdate"]