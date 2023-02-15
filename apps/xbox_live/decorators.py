from functools import wraps

from apps.xbox_live.tokens import get_oauth_token, get_user_token, get_xsts_token


def oauth_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["XboxLiveOAuthToken"] = get_oauth_token()
        return func(*args, **kwargs)

    return wrapper


def user_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["XboxLiveUserToken"] = get_user_token()
        return func(*args, **kwargs)

    return wrapper


def xsts_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["XboxLiveXSTSToken"] = get_xsts_token()
        return func(*args, **kwargs)

    return wrapper
