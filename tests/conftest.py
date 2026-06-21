# navyfox._navyfox no longer exists (ctypes replaced the PyO3 extension).
# The native library loads lazily in _native/handle.py, so no stub is needed
# for unit tests — they patch get_handle() directly before any document is created.
