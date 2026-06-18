import sys
from unittest.mock import MagicMock

# Provide a stub for the compiled Rust extension so the navyfox package can be
# imported without the native binary present (unit tests mock get_handle anyway).
sys.modules.setdefault("navyfox._navyfox", MagicMock())
