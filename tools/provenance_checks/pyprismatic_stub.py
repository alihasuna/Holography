# Minimal stand-in so that `import pyprismatic` succeeds for API inspection ONLY.
# No simulation is run. Records attribute assignments.
class Metadata:
    def __init__(self, **kw):
        object.__setattr__(self, "_rec", {})
        for k, v in kw.items(): setattr(self, k, v)
    def __setattr__(self, k, v):
        self._rec[k] = v
        object.__setattr__(self, k, v)
    def go(self): raise RuntimeError("stub pyprismatic: go() not implemented")
