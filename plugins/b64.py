import base64


def decode( message : str ) -> str:
    padding = "=" * (-len(message) % 4)
    return base64.urlsafe_b64decode( message + padding ).decode()


def encode( message : str ) -> str:
    return base64.urlsafe_b64encode( message ).rstrip( b"=" ).decode()
