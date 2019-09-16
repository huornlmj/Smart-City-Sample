#!/usr/bin/python3

from db_ingest import DBIngest
from db_query import DBQuery
from signal import signal, SIGTERM
import time
import os

retention_time=float(os.environ["RETENTION_TIME"])  # in seconds
service_interval=float(os.environ["SERVICE_INTERVAL"])  # in seconds
indexes=os.environ["INDEXES"].split(",")
office=list(map(float, os.environ["OFFICE"].split(",")))
dbhost=os.environ["DBHOST"]
storage="/var/www/mp4"

dbs=None
rs=None

def quit_service(signum, sigframe):
    if dbs and rs: dbs.delete(rs["_id"])
    exit(143)

signal(SIGTERM, quit_service)
dbs=DBIngest(index="services",office=office,host=dbhost)
while True:
    try:
        rs=dbs.ingest({
            "name": "cleanup",
            "service": "maintanence",
            "status": "active",
        })
        break
    except Exception as e:
        print("Exception: "+str(e), flush=True)
        time.sleep(10)

while True: 
    time.sleep(service_interval)

    print("Searching...",flush=True)
    for index in indexes:
        db=DBQuery(index=index,office=office,host=dbhost)
        try:
            for r in db.search("time<now-"+str(retention_time*1000), size=500):
                # delete the record
                db.delete(r["_id"])
    
                # delete the path file
                if "path" in r["_source"]:
                    try:
                        os.remove(storage+"/"+r["_source"]["path"])
                        os.remove(storage+"/"+r["_source"]["path"]+".png")
                    except Exception as e:
                        pass
        except Exception as e:
            print("Exception: "+str(e), flush=True)
            time.sleep(10)

