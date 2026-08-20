# repo-infra: checkmk-harness v1
class _Rec:
    def __init__(self, *a, **k):
        self.args = a
        self.kwargs = k


Plugin = PluginConfig = _Rec

OS = type("OS", (), {"LINUX": 0, "WINDOWS": 1, "SOLARIS": 2, "AIX": 3})


class _Register:
    """`register.bakery_plugin(...)` is a call, not a decorator, in this API."""

    def bakery_plugin(self, *a, **k):
        return _Rec(*a, **k)


register = _Register()
