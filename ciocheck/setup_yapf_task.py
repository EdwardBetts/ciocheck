# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""Setup script auxiliary process so we can `yapf` and `isort` in parallel."""

from __future__ import absolute_import, print_function

# Standard library imports
import codecs
import os
import platform
import sys

# Third party imports
from yapf.yapflib.yapf_api import FormatFile
import isort

# Local imports
from ciocheck import CONFIGURATION_FILE
from ciocheck.setup_atomic_replace import atomic_replace


def _format_file(path):
    root_path = os.environ.get('CIOCHECK_PROJECT_ROOT', None)
    style_config = None
    short_path = path.replace(root_path, '.')

    if root_path:
        style_config_path = os.path.join(root_path, CONFIGURATION_FILE)
        if os.path.isfile(style_config_path):
            style_config = style_config_path

    try:
        # First isort
        with open(path, 'r') as f:
            old_contents = f.read()
        new_contents = isort.SortImports(file_contents=old_contents).output

        with open(path, 'w') as f:
            f.write(new_contents)
        isort_changed = new_contents != old_contents

        # Then YAPF
        # It might be tempting to use the "inplace" option to FormatFile, but
        # it doesn't do an atomic replace, which is dangerous, so don't use
        # it unless you submit a fix to yapf.
        (contents, encoding, changed) = FormatFile(path,
                                                   style_config=style_config)
        if platform.system() == 'Windows':
            # yapf screws up line endings on windows
            with codecs.open(path, 'r', encoding) as f:
                old_contents = f.read()

            contents = contents.replace("\r\n", "\n")
            if len(old_contents) == 0:
                # Windows yapf seems to force a newline? I dunno
                contents = ""
            changed = (old_contents != contents)
    except Exception as e:
        error = "yapf crashed on {path}: {error}".format(path=short_path,
                                                         error=e)
        print(error, file=sys.stderr)
        return False

    if changed:
        atomic_replace(path, contents, encoding)
        print("\nReformatted:     {path}".format(path=short_path))
    if isort_changed:
        print("\nSorted imports in {path}.".format(path=short_path))

    return changed and isort_changed


exit_code = 0
for filename in sys.argv[1:]:
    if not _format_file(filename):
        exit_code = 1

sys.exit(exit_code)