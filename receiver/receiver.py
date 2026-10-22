#!/usr/bin/env python3
"""Visible, tailnet-only alert receiver. Python standard library only."""
import argparse, hmac, json, os, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

MAX_BODY = 16 * 1024
ALLOWED_SEVERITIES = {"info", "low", "medium", "high", "critical"}
EVENTS_FILE = Path(__file__).resolve().parent / "events.jsonl"
lock = threading.Lock()
seen_ids = set()

DASHBOARD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DualDesktopSecurityMonitor</title><style>
:root{color-scheme:dark;font:16px system-ui,sans-serif;background:#0b1220;color:#e8eef8}body{max-width:1050px;margin:0 auto;padding:24px}
h1{font-size:clamp(1.5rem,4vw,2.2rem)}.muted{color:#9eafc8}.pill{border:1px solid #355072;border-radius:999px;padding:5px 10px}
.panel{background:#121e31;border:1px solid #263a55;border-radius:16px;padding:18px;margin-top:18px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px 8px;border-bottom:1px solid #293b54;vertical-align:top;overflow-wrap:anywhere}
th{color:#a9bdd7;font-size:.85rem}button{background:#264a75;color:white;border:0;border-radius:9px;padding:9px 13px}
@media(max-width:650px){body{padding:12px}.tablewrap{overflow-x:auto}th,td{min-width:110px}}
</style></head><body><header><p class="muted">LOCAL NETWORK SECURITY LAB</p><h1>DualDesktopSecurityMonitor</h1>
<p class="muted">Desktop B receiver · visible event history · authenticated submissions</p><span class="pill" id="status">Loading…</span></header>
<section class="panel"><h2>Recent alerts</h2><p class="muted">Events are stored locally in receiver/events.jsonl. Refreshes every 5 seconds.</p>
<div class="tablewrap"><table><thead><tr><th>Received</th><th>Severity</th><th>Source</th><th>Event</th><th>Details</th></tr></thead><tbody id="events"></tbody></table></div></section>
<script>
async function refresh(){try{const r=await fetch('/api/events',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json(),b=document.getElementById('events');b.replaceChildren();
if(!d.events.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='No alerts received yet.';tr.append(td);b.append(tr);}
for(const e of d.events){const tr=document.createElement('tr');for(const v of [e.received_at,e.severity,e.source,e.event_type,e.details]){const td=document.createElement('td');td.textContent=String(v??'');tr.append(td);}b.append(tr);}
document.getElementById('status').textContent='Online · '+d.events.length+' events';}catch(e){document.getElementById('status').textContent='Receiver unavailable';}}
refresh();setInterval(refresh,5000);
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    server_version = "DDSMReceiver/1.0"
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))
    def send_json(self, status, payload):
        raw=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff");self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":
            raw=DASHBOARD.encode("utf-8");self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(raw)))
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Security-Policy","default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'")
            self.send_header("X-Content-Type-Options","nosniff");self.end_headers();self.wfile.write(raw)
        elif path=="/api/events":
            events=[]
            with lock:
                if EVENTS_FILE.exists():
                    try:
                        for line in EVENTS_FILE.read_text(encoding="utf-8").splitlines()[-200:]:
                            try: events.append(json.loads(line))
                            except json.JSONDecodeError: pass
                    except OSError: pass
            self.send_json(200,{"events":list(reversed(events))})
        elif path=="/health": self.send_json(200,{"status":"ok"})
        else: self.send_json(404,{"error":"not found"})
    def do_POST(self):
        if urlparse(self.path).path!="/api/events": self.send_json(404,{"error":"not found"});return
        expected=("Bearer "+self.server.auth_token).encode()
        if not hmac.compare_digest(self.headers.get("Authorization","").encode(),expected):
            self.send_json(401,{"error":"unauthorized"});return
        if self.headers.get("Content-Type","").split(";")[0].strip().lower()!="application/json":
            self.send_json(415,{"error":"content-type must be application/json"});return
        try: length=int(self.headers.get("Content-Length","0"))
        except ValueError: self.send_json(400,{"error":"invalid content length"});return
        if length<1 or length>MAX_BODY: self.send_json(413,{"error":"body must be between 1 and 16384 bytes"});return
        try: p=json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError): self.send_json(400,{"error":"invalid JSON"});return
        if not isinstance(p,dict): self.send_json(400,{"error":"JSON object required"});return
        eid,source,etype=p.get("event_id"),p.get("source"),p.get("event_type")
        severity,details=p.get("severity","info"),p.get("details","")
        if not all(isinstance(v,str) and 1<=len(v)<=n for v,n in [(eid,80),(source,80),(etype,100)]):
            self.send_json(400,{"error":"event_id, source, and event_type must be short strings"});return
        if severity not in ALLOWED_SEVERITIES: self.send_json(400,{"error":"invalid severity"});return
        if not isinstance(details,str) or len(details)>2000: self.send_json(400,{"error":"details must be a string of at most 2000 characters"});return
        with lock:
            if eid in seen_ids: self.send_json(409,{"error":"duplicate event_id"});return
            seen_ids.add(eid)
            if len(seen_ids)>10000: seen_ids.clear();seen_ids.add(eid)
            event={"event_id":eid,"received_at":time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),
                   "source":source,"event_type":etype,"severity":severity,"details":details}
            try:
                EVENTS_FILE.parent.mkdir(parents=True,exist_ok=True)
                with EVENTS_FILE.open("a",encoding="utf-8") as f: f.write(json.dumps(event,ensure_ascii=False)+"\n")
            except OSError:
                seen_ids.discard(eid);self.send_json(500,{"error":"could not save event"});return
        self.send_json(201,{"accepted":True,"event_id":eid})

def main():
    parser=argparse.ArgumentParser(description="Desktop B authenticated alert receiver")
    parser.add_argument("--host",required=True,help="Desktop B Tailscale IPv4 address, e.g. 100.x.y.z")
    parser.add_argument("--port",type=int,default=8787);args=parser.parse_args()
    token=os.environ.get("DDSM_TOKEN","")
    if len(token)<32: raise SystemExit("Set DDSM_TOKEN to a random secret of at least 32 characters.")
    if not 1<=args.port<=65535: raise SystemExit("Port must be between 1 and 65535.")
    server=ThreadingHTTPServer((args.host,args.port),Handler);server.auth_token=token
    print("Dashboard listening on http://%s:%s/"%(args.host,args.port))
    print("Bind to Desktop B's Tailscale IP only. Tailscale encrypts tailnet traffic.")
    print("Press Ctrl+C to stop. Events are saved in receiver/events.jsonl.")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nStopping receiver.")
    finally: server.server_close()
if __name__=="__main__": main()
