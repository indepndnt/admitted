# WebFetch

This project is brand new. The API is 100% guaranteed to change.

# References

- [Selenium Python bindings documentation](https://www.selenium.dev/selenium/docs/api/py/index.html)
- [Selenium project documentation](https://www.selenium.dev/documentation/)
- [lxml html parser documentation](https://lxml.de/lxmlhtml.html)

# Installation

### Requirement format for this GitHub repo as a dependency
`webfetch @ git+https://git@github.com/Accounting-Data-Solutions/webfetch@main`


# git pre-commit
#### .git/hooks/pre-commit
```bash
#!/bin/bash
if [ -z "${VIRTUAL_ENV}" ] ; then
  echo "Please activate your virtual environment before commit!"
  exit 1
fi
root=$(git rev-parse --show-toplevel)
black ${root} | while read line ; do
  if [[ ${line} == "reformatted*" ]] ; then
    len=$(($(wc -c <<< ${line})-12))
    file=${line:12:len}
    git add ${file}
  fi
done
pylint -j2 -sn ${root}/src/webfetch
pytest -x
```
