# Publishing Myco to PyPI

Everything is ready. You just need a PyPI API token.

## The one manual step

1. Go to **https://pypi.org/account/register/** and register with:
   - Email: `thiibaultdantigny292@gmail.com`
   - Username: `Battam1111` (or similar)
   - Verify your email when the confirmation arrives

2. After login, go to **https://pypi.org/manage/account/token/** and create a token:
   - Token name: `myco-publish`
   - Scope: `Entire account` (first upload) → switch to project-scoped after first publish
   - Copy the token (shown only once — starts with `pypi-`)

3. Create `C:\Users\10350\.pypirc` with this content:
   ```ini
   [distutils]
   index-servers = pypi

   [pypi]
   repository = https://upload.pypi.org/legacy/
   username = __token__
   password = pypi-PASTE_YOUR_TOKEN_HERE
   ```

4. Run the upload:
   ```cmd
   scripts\pypi_upload.bat
   ```
   Or directly:
   ```cmd
   python -m twine upload dist\*
   ```

5. Verify: https://pypi.org/project/myco/

## After publishing

Update README to show the pip install badge. Add to the top of README.md:

```markdown
[![PyPI version](https://badge.fury.io/py/myco.svg)](https://badge.fury.io/py/myco)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

## Future releases

```bash
# Update version in src/myco/__init__.py and pyproject.toml
# Then rebuild and upload:
python -m build
python -m twine upload dist/myco-0.9.1*
```
