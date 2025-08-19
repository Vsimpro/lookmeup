import base62


def decode( message : str ) -> bytes:
    numbers = base62.decode( message )
    bytes   = numbers.to_bytes((numbers.bit_length() + 7) // 8, "big")
    
    return bytes


def encode( message : str ) -> str:
    _bytes = message
    if type(message) != bytes:
        _bytes   = message.encode()
    
    numbers = int.from_bytes(_bytes, "big")
    return base62.encode( numbers )
