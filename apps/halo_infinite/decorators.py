from functools import wraps

from apps.halo_infinite.tokens import (
    get_clearance_token,
    get_spartan_token,
    get_xsts_token,
)


def xsts_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["HaloInfiniteXSTSToken"] = get_xsts_token()
        return func(*args, **kwargs)

    return wrapper


def spartan_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["HaloInfiniteSpartanToken"] = get_spartan_token()
        return func(*args, **kwargs)

    return wrapper


def clearance_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["HaloInfiniteClearanceToken"] = get_clearance_token()
        return func(*args, **kwargs)

    return wrapper
