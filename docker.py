#!/usr/bin/python
import os
import re
import sys
from subprocess import Popen, PIPE

singularity = True
if any('grid-workernode-c7' in arg for arg in sys.argv):
    singularity = True

gateway = False
if any('atl' in arg for arg in sys.argv) or any('cms' in arg for arg in sys.argv):
    gateway = True

count = 0
dargs = ['/usr/bin/sudo', '/usr/bin/docker']
for arg in sys.argv:
    if count > 0:
        m = re.search(r'--memory=([\d]+)m', arg)
        if m:
            memory = int(m.group(1))
            dargs.append('--memory=%dm' % (memory*2))
            dargs.append('--memory-reservation=%dm' % memory)
            if not os.path.isfile('/etc/nogateway') and gateway:
                dargs.append('--network=ralworker')
                dargs.append('--add-host=xrootd.echo.stfc.ac.uk:172.28.1.1')
                dargs.append('--add-host=cms-aaa-proxy695.gridpp.rl.ac.uk:172.28.1.1')
                dargs.append('--add-host=cms-aaa-proxy719.gridpp.rl.ac.uk:172.28.1.1')
                dargs.append('--label=xrootd-local-gateway=true')
            else:
                dargs.append('--label=xrootd-local-gateway=false')
        else:
            dargs.append(arg)

        # Allow singularity to work inside of Docker containers
        if arg == 'run' and singularity:
            dargs.append('-eSINGULARITY_BINDPATH=/etc/hosts')
            dargs.append('--cap-add=SYS_ADMIN')
            dargs.append('--cap-add=DAC_OVERRIDE')
            dargs.append('--cap-add=SETUID')
            dargs.append('--cap-add=SETGID')
            dargs.append('--cap-add=SYS_CHROOT')
    count += 1


if '/' in dargs[-1] and not dargs[-1].startswith('-'):
    command = dargs.pop()
    dargs = dargs + ['/usr/bin/nice', '-n 15', command]

p = Popen(dargs, stdout=PIPE, stderr=PIPE)
output, err = p.communicate()
for l in output:
    sys.stdout.write(l)
for l in err:
    sys.stderr.write(l)
exit(p.returncode)
