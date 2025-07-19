import json, base62 

def serialize_into_header(name: str, size):
    data = json.dumps({"name": name, "size": size})
    encoded = base62.encodebytes(data.encode())
    return encoded

def deserialize_from_header(chunk: str):
    decoded = base62.decodebytes(chunk).decode()
    data = json.loads(decoded)
    return data