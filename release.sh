#!/bin/bash -e
# INCREMENT VERSION
# -----------------
# shellcheck disable=SC2089
inc_version_command='import datetime as d;v=[int(v) for v in open("VERSION").read().split(".")];y=d.datetime.now().year;print(f"{v[0]}.{v[1]+1}" if v[0]==y else f"{y}.0",end="",flush=True)'
# python script `inc_version_command` equates to:
# >>> import datetime
# >>> # get version elements as ints (e.g. [2022, 0])
# >>> version_major, version_minor = [int(v) for v in open("VERSION").read().split(".")]
# >>> year = datetime.datetime.now().year  # current year
# >>> if version_major == year:
# >>>     # same year as current version, increment least significant int
# >>>     version_minor += 1
# >>> else:
# >>>     # new year, set version to {year}.0
# >>>     version_major, version_minor = year, 0
# >>> # print new version number with no newline
# >>> print(f"{version_major}.{version_minor}", end="", flush=True)
new_version=$(python -q -c "${inc_version_command}")
# this has to be in a separate command because bash opens VERSION for writing before executing the command
echo "${new_version}" > VERSION

# COMMIT CHANGES
# --------------
git add VERSION
git commit -m "release ${new_version}"

# TAG AND PUSH TO GITHUB FOR GITHUB ACTION TO PUBLISH
# ---------------------------------------------------
git tag "${new_version}"
git push origin "${new_version}"
