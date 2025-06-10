import json

initial_data = {
    "pais": "",
    "PD": 0,
    "alimentos": [],
    "tablas": {}
}

with open("datos.json", "w") as f:
    json.dump(initial_data, f, indent=4)