"""Decode a two-corner state token (TC2, or TC1 from builds before the f0efecf re-pin) to JSON, checking the CRC.
Usage: python3 tools/decode_token.py 'TC2:...'   (spec: unapproved/gordon/playtest-state-spec.md §0.5)"""
import base64, binascii, json, struct, sys
tok = sys.argv[1].strip(); p = tok.split(":")
if p[0] == "TC1":
    head, b64, crc = ("TC1" + p[1]), p[2], p[3]
elif p[0] == "TC2":
    head, b64, crc = ("TC2" + p[1] + p[2]), p[3], p[4]
else:
    sys.exit("unknown token version " + p[0])
payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
calc = "%04X" % binascii.crc_hqx(head.encode() + payload, 0xFFFF)
d = json.loads(payload)
def f(v): return struct.unpack("<d", struct.pack("<Q", int(v, 16)))[0] if isinstance(v, str) and v.startswith("0x") else v
if p[0] == "TC2":
    d["cum_player_value"] = f(d["cum_player"]); d["cum_opponent_value"] = f(d["cum_opponent"])
    for t in d["turns"]: t["qte_value"] = [f(v) for v in t["qte"]]
    print(f"TC2 sim {d['sim']} build {d['build']}: replay on a build with this sim pin (same build id = identical visuals too)")
else:
    print(f"TC1 sim {p[1]}: pre-f0efecf token; replay it on its own build (repo unapproved/gordon/two-corner at 4322b31 or earlier)")
print("CRC", "OK" if calc == crc else f"MISMATCH (calc {calc}, token {crc})")
print(json.dumps(d, indent=1))
