"""Select one immutable review catalog while retaining setup-bazel's caches."""

import os
from pathlib import Path
import re
import shlex
import shutil
import tempfile


revision = os.environ['SONIC_BAZEL_REGISTRY_REVISION']
assert re.fullmatch('[0-9a-f]{40}', revision)
main = 'https://raw.githubusercontent.com/securely1g/sonic-bazel-registry/main'
configuration = Path('.bazelrc').read_text()
assert configuration.count(main) == 1
configuration = configuration.replace(main, main.removesuffix('main') + revision)
home = Path.home() / '.bazelrc'
if home.is_file():
    caches = [line for line in home.read_text().splitlines()
              if line.startswith(('build --disk_cache=', 'common --repository_cache='))]
    configuration += '\n' + '\n'.join(caches) + '\n'
directory = Path(tempfile.mkdtemp(prefix='linkmgrd-bazel-'))
rc = directory / 'review.bazelrc'
rc.write_text(configuration)
binary = shutil.which('bazel')
assert binary
wrapper = directory / 'bazel'
wrapper.write_text('#!/bin/sh\nexec ' + shlex.quote(binary) +
                   ' --host_jvm_args=-Xmx3g --nosystem_rc --nohome_rc --noworkspace_rc --bazelrc=' +
                   shlex.quote(str(rc)) + ' "$@"\n')
wrapper.chmod(0o755)
evidence = Path('bazel-evidence')
evidence.mkdir(exist_ok=True)
(evidence / 'review.bazelrc').write_text(configuration)
if os.environ.get('GITHUB_ENV'):
    with open(os.environ['GITHUB_ENV'], 'a') as environment:
        environment.write('BAZEL_BINARY=' + str(wrapper) + '\n')
print(wrapper)
