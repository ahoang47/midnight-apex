"""Decode a two-corner state token (TC3, or older TC2/TC1) to JSON, checking the CRC.
Usage: python3 tools/decode_token.py 'TC3:...'   (spec: unapproved/gordon/playtest-state-spec.md §0.5)"""
import base64, binascii, json, struct, sys
tok = sys.argv[1].strip(); p = tok.split(":")
if p[0] == "TC1":
    head, b64, crc = ("TC1" + p[1]), p[2], p[3]
elif p[0] in ("TC2", "TC3"):
    head, b64, crc = (p[0] + p[1] + p[2]), p[3], p[4]
else:
    sys.exit("unknown token version " + p[0])
payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
calc = "%04X" % binascii.crc_hqx(head.encode() + payload, 0xFFFF)
d = json.loads(payload)
def f(v): return struct.unpack("<d", struct.pack("<Q", int(v, 16)))[0] if isinstance(v, str) and v.startswith("0x") else v
if p[0] == "TC3":
    d["cum_player_value"] = f(d["cum_player"]); d["cum_opponent_value"] = f(d["cum_opponent"])
    for t in d["turns"]: t["qte_value"] = [f(v) for v in t["qte"]]
    print(f"TC3 sim {d['sim']} build {d['build']}: replay on a build with this sim pin (same build id = identical visuals too)")
elif p[0] == "TC2":
    print(f"outdated token (TC2, sim {d.get('sim', p[1])}): made before the POW/EN/HAN rename. Replay it on the build that made it. Payload follows.")
    if "cum_player" in d:
        d["cum_player_value"] = f(d["cum_player"]); d["cum_opponent_value"] = f(d["cum_opponent"])
        for t in d.get("turns", []): t["qte_value"] = [f(v) for v in t["qte"]]
else:
    print(f"outdated token (TC1, sim {p[1]}): pre-f0efecf token; replay it on its own build (repo unapproved/gordon/two-corner at 4322b31 or earlier)")
print("CRC", "OK" if calc == crc else f"MISMATCH (calc {calc}, token {crc})")
print(json.dumps(d, indent=1))
