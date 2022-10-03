# WebFetch
This project is brand new. The API is 100% guaranteed to change. Also the name.

This library aims to make automating tasks that require
authentication on web sites simpler. In general it would
be better to make HTTP requests using an appropriate
library, but at times it is not obvious how to replicate
the login process and you don't want to have to reverse
engineer the site just to get your task done. That is where
this library comes in.

We use Selenium to automate a Chrome instance, and set the
user data directory to the Chrome default so that "remember
me" settings will persist to avoid 2FA on every instance.
We install ChromeDriver in a user binary location and manage
ensuring the ChromeDriver version is correct for the current
installed Chrome version.

We expose a `fetch` method to make HTTP requests to the site
with credentials, eliminating the need to copy cookies and
headers; and an `outside_request` method that uses `urllib3`
(which is also a dependency of Selenium) to make anonymous
HTTP requests.

We also introduce a couple of methods that support exploring
a site's Javascript environment from within Python:
`page.window.new_keys()` lists non-default global variables,
and `page.window[key]` will access global variables.
`page.browser.debug_show_page` will dump a text version of
the current page to the console (if `html2text` is
installed, otherwise the raw page source).
`site.browser.debugger_url` is the address to find the
Chrome debugger to access the browser environment.

# Installation
#### Requirement format for this GitHub repo as a dependency
`webfetch @ git+https://git@github.com/Accounting-Data-Solutions/webfetch@main`

#### pip
This is not yet published on PyPI because I'm not sure I like the name.

# Usage
Generally, the `webfetch` API is intended to follow the
[encouraged practice of page object models](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
by establishing a pattern of defining `Page` classes each
with one initialization method that defines selectors for
all relevant elements on the page and one or more action
methods defining the desired interaction with the page.

### Define your Site
The Site is a special version of a Page object that defines
your login page and the method to complete the login action.
All other Page objects will have a reference to this for
testing if you are authenticated and repeating the login
if necessary.

```python
from webfetch import Site, Page

class MySite(Site):
    def __init__(self):
        # get login credentials from secure location
        credentials = {}
        super().__init__(
            login_url="https://www.example.com/login",
            credentials=credentials,
        )
    
    def _init_login(self):
        self.username_selector = "input#username"
        self.password_selector = "input#password"
        self.submit_selector = "button#login"

    def _do_login(self) -> "MySite":
        self.css(self.username_selector).clear().send_keys(self.credentials["username"])
        self.css(self.password_selector).clear().send_keys(self.credentials["password"])
        self.css(self.submit_selector).click()
        return self

    def is_authenticated(self) -> bool:
        return self.window["localStorage.accessToken"] is not None
```

### Define a Page

```python
class MyPage(Page):
    def __init__(self):
        super().__init__(MySite())
        self.navigate("https://www.example.com/interest")

    def _init_page(self) -> None:
        self.element_of_interest = "//div[@id='interest']"
        self.action_button = "#action-btn"

    def get_interesting_text(self) -> str:
        element = self.xpath(self.element_of_interest)
        return element.text

    def do_page_action(self) -> None:
        self.css(self.action_button).click()
```

### Use your Page object

```python
page = MyPage()
print(f"Received '{page.get_interesting_text()}'. Interesting!")
page.do_page_action()
print(f"Non-default global variables are {page.window.new_keys()}")
print(f"The document title is '{page.window['document.title']}'.")
response = page.window.fetch(method="post", url="/api/option", payload={"showInterest": True}, headers={"x-snowflake": "example-option-header"})
print(f"Fetch returned '{response['data']}'.")
response = page.outside_request(method="get", url="https://www.google.com", destination="text")
print(f"The length of Google's page source is {len(response)} characters.")
```

# References
- [Selenium Python bindings documentation](https://www.selenium.dev/selenium/docs/api/py/index.html)
- [Selenium project documentation](https://www.selenium.dev/documentation/)
- [lxml html parser documentation](https://lxml.de/lxmlhtml.html)

# Development
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
