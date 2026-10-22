#!/usr/bin/env python3
"""Send one explicitly requested synthetic alert to Desktop B."""
import argparse, json, os, sys, urllib.error, urllib.request, uuid

def main():
    parser=argparse.ArgumentParser(description="Send a harmless synthetic DDSM alert")
    parser.add_argument("--receiver",required=True,help="Desktop B Tailscale URL, e.g. http://100.x.y.z:8787")
    parser.add_argument("--source",default="Desktop-A",help="Short source label")
    args=parser.parse_args()
    token=os.environ.get("DDSM_TOKEN","")
    if len(token)<32: raise SystemExit("Set DDSM_TOKEN to the same random secret used on Desktop B.")
    payload={"event_id":str(uuid.uuid4()),"source":args.source[:80],"event_type":"synthetic_test_alert",
             "severity":"info","details":"Harmless connectivity test. No personal data included."}
    req=urllib.request.Request(args.receiver.rstrip("/")+"/api/events",data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer "+token},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=8) as response:
            print("Receiver response:",response.status,response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print("Receiver rejected the event:",exc.code,exc.read().decode("utf-8"),file=sys.stderr);raise SystemExit(1)
    except (urllib.error.URLError,TimeoutError) as exc:
        print("Could not reach Desktop B. Check Tailscale, IP, port, and firewall:",exc,file=sys.stderr);raise SystemExit(1)
if __name__=="__main__": main()
