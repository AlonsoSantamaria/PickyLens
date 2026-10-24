"""One-time DNS addition on the verified VESTA authoritative zone."""
from pathlib import Path
import re
import shutil
import subprocess
zone=Path('/var/lib/bind/neovantia.live.hosts')
text=zone.read_text()
record='pickylens.neovantia.live. 300 IN A 163.245.192.48'
if 'pickylens.neovantia.live.' in text:
    raise SystemExit('PickyLens DNS name already exists; inspect instead of overwriting')
match=re.search(r'(SOA[^\n]+\(\s*)(\d+)',text)
if not match:raise SystemExit('SOA serial not found')
serial=str(int(match.group(2))+1)
updated=text[:match.start(2)]+serial+text[match.end(2):]+'\n'+record+'\n'
backup=zone.with_name(zone.name+'.before-pickylens')
if backup.exists():raise SystemExit('Backup already exists; inspect before retry')
shutil.copy2(zone,backup)
candidate=zone.with_name(zone.name+'.pickylens-candidate')
shutil.copy2(zone,candidate)
candidate.write_text(updated)
subprocess.run(['named-checkzone','neovantia.live',str(candidate)],check=True)
candidate.replace(zone)
subprocess.run(['rndc','reload','neovantia.live'],check=True)
print('Single PickyLens A record added; prior zone preserved.')
