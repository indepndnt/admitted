# Admitted
_/ədˈmɪtɪd/ verb : allowed entry (as to a place, fellowship, or privilege)_

This project is very new. The API is very likely to change.

This library aims to make automating tasks that require authentication on websites simpler. In general, it would
be better to make HTTP requests using an appropriate library, but at times it is not obvious how to replicate
the login process, and you don't want to have to reverse engineer the site just to get your task done. That is where
this library comes in.

We use Selenium to automate a Chrome for Testing instance, and set the user data directory to the Chrome default so that
"remember me" settings will persist to avoid 2FA on every instance. We automatically install Chrome For Testing and
ChromeDriver in a user binary location and manage ensuring the versions are aligned.

We expose a `fetch` method to make HTTP requests to the site with credentials through Chrome, eliminating the need to
copy cookies and headers; and a `direct_request` method that uses `urllib3` (which is also a dependency of Selenium) to
make anonymous HTTP requests.

We also introduce a couple of methods that support exploring a site's Javascript environment from within Python:
`page.window.new_keys()` lists non-default global variables, and `page.window[key]` will access global variables.
`page.browser.debug_show_page` will dump a text version of the current page to the console (if `html2text` is
installed, otherwise the raw page source).

# Installation
#### pip
- `pip install admitted`, or
- `pip install admitted[debug]` to include `html2text` for exploratory work, or
- `pip install admitted[dev]` for the development environment.

#### Requirement format for this GitHub repo as a dependency
`admitted @ git+https://git@github.com/Accounting-Data-Solutions/admitted@main`

### Chrome for Testing
Chrome versions earlier than 115 are no longer supported. You need to have Chrome for Testing installed. See
[Chrome for Testing availability](https://googlechromelabs.github.io/chrome-for-testing/) for download options.

# Usage
Generally, the `admitted` API is intended to follow the
[encouraged practice of page object models](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
by establishing a pattern of defining `Page` classes each with one initialization method that defines selectors for
all relevant elements on the page and one or more action methods defining the desired interaction with the page.

### Define your Site
The Site is a special version of a Page object that defines your login page and the method to complete the login action.
All other Page objects will have a reference to this for testing if you are authenticated and repeating the login
if necessary.

The default behavior of `Site.__init__` is to call the `login` method; this can be avoided by passing `postpone=True`
to `Site`.

```python
from admitted import Site, Page

class MySite(Site):
    def __init__(self):
        # get login credentials from secure location
        credentials = {
          "username": "user",
          "password": "do_not_actually_put_your_password_in_your_code",
        }
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
The default behavior of `Page.navigate` is to call `self.site.login` on the first retry if navigation fails.

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
response = page.window.fetch(method="post", url="/api/option", payload={"showInterest": True},
                             headers={"x-snowflake": "example-option-header"})
print(f"Fetch returned '{response.json}'.")
response = page.direct_request(method="get", url="https://www.google.com")
print(f"The length of Google's page source is {len(response.text)} characters.")
```

### HTTP Response API
The `Page.window.fetch` and `Page.direct_request` methods both return a `Response` object with the following API.
- `content` property: Response body as `bytes`.
- `text` property: Response body as `str`, or `None`.
- `json` property: JSON parsed response body, or `None`.
- `html` property: `lxml` parsed HTML element tree, or `None`.
- `write_stream` method: Stream response data to the provided file pointer if `direct_request` method was called with `stream=True`, otherwise writes `Response.content`.
  - `destination` argument: file pointer for a file opened with a write binary mode.
  - `chunck_size` argument: (optional) number of bytes to write at a time.
  - Returns `destination`.

# References
- [Selenium Python bindings documentation](https://www.selenium.dev/selenium/docs/api/py/index.html)
- [Selenium project documentation](https://www.selenium.dev/documentation/)
- [lxml html parser documentation](https://lxml.de/lxmlhtml.html)

# Development
Configure pre-commit hooks to format, lint, and test code before commit.
#### `.git/hooks/pre-commit`
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
pylint --rcfile ${root}/pyproject.toml ${root}/src/admitted
pytest -x -rN --no-cov --no-header
```

### Release
A release is published to PyPI by a GitHub Action when there is a push to `main` with a tag (see
`.github/workflows/publish.yml`). Run ./release.sh to increment the version number and push with a tag.
