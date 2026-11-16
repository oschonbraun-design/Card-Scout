#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from cardscanner.serpapi_ebay import SerpApiEbayClient
from cardscanner.identity import parse_identity
from cardscanner.comps import CsvCompProvider, comp_stats
from cardscanner.scoring import score_deal
from cardscanner.alerts import send_alert, format_alert
from cardscanner.db import connect, is_new

def load_cfg(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def scan(cfg, db_path, comps_path):
    client=SerpApiEbayClient(); db=connect(db_path)
    comps=CsvCompProvider(comps_path,cfg["max_comp_age_days"])
    candidates=alerts=0
    for p in cfg["players"]:
        for q in p["queries"]:
            try:
                items=client.search(q,p["name"],cfg["budget"]["min"],cfg["budget"]["max"])
                for item in items:
                    if not is_new(db,item.item_id,item.title,item.price): continue
                    candidates+=1
                    ident,conf=parse_identity(item.title,p["name"]); item.identity=ident; item.confidence=conf
                    stats=comp_stats(comps.get(ident.fingerprint()))
                    result=score_deal(item,stats,cfg)
                    if result and result["level"] in {"WATCH","GOOD","STEAL"}:
                        send_alert(format_alert(item,result,stats)); alerts+=1
            except Exception as e:
                print(f"Query failed [{q}]: {e}")
    print(f"Scan complete: {candidates} new listings checked; {alerts} alerts.")

def main():
    ap=argparse.ArgumentParser(description="Conservative eBay sports-card deal scanner")
    ap.add_argument("--config",default="config.json"); ap.add_argument("--db",default="scanner.db")
    ap.add_argument("--comps",default="data/comps.csv"); ap.add_argument("--loop",action="store_true")
    args=ap.parse_args(); cfg=load_cfg(args.config)
    while True:
        scan(cfg,args.db,args.comps)
        if not args.loop: break
        time.sleep(max(60,int(cfg["scan_interval_seconds"])))
if __name__=="__main__": main()
