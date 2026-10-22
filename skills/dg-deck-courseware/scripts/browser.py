"""Resolve Chrome/Chromium for the Playwright scripts in this skill.

Order: an explicit path, the CHROME environment variable, a system Chrome or
Chromium on PATH, then None so Playwright uses the browser from
`playwright install chromium`.
"""
import os
import shutil


_CANDIDATES = (
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
)
_NAMES = ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser')


def resolve_chrome(explicit=None):
    if explicit:
        return explicit
    env = os.environ.get('CHROME')
    if env:
        return env
    for path in _CANDIDATES:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    for name in _NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def launch_chromium(playwright, chrome=None, args=None):
    launch_args = ['--no-sandbox']
    if args:
        launch_args.extend(args)
    kwargs = {'args': launch_args}
    if chrome:
        kwargs['executable_path'] = chrome
    return playwright.chromium.launch(**kwargs)
