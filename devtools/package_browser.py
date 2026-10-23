"""Build a judge bundle pinned to one operator-selected HTTPS origin."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile


def package(origin, destination):
    url=urlsplit(origin)
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:
        raise ValueError('Supply one HTTPS origin without credentials, path, query or fragment')
    origin=origin.rstrip('/')
    source=Path(__file__).resolve().parents[1]/'extensions'/'browser'
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(destination,'x') as out:
        for path in source.iterdir():
            if not path.is_file():continue
            content=path.read_bytes()
            if path.name=='manifest.json':
                manifest=json.loads(content);manifest['host_permissions']=[origin+'/*'];content=json.dumps(manifest,indent=2).encode()
            elif path.name=='worker.js':
                content=content.replace(b"'http://127.0.0.1:8000'",json.dumps(origin).encode())
            out.writestr(path.name,content)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('origin');parser.add_argument('destination');args=parser.parse_args()
    package(args.origin,args.destination)
