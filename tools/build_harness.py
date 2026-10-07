#!/usr/bin/env python3
"""Générateur du faisceau moteur M50B25 VANOS Turbo — MaxxECU RACE.

Lit la définition YAML du faisceau, applique un contrôle de règles
électriques (ERC), calcule les longueurs de coupe et les torons, puis
produit la page interactive, la liste de coupe, le brochage ECU, la
nomenclature et le rapport de vérification.

Usage : python3 tools/build_harness.py [harness.yaml] [--out docs]
"""
import argparse
import csv
import heapq
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "harness" / "m50b25_vanos_turbo.yaml"
TEMPLATE = Path(__file__).resolve().parent / "template.html"

# Classe électrique des broches ECU selon leur type
ECU_KIND_CLASS = {
    "ecu_12v": "PWR12",
    "ecu_gnd": "GND_PWR",
    "sensor_gnd": "GND_SENS",
    "vr_gnd": "GND_VR",
    "knock_gnd": "GND_KNOCK",
    "shield_gnd": "GND_SHIELD",
    "v5": "V5",
}
ECU_OUTPUT_KINDS = {"ign", "inj", "gpo", "gpo_hs", "motor"}
CLASS_LABEL = {
    "PWR12": "+12 V",
    "V5": "+5 V capteurs",
    "V15": "+15 contact",
    "GND_PWR": "masse puissance",
    "GND_SENS": "Sensor GND",
    "GND_VR": "VR GND",
    "GND_KNOCK": "Knock GND",
    "GND_SHIELD": "blindage",
}
# Gaine thermo DR-25 (Ø intérieur fourni / rétreint, mm)
SLEEVES = [(3.2, 1.6), (4.8, 2.4), (6.4, 3.2), (9.5, 4.8), (12.7, 6.4),
           (19.1, 9.5), (25.4, 12.7), (38.1, 19.1), (50.8, 25.4)]


def natural_key(text):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(text))]


def fmt_mm2(value):
    return f"{value:g}".replace(".", ",")


class Harness:
    def __init__(self, data):
        self.d = data
        self.rules = data["wire_rules"]
        self.errors = []
        self.warnings = []
        self.infos = []
        self.endpoints = {}
        self.owners = {}
        self._load_owners()
        self._load_wires()
        self._build_topology()
        self._build_nets()

    # ------------------------------------------------------------------ model
    def _add_owner(self, oid, **info):
        if oid in self.owners:
            self.errors.append(f"Identifiant en double : {oid}")
        self.owners[oid] = info

    def _add_endpoint(self, eid, **info):
        self.endpoints[eid] = info

    def _load_owners(self):
        ecu = self.d["ecu"]
        for cid, conn in ecu["connectors"].items():
            self._add_owner(cid, cat="ecu", label=f"{ecu['name']} — {cid}",
                            title=conn["title"], node=ecu["node"], system="REF")
            for pin, p in conn["pins"].items():
                self._add_endpoint(
                    f"{cid}.{pin}", owner=cid, pin=pin, cat="ecu", fn=p["fn"],
                    kind=p["kind"], max_a=p.get("max_a"),
                    cls=ECU_KIND_CLASS.get(p["kind"]))

        for cid, c in self.d["components"].items():
            ctype = c.get("type", "")
            cat = "fuse" if ctype == "fuse" else "relay" if ctype == "relay" else (
                "inline" if c.get("inline") else "comp")
            self._add_owner(cid, cat=cat, label=c["label"], ref=c.get("ref", ""),
                            type=ctype, connector=c.get("connector", ""),
                            node=c["node"], system=c.get("system", "REF"),
                            harness=c.get("harness"), notes=c.get("notes", ""),
                            verify=c.get("verify", ""), rating_a=c.get("rating_a"),
                            load_a=c.get("load_a"), r_ohm=c.get("r_ohm"),
                            supply5_ma=c.get("supply5_ma"),
                            external=bool(c.get("external")),
                            optional=bool(c.get("optional")))
            for pin, p in c["pins"].items():
                cls = p.get("cls")
                if cat == "fuse" or (cat == "relay" and str(pin) in ("30", "87")):
                    cls = "PWR12"
                self._add_endpoint(f"{cid}.{pin}", owner=cid, pin=str(pin), cat=cat,
                                   fn=p["fn"], cls=cls, nc=bool(p.get("nc")),
                                   supply=bool(p.get("supply")))

        for gid, g in self.d["grounds"].items():
            self._add_owner(gid, cat="ground", label=g["label"], node=g["node"],
                            system="GND", ground_kind=g["kind"],
                            harness=g.get("harness"), notes=g.get("notes", ""))
            self._add_endpoint(gid, owner=gid, pin="", cat="ground", fn=g["label"],
                               cls="GND_PWR")

        for sid, s in self.d["splices"].items():
            self._add_owner(sid, cat="splice", label=s["label"], node=s["node"],
                            system="REF", busbar=bool(s.get("busbar")))
            self._add_endpoint(sid, owner=sid, pin="", cat="splice", fn=s["label"],
                               cls=s.get("cls"))

        ecu_node = self.d["ecu"]["node"]
        for cid, c in self.d["cables"].items():
            if c.get("shield"):
                self._add_owner(f"{cid}.SH", cat="shield", label=f"Blindage {cid}",
                                node=ecu_node, system="REF", cable=cid)
                self._add_endpoint(f"{cid}.SH", owner=f"{cid}.SH", pin="", cat="shield",
                                   fn=f"Blindage {c['label']}", cls="GND_SHIELD")

    def _load_wires(self):
        self.wires = []
        counters = defaultdict(int)
        for idx, w in enumerate(self.d["wires"]):
            for end in ("from", "to"):
                if w[end] not in self.endpoints:
                    self.errors.append(f"Fil n°{idx + 1} : extrémité inconnue « {w[end]} »")
            sheet = w["sheet"]
            if sheet not in self.d["sheets"]:
                self.errors.append(f"Fil n°{idx + 1} : planche inconnue « {sheet} »")
            internal = bool(w.get("internal"))
            drain = bool(w.get("drain"))
            if internal:
                counters["BUS"] += 1
                wid = f"BUS-{counters['BUS']:02d}"
            elif drain:
                counters["SH"] += 1
                wid = f"SH-{counters['SH']:02d}"
            else:
                counters[sheet] += 1
                wid = f"{sheet}-{counters[sheet]:02d}"
            cable = w.get("cable")
            if cable and cable not in self.d["cables"]:
                self.errors.append(f"{wid} : câble inconnu « {cable} »")
            if not internal and not drain:
                if "mm2" not in w or "color" not in w:
                    self.errors.append(f"{wid} : section ou couleur manquante")
                for part in str(w.get("color", "")).split("/"):
                    if part and part not in self.d["colors"]:
                        self.errors.append(f"{wid} : couleur inconnue « {part} »")
            self.wires.append({
                "id": wid, "from": w["from"], "to": w["to"], "sheet": sheet,
                "mm2": w.get("mm2"), "color": w.get("color"), "cable": cable,
                "harness": w.get("harness") or self._infer_harness(w),
                "internal": internal, "drain": drain, "note": w.get("note", ""),
            })

    def _infer_harness(self, w):
        harn = {self.owners.get(self.endpoints.get(w[e], {}).get("owner"), {}).get("harness")
                for e in ("from", "to")}
        harn.discard(None)
        if "CAB" in harn:
            return "CAB"
        if "CHS" in harn:
            return "CHS"
        return "ENG"

    # ------------------------------------------------------------- topology
    def _build_topology(self):
        topo = self.d["topology"]
        self.nodes = topo["nodes"]
        self.adj = defaultdict(list)
        self.segments = []
        for a, b, length in topo["segments"]:
            for n in (a, b):
                if n not in self.nodes:
                    self.errors.append(f"Topologie : nœud inconnu « {n} »")
            sid = f"{a}~{b}"
            self.segments.append({"id": sid, "a": a, "b": b, "length": float(length)})
            self.adj[a].append((b, float(length), sid))
            self.adj[b].append((a, float(length), sid))
        for oid, o in self.owners.items():
            if o["node"] not in self.nodes:
                self.errors.append(f"{oid} : nœud de topologie inconnu « {o['node']} »")
        self._paths = {}

    def _dijkstra(self, src):
        if src in self._paths:
            return self._paths[src]
        dist = {src: 0.0}
        prev = {}
        heap = [(0.0, src)]
        while heap:
            d, n = heapq.heappop(heap)
            if d > dist.get(n, math.inf):
                continue
            for m, length, sid in self.adj[n]:
                nd = d + length
                if nd < dist.get(m, math.inf):
                    dist[m] = nd
                    prev[m] = (n, sid)
                    heapq.heappush(heap, (nd, m))
        self._paths[src] = (dist, prev)
        return dist, prev

    def path(self, a, b):
        dist, prev = self._dijkstra(a)
        if b not in dist:
            return math.inf, []
        segs = []
        n = b
        while n != a:
            n, sid = prev[n]
            segs.append(sid)
        return dist[b], list(reversed(segs))

    # ------------------------------------------------------------------ nets
    def _build_nets(self):
        parent = {e: e for e in self.endpoints}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for w in self.wires:
            if w["from"] in parent and w["to"] in parent:
                ra, rb = find(w["from"]), find(w["to"])
                if ra != rb:
                    parent[ra] = rb
        groups = defaultdict(list)
        connected = set()
        for w in self.wires:
            connected.update((w["from"], w["to"]))
        for e in self.endpoints:
            if e in connected:
                groups[find(e)].append(e)
        self.nets = []
        self.net_of = {}
        for members in groups.values():
            members.sort(key=natural_key)
            net = {"id": f"N{len(self.nets) + 1:03d}", "members": members,
                   "name": self._net_name(members)}
            self.nets.append(net)
            for m in members:
                self.net_of[m] = net["id"]
        self.nets.sort(key=lambda n: natural_key(n["name"]))
        self.net_by_id = {n["id"]: n for n in self.nets}
        for w in self.wires:
            w["net"] = self.net_of.get(w["from"])

    def _net_name(self, members):
        def first(cat):
            return next((m for m in members if self.endpoints[m]["cat"] == cat), None)

        ecu = first("ecu")
        if ecu:
            return f"{ecu} {self.endpoints[ecu]['fn']}"
        for cat in ("splice", "ground"):
            m = first(cat)
            if m:
                return self.endpoints[m]["fn"]
        fuse = next((m for m in members if self.endpoints[m]["cat"] == "fuse"
                     and self.endpoints[m]["pin"] == "2"), None)
        if fuse:
            return f"Sortie {fuse.split('.')[0]}"
        relay = next((m for m in members if self.endpoints[m]["cat"] == "relay"), None)
        if relay:
            return f"{relay} {self.endpoints[relay]['fn']}"
        return members[0]

    # ------------------------------------------------------------------ ERC
    def is_source(self, eid):
        e = self.endpoints[eid]
        if e["cat"] == "fuse" and e["pin"] == "2":
            return True
        if e["cat"] == "relay" and e["pin"] == "87":
            return True
        if e["cat"] == "ecu" and e["kind"] in ("v5",):
            return True
        return e["owner"] in ("BATT", "KEY")

    def erc(self):
        for net in self.nets:
            classes = defaultdict(list)
            ecu_pins = []
            sources = []
            for m in net["members"]:
                e = self.endpoints[m]
                if e.get("cls"):
                    classes[e["cls"]].append(m)
                if e["cat"] == "ecu":
                    ecu_pins.append(m)
                if self.is_source(m):
                    sources.append(m)
            if len(classes) > 1:
                detail = " ; ".join(f"{CLASS_LABEL[c]} ({', '.join(v)})" for c, v in classes.items())
                self.errors.append(f"Réseau « {net['name']} » : classes incompatibles — {detail}")
            if len(ecu_pins) > 1 and any(not self.endpoints[p].get("cls") for p in ecu_pins):
                self.errors.append(f"Réseau « {net['name']} » : plusieurs broches ECU reliées ({', '.join(ecu_pins)})")
            signal_ecu = [p for p in ecu_pins if not self.endpoints[p].get("cls")]
            if signal_ecu and classes:
                self.errors.append(f"Réseau « {net['name']} » : signal ECU {signal_ecu[0]} relié à "
                                   f"{', '.join(CLASS_LABEL[c] for c in classes)}")
            if len(sources) > 1:
                self.errors.append(f"Réseau « {net['name']} » : plusieurs sources d'alimentation ({', '.join(sources)})")
            if "GND_SENS" in classes or "GND_VR" in classes or "GND_KNOCK" in classes or "GND_SHIELD" in classes:
                grounds = [m for m in net["members"] if self.endpoints[m]["cat"] == "ground"]
                if grounds:
                    self.errors.append(f"Réseau « {net['name']} » : masse de référence ECU reliée à {grounds[0]}")

        # Utilisation des broches
        uses = defaultdict(list)
        for w in self.wires:
            for end in ("from", "to"):
                uses[w[end]].append(w["id"])
        for eid, e in self.endpoints.items():
            n = len(uses.get(eid, []))
            if e["cat"] == "ecu" and n > 1:
                self.errors.append(f"Broche ECU {eid} utilisée par {n} fils ({', '.join(uses[eid])}) — passer par une épissure")
            if e["cat"] in ("comp", "fuse", "relay", "inline") and n == 0 and not e.get("nc"):
                opt = self.owners[e["owner"]].get("optional")
                (self.infos if opt else self.warnings).append(f"Broche {eid} ({e['fn']}) non raccordée")
            if e["cat"] == "comp" and n > 1 and not self.owners[e["owner"]].get("external"):
                self.warnings.append(f"Broche {eid} reçoit {n} fils : prévoir une épissure plutôt qu'un double sertissage")
            if e["cat"] == "splice" and n < 2:
                self.errors.append(f"Épissure {eid} avec moins de 2 fils")
            if e["cat"] == "ground" and n == 0:
                self.warnings.append(f"Point de masse {eid} inutilisé")
            if e["cat"] == "inline" and n not in (0, 2):
                self.warnings.append(f"Connecteur traversant {eid} : {n} fil(s) (attendu 2)")

        # Épissures : capacité physique
        for sid in self.d["splices"]:
            ws = [w for w in self.wires if sid in (w["from"], w["to"]) and not w["internal"]]
            total = sum(w["mm2"] or 0 for w in ws)
            if len(ws) > 8 or total > 10:
                self.warnings.append(f"Épissure {sid} : {len(ws)} fils / {fmt_mm2(total)} mm² — scinder en deux")
            self.owners[sid]["wires"] = len(ws)
            self.owners[sid]["csa"] = round(total, 2)

        self._fuse_checks()
        self._output_checks()

    def _min_mm2(self, rating):
        table = sorted((float(k), float(v)) for k, v in self.rules["fuse_min_mm2"].items())
        for amps, mm2 in table:
            if rating <= amps:
                return mm2
        return table[-1][1]

    def _members_of(self, eid):
        net = self.net_of.get(eid)
        return self.net_by_id[net]["members"] if net else []

    def _downstream(self, eid, seen=None):
        """Réseaux alimentés depuis la broche eid (traverse les contacts de relais)."""
        seen = seen if seen is not None else set()
        net = self.net_of.get(eid)
        if not net or net in seen:
            return [], []
        seen.add(net)
        nets = [net]
        fuses = []
        for m in self.net_by_id[net]["members"]:
            e = self.endpoints[m]
            if e["cat"] == "relay" and e["pin"] == "30":
                sub_n, sub_f = self._downstream(f"{e['owner']}.87", seen)
                nets += sub_n
                fuses += sub_f
            if e["cat"] == "fuse" and e["pin"] == "1" and m != eid:
                fuses.append(e["owner"])
        return nets, fuses

    def load_of_owner(self, oid, worst=True):
        o = self.owners[oid]
        if oid == "ECU":
            return self.d["ecu"].get("load_a", 0)
        if o.get("load_a") is not None:
            return o["load_a"]
        if o.get("r_ohm"):
            r = o["r_ohm"]
            rmin = min(r) if isinstance(r, list) else r
            rmax = max(r) if isinstance(r, list) else r
            v = self.rules["supply_v"]
            return v / rmin if worst else v / rmax
        return 0.0

    def fuse_load(self, fid, _seen=None):
        _seen = _seen if _seen is not None else set()
        if fid in _seen:
            return 0.0, []
        _seen.add(fid)
        nets, fuses = self._downstream(f"{fid}.2")
        total = 0.0
        detail = []
        for net in nets:
            for m in self.net_by_id[net]["members"]:
                e = self.endpoints[m]
                if e.get("supply"):
                    a = self.load_of_owner(e["owner"])
                    total += a
                    detail.append((e["owner"], a))
                if m == "CMC1.M4":
                    a = self.d["ecu"].get("load_a", 0)
                    total += a
                    detail.append(("ECU", a))
        for f in fuses:
            a, _ = self.fuse_load(f, _seen)
            total += a
            detail.append((f, a))
        return total, detail

    def _fuse_checks(self):
        self.fuse_table = []
        wire_by_net = defaultdict(list)
        for w in self.wires:
            if not w["internal"] and not w["drain"]:
                wire_by_net[w["net"]].append(w)
        for fid, o in self.owners.items():
            if o["cat"] != "fuse":
                continue
            rating = o["rating_a"]
            need = self._min_mm2(rating)
            nets, _ = self._downstream(f"{fid}.2")
            for net in nets:
                for w in wire_by_net[net]:
                    w.setdefault("fuse", fid)
                    if w["mm2"] < need:
                        self.errors.append(
                            f"{w['id']} ({fmt_mm2(w['mm2'])} mm²) derrière {fid} {rating} A : "
                            f"section mini {fmt_mm2(need)} mm²")
            load, detail = self.fuse_load(fid)
            ratio = load / rating if rating else 0
            status = "ok"
            if ratio > 1:
                status = "bad"
                self.errors.append(f"{fid} : charge estimée {load:.1f} A > calibre {rating} A")
            elif ratio > self.rules["fuse_load_warn_ratio"]:
                status = "warn"
                self.warnings.append(f"{fid} : charge estimée {load:.1f} A ({ratio:.0%} du calibre {rating} A)")
            self.fuse_table.append({
                "id": fid, "label": o["label"], "rating": rating, "min_mm2": need,
                "load": round(load, 2), "ratio": round(ratio, 2), "status": status,
                "loads": [{"id": i, "a": round(a, 2)} for i, a in detail],
            })
        self.fuse_table.sort(key=lambda f: natural_key(f["id"]))

        # Réseaux d'alimentation sans fusible amont
        for w in self.wires:
            if w["internal"] or w["drain"] or w.get("fuse"):
                continue
            members = self._members_of(w["from"])
            if any(self.endpoints[m]["owner"] == "BATT" for m in members):
                self.infos.append(f"{w['id']} : liaison batterie → fusible général, garder la plus courte possible")

    def _output_checks(self):
        self.output_table = []
        for eid, e in self.endpoints.items():
            if e["cat"] != "ecu" or e["kind"] not in ECU_OUTPUT_KINDS:
                continue
            members = self._members_of(eid)
            if not members:
                continue
            loads = sorted({self.endpoints[m]["owner"] for m in members
                            if self.endpoints[m]["cat"] in ("comp", "relay")
                            and not self.endpoints[m].get("supply")})
            if not loads:
                continue
            worst = sum(self.load_of_owner(o, True) for o in loads)
            best = sum(self.load_of_owner(o, False) for o in loads)
            max_a = e.get("max_a")
            status = "ok"
            uncertain = any(isinstance(self.owners[o].get("r_ohm"), list) for o in loads)
            if max_a and worst > max_a:
                if uncertain and best <= max_a:
                    status = "warn"
                    self.warnings.append(
                        f"{eid} ({e['fn']}) → {', '.join(loads)} : {best:.1f}–{worst:.1f} A selon la "
                        f"résistance réelle, limite {max_a} A — mesurer avant de figer")
                else:
                    status = "bad"
                    self.errors.append(f"{eid} ({e['fn']}) → {', '.join(loads)} : {worst:.1f} A > {max_a} A")
            self.output_table.append({
                "pin": eid, "fn": e["fn"], "loads": loads, "max_a": max_a,
                "a_min": round(best, 2), "a_max": round(worst, 2), "status": status,
            })
        self.output_table.sort(key=lambda r: natural_key(r["pin"]))

    # ------------------------------------------------------------ lengths
    def compute_lengths(self):
        r = self.rules
        step = r["round_to_m"]
        for w in self.wires:
            if w["internal"] or w["drain"]:
                w["length_m"] = 0
                w["path"] = []
                continue
            na = self.owners[self.endpoints[w["from"]]["owner"]]["node"]
            nb = self.owners[self.endpoints[w["to"]]["owner"]]["node"]
            dist, segs = self.path(na, nb)
            if math.isinf(dist):
                self.errors.append(f"{w['id']} : aucun chemin entre {na} et {nb}")
                dist, segs = 0, []
            raw = dist + 2 * r["termination_m"] + r["slack_m"]
            w["route_m"] = round(dist, 3)
            w["length_m"] = round(math.ceil(raw / step - 1e-9) * step, 2)
            w["path"] = segs

        self.cable_table = []
        for cid, c in self.d["cables"].items():
            cores = [w for w in self.wires if w["cable"] == cid and not w["drain"]]
            if not cores:
                self.warnings.append(f"Câble {cid} sans conducteur")
                continue
            length = max(w["length_m"] for w in cores)
            path = sorted({s for w in cores for s in w["path"]})
            self.cable_table.append({"id": cid, "label": c["label"], "type": c["type"],
                                     "od_mm": c["od_mm"], "length_m": length,
                                     "cores": [w["id"] for w in cores], "path": path,
                                     "shield": bool(c.get("shield"))})

        od = {float(k): v for k, v in r["od_mm"].items()}
        seg_items = defaultdict(list)
        for w in self.wires:
            if w["internal"] or w["drain"] or w["cable"]:
                continue
            for s in w["path"]:
                seg_items[s].append(od.get(float(w["mm2"]), 2.0))
        seg_wires = defaultdict(int)
        for w in self.wires:
            if not w["internal"] and not w["drain"]:
                for s in w["path"]:
                    seg_wires[s] += 1
        for c in self.cable_table:
            for s in c["path"]:
                seg_items[s].append(c["od_mm"])
        for seg in self.segments:
            items = seg_items.get(seg["id"], [])
            if not items:
                bundle = 0
            elif len(items) == 1:
                bundle = items[0]
            else:
                bundle = 1.15 * math.sqrt(sum(x * x for x in items))
            seg["wires"] = seg_wires.get(seg["id"], 0)
            seg["bundle_mm"] = round(bundle, 1)
            seg["sleeve"] = self._sleeve(bundle) if bundle else None

    @staticmethod
    def _sleeve(bundle):
        for exp, rec in SLEEVES:
            if exp >= 1.2 * bundle and rec <= bundle:
                return f"DR-25 {exp:g}/{rec:g} mm"
        for exp, rec in SLEEVES:
            if exp >= 1.2 * bundle:
                return f"DR-25 {exp:g}/{rec:g} mm"
        return "hors gamme"

    # --------------------------------------------------------------- BOM
    def bom(self):
        rows = []
        used = defaultdict(set)
        for w in self.wires:
            if w["internal"]:
                continue
            for end in ("from", "to"):
                e = self.endpoints[w[end]]
                if e["cat"] in ("ecu", "comp", "inline", "fuse", "relay"):
                    used[e["owner"]].add(e["pin"])

        for cid, conn in self.d["ecu"]["connectors"].items():
            rows.append({"cat": "Connecteurs", "item": conn["title"], "qty": 1,
                         "detail": f"{len(used[cid])} contacts utilisés / {len(conn['pins'])}"})
        by_conn = defaultdict(list)
        for oid, o in self.owners.items():
            if o["cat"] in ("comp", "inline") and not o.get("external"):
                by_conn[o["connector"]].append(oid)
        for conn, ids in sorted(by_conn.items()):
            contacts = sum(len(used[i]) for i in ids)
            qty = len(ids) * (2 if self.owners[ids[0]]["cat"] == "inline" else 1)
            rows.append({"cat": "Connecteurs", "item": conn, "qty": qty,
                         "detail": f"{', '.join(ids)} — {contacts} contacts"})

        fuses = sorted((o for o in self.owners.values() if o["cat"] == "fuse"),
                       key=lambda o: o["rating_a"])
        rated = defaultdict(int)
        for o in fuses:
            rated[o["ref"]] += 1
        for ref, qty in rated.items():
            rows.append({"cat": "Protection", "item": f"Fusible {ref}", "qty": qty, "detail": ""})
        relays = defaultdict(int)
        for o in self.owners.values():
            if o["cat"] == "relay":
                relays[o["ref"]] += 1
        for ref, qty in relays.items():
            rows.append({"cat": "Protection", "item": ref, "qty": qty, "detail": ""})
        rows.append({"cat": "Protection", "item": "Boîte fusibles/relais étanche avec barrettes (ex. Bussmann RTMR)",
                     "qty": 1, "detail": "2 barrettes : +12 V permanent (BUS30), +12 V commuté (BUS87)"})

        splices = [s for s, v in self.d["splices"].items() if not v.get("busbar")]
        rows.append({"cat": "Épissures", "item": "Épissure sertie ou à souder + thermo à colle (ex. Raychem D-436)",
                     "qty": len(splices), "detail": ", ".join(splices)})
        for gid in self.d["grounds"]:
            n = sum(1 for w in self.wires if gid in (w["from"], w["to"]))
            if n:
                rows.append({"cat": "Masses", "item": f"Cosse œillet M8 étamée — {gid}", "qty": n,
                             "detail": self.owners[gid]["label"]})

        meters = defaultdict(float)
        for w in self.wires:
            if w["internal"] or w["drain"] or w["cable"]:
                continue
            meters[(w["mm2"], w["color"])] += w["length_m"]
        for (mm2, color), m in sorted(meters.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            rows.append({"cat": "Fil", "item": f"FLRY-B {fmt_mm2(mm2)} mm² {color}",
                         "qty": round(m * 1.1, 1), "unit": "m", "detail": f"coupe {m:.2f} m + 10 %".replace(".", ",")})
        for c in self.cable_table:
            rows.append({"cat": "Câble", "item": c["type"], "qty": round(c["length_m"] * 1.1, 1),
                         "unit": "m", "detail": f"{c['id']} — {c['label']}"})
        sleeves = defaultdict(float)
        for s in self.segments:
            if s.get("sleeve"):
                sleeves[s["sleeve"]] += s["length"]
        for sl, m in sorted(sleeves.items()):
            rows.append({"cat": "Gaine", "item": sl, "qty": round(m * 1.1, 1), "unit": "m",
                         "detail": "selon tronçons du formboard"})
        labels = sum(2 for w in self.wires if not w["internal"] and not w["drain"])
        rows.append({"cat": "Repérage", "item": "Étiquettes thermo imprimables (repère de fil)",
                     "qty": labels, "detail": "une à chaque extrémité"})
        for r in rows:
            r.setdefault("unit", "pc")
        return rows

    # ------------------------------------------------------------- export
    def export(self):
        ecu_pins = []
        for cid, conn in self.d["ecu"]["connectors"].items():
            for pin, p in conn["pins"].items():
                eid = f"{cid}.{pin}"
                wires = [w for w in self.wires if eid in (w["from"], w["to"])]
                ecu_pins.append({"id": eid, "conn": cid, "pin": pin, "fn": p["fn"], "kind": p["kind"],
                                 "max_a": p.get("max_a"), "wires": [w["id"] for w in wires],
                                 "sheet": wires[0]["sheet"] if wires else None})
        endpoints = {k: {kk: vv for kk, vv in v.items() if vv not in (None, False, "")}
                     for k, v in self.endpoints.items()}
        five_v = sum(self.owners[o].get("supply5_ma") or 0 for o in
                     {self.endpoints[m]["owner"] for m in self._members_of("CMC1.G1")})
        return {
            "meta": self.d["meta"], "colors": self.d["colors"], "color_legend": self.d["color_legend"],
            "rules": {k: self.rules[k] for k in ("insulation", "slack_m", "termination_m", "round_to_m")},
            "sheets": self.d["sheets"], "systems": self.d["systems"],
            "ecu": {"name": self.d["ecu"]["name"],
                    "connectors": {cid: {"title": c["title"], "rows": c["rows"], "cols": c["cols"]}
                                   for cid, c in self.d["ecu"]["connectors"].items()},
                    "pins": ecu_pins},
            "owners": self.owners, "endpoints": endpoints, "wires": self.wires,
            "nets": self.nets, "cables": self.cable_table,
            "topology": {"root": self.d["topology"]["root"], "estimated": self.d["topology"]["estimated"],
                         "nodes": self.nodes, "segments": self.segments},
            "fuses": self.fuse_table, "outputs": self.output_table, "five_v_ma": five_v,
            "audit": self.d["audit"], "mtune": self.d["mtune"], "checks": self.d["checks"],
            "bom": self.bom(),
            "validation": {"errors": self.errors, "warnings": self.warnings, "infos": self.infos},
        }


def endpoint_label(h, eid):
    e = h.endpoints[eid]
    return f"{eid} ({e['fn']})"


def write_outputs(h, data, out):
    out.mkdir(parents=True, exist_ok=True)
    real = [w for w in h.wires if not w["internal"] and not w["drain"]]
    order = sorted(real, key=lambda w: (-w["mm2"], w["color"], natural_key(w["id"])))
    with open(out / "liste_de_coupe.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["Repère", "Section mm²", "Couleur", "Longueur coupe m", "Câble", "Faisceau",
                     "De", "Fonction (de)", "Vers", "Fonction (vers)", "Planche", "Fusible amont", "Note"])
        for w in order:
            wr.writerow([w["id"], fmt_mm2(w["mm2"]), w["color"], f"{w['length_m']:.2f}".replace(".", ","),
                         w["cable"] or "", w["harness"], w["from"], h.endpoints[w["from"]]["fn"],
                         w["to"], h.endpoints[w["to"]]["fn"], h.d["sheets"][w["sheet"]]["title"],
                         w.get("fuse", ""), w["note"]])
    with open(out / "brochage_ecu.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["Broche", "Fonction MaxxECU", "Repère fil", "Section mm²", "Couleur", "Destination"])
        for p in data["ecu"]["pins"]:
            ws = [w for w in h.wires if w["id"] in p["wires"]]
            if not ws:
                wr.writerow([p["id"], p["fn"], "LIBRE", "", "", ""])
            for w in ws:
                other = w["to"] if w["from"] == p["id"] else w["from"]
                wr.writerow([p["id"], p["fn"], w["id"], fmt_mm2(w["mm2"]), w["color"],
                             endpoint_label(h, other)])
    with open(out / "nomenclature.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["Catégorie", "Article", "Quantité", "Unité", "Détail"])
        for r in data["bom"]:
            wr.writerow([r["cat"], r["item"], str(r["qty"]).replace(".", ","), r["unit"], r["detail"]])
    (out / "harness.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "rapport.md").write_text(report_md(h, data), encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (out / "faisceau.html").write_text(html.replace("/*__HARNESS_DATA__*/null", payload), encoding="utf-8")


def report_md(h, data):
    m = data["meta"]
    v = data["validation"]
    sev = {"fix": "🛠 Corrigé", "add": "➕ Ajouté", "warn": "⚠️ À vérifier", "ok": "✅ Validé"}
    real = [w for w in h.wires if not w["internal"] and not w["drain"]]
    lines = [f"# {m['project']} — rapport de vérification", "",
             f"*{m['ecu']} · révision {m['revision']} · {m['date']} · {m['status']}*", "",
             "> Généré par `tools/build_harness.py` depuis `harness/m50b25_vanos_turbo.yaml`. Ne pas éditer à la main.", "",
             f"**{len(real)} fils** · **{sum(w['length_m'] for w in real):.1f} m de fil coupé** · "
             f"{len(h.d['splices'])} épissures/barrettes · {len(data['fuses'])} fusibles · "
             f"{sum(1 for o in h.owners.values() if o['cat'] == 'relay')} relais", "",
             f"## Contrôle des règles électriques : {len(v['errors'])} erreur(s), {len(v['warnings'])} alerte(s)", ""]
    for e in v["errors"]:
        lines.append(f"- ❌ {e}")
    for w in v["warnings"]:
        lines.append(f"- ⚠️ {w}")
    for i in v["infos"]:
        lines.append(f"- ℹ️ {i}")
    if not (v["errors"] or v["warnings"] or v["infos"]):
        lines.append("- Aucun point.")
    lines += ["", "## Audit du plan d'origine", ""]
    for a in data["audit"]:
        lines += [f"### {sev[a['sev']]} — {a['title']}", "", a["detail"], ""]
    lines += ["## Fusibles", "", "| Fusible | Circuit | Calibre | Section mini | Charge estimée | Taux |",
              "|---|---|---|---|---|---|"]
    for f in data["fuses"]:
        lines.append(f"| {f['id']} | {f['label']} | {f['rating']} A | {fmt_mm2(f['min_mm2'])} mm² | "
                     f"{f['load']:.1f} A | {f['ratio']:.0%} |")
    lines += ["", "## Sorties ECU chargées", "", "| Broche | Fonction | Charge | Courant | Limite |",
              "|---|---|---|---|---|"]
    for o in data["outputs"]:
        cur = f"{o['a_min']:.2f} A" if o["a_min"] == o["a_max"] else f"{o['a_min']:.2f}–{o['a_max']:.2f} A"
        lim = f"{o['max_a']} A" if o["max_a"] else "—"
        lines.append(f"| {o['pin']} | {o['fn']} | {', '.join(o['loads'])} | {cur} | {lim} |")
    lines += ["", f"Consommation estimée sur le +5 V capteurs (G1) : **{data['five_v_ma']} mA**.", "",
              "## Brochage ECU", "", "| Broche | Fonction | Fil | Section | Couleur | Vers |", "|---|---|---|---|---|---|"]
    for p in data["ecu"]["pins"]:
        ws = [w for w in h.wires if w["id"] in p["wires"]]
        for w in ws:
            other = w["to"] if w["from"] == p["id"] else w["from"]
            lines.append(f"| {p['id']} | {p['fn']} | {w['id']} | {fmt_mm2(w['mm2'])} | {w['color']} | {endpoint_label(h, other)} |")
    free = [p for p in data["ecu"]["pins"] if not p["wires"]]
    lines += ["", "Broches libres : " + ", ".join(f"{p['id']} ({p['fn']})" for p in free), ""]
    lines += ["## Réglages MTune liés au câblage", "", "| Fonction | Réglage |", "|---|---|"]
    for t in data["mtune"]:
        lines.append(f"| {t['item']} | {t['value']} |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", default=str(DEFAULT_SRC))
    ap.add_argument("--out", default=str(ROOT / "docs"))
    args = ap.parse_args()
    data = yaml.safe_load(Path(args.source).read_text(encoding="utf-8"))
    h = Harness(data)
    h.erc()
    h.compute_lengths()
    export = h.export()
    write_outputs(h, export, Path(args.out))
    v = export["validation"]
    real = [w for w in h.wires if not w["internal"] and not w["drain"]]
    print(f"{len(real)} fils, {sum(w['length_m'] for w in real):.1f} m, "
          f"{len(v['errors'])} erreur(s), {len(v['warnings'])} alerte(s), {len(v['infos'])} info(s)")
    for e in v["errors"]:
        print(f"  ERREUR  {e}")
    for w in v["warnings"]:
        print(f"  ALERTE  {w}")
    for i in v["infos"]:
        print(f"  INFO    {i}")
    return 1 if v["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
