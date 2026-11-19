"""Shim: the approved tone presets moved to art/mood/tones/tones.py (Austin 2026-11-19).
Keeps the remaining unapproved tones study importing TONES / hx from this path."""
import importlib.util
import os

_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', 'art', 'mood', 'tones', 'tones.py',
))
_spec = importlib.util.spec_from_file_location('_approved_tones', _PATH)
if _spec is None or _spec.loader is None:
    raise ImportError('approved tones.py not found at %s' % _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
TONES = _mod.TONES
hx = _mod.hx
