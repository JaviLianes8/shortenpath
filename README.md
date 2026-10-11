# shortenpath

Abbreviate a filesystem path for display within a width budget: collapse home to `~` and middle-elide long paths.

## Install

```
pip install shortenpath
```

## Usage

```python
from shortenpath import shorten

# Short paths pass through untouched.
shorten("/etc/hosts", 40)                       # "/etc/hosts"

# The home directory collapses to ~.
shorten("/home/javi/code/app.py", home="/home/javi")   # "~/code/app.py"

# Too long for the budget: the middle is elided, head and tail stay readable.
shorten("/a/b/c/d/e/file", 11)                  # "/a/.../file"
shorten("/home/javi/proj/sub/deep/file.py", 20, home="/home/javi")
                                                # "~/proj/.../file.py"

# When even the basename overflows, it is truncated from the front.
shorten("/a/b/verylongfilename.py", 8)          # "...me.py"

# Works with any separator (Windows paths, URLs, custom roots).
shorten("C:\\a\\b\\c\\d\\report.txt", 18, sep="\\")     # "C:\...\report.txt"
```

`shorten(path, max_len, *, home_tilde=True, home=None, sep=os.sep, placeholder="...")`
returns a string no longer than `max_len`. It is display-only and never reads the
filesystem: `home` defaults to the current user's home directory but can be set
explicitly for deterministic output, and `sep` selects the separator to split on.

## Why

Collapsing a path to `~` and trimming its middle to fit a column budget is a common
need in prompts, status bars, logs and tables, yet on PyPI the pieces live apart:
`os.path.expanduser` only expands, and `textwrap.shorten` truncates words from the end,
not the middle of a path. The npm (`tildify`) and Rust ecosystems ship this, but the
Python versions circulate as copy-paste snippets. This packages the two together,
typed, with no dependencies.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
