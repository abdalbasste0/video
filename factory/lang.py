"""Video language (channel.language in settings): "ar" (right-to-left) or "en" (left-to-right)."""

_state = {"code": "ar"}

TEXT = {
    "chapter": {"ar": "الفصل {n}", "en": "Chapter {n}"},
    "subscribe": {"ar": "اشترك", "en": "Subscribe"},
    "subscribed": {"ar": "مشترك", "en": "Subscribed"},
    "like": {"ar": "لايك", "en": "Like"},
    "comments": {"ar": "قولنا في الكومنتات …", "en": "Tell us in the comments …"},
}

NAMES = {"ar": "Arabic (العربية)", "en": "English"}


def set_language(code):
    _state["code"] = code if code in NAMES else "ar"


def code():
    return _state["code"]


def rtl():
    return _state["code"] == "ar"


def t(key, **kw):
    return TEXT[key].get(_state["code"], TEXT[key]["ar"]).format(**kw)
