---
name: playwright-browser
description: Use when a coding agent should look at a web page in a headless browser — check that a UI it changed renders, read a page's title, text or accessibility tree, click through a flow, take a screenshot and look at it or attach it to a pull request or issue, or run the repository's own Playwright end-to-end tests (`playwright test`). Needs the node toolchain, which carries Chromium and the Playwright CLI.
metadata:
  version: "1.0.0"
---

# A headless browser in the agent's actor

The `node` toolchain carries Chromium and the Playwright CLI under `/opt/kagent/tools/node/bin`:
`playwright-cli` and `chromium`. Without them (`command -v playwright-cli` finds nothing) the agent
has no `node` toolchain mounted; say so instead of installing a browser. Nothing is ever downloaded:
no `playwright install`, no `playwright-cli install`, no `npx playwright install`. The actor has no
route to Playwright's download hosts, and the toolchain's Chromium is the browser.

## The Playwright CLI

`playwright-cli` is configured by the toolchain through its environment, which outranks a
repository's own `.playwright/cli.config.json`: the toolchain's Chromium, headless, Chromium's
sandbox off, service workers blocked. Pass no `--browser`, `--headed`, `--cdp`, `--extension` or a
config naming another browser. The commands and their flags come from `playwright-cli --help` and
`playwright-cli <command> --help`.

```bash
playwright-cli open http://localhost:3000/   # starts the browser, keeps it between commands
playwright-cli eval "document.title"
playwright-cli snapshot                      # the accessibility tree, with refs (e12) for click/fill
playwright-cli click e12
playwright-cli screenshot --filename=/tmp/login.png
playwright-cli close                         # always: Chromium shares the actor's memory
```

## What a page can reach

- A server the agent runs in its own actor on `localhost`: start it in the background, wait until
  it answers (`curl -sf`), then open it.
- An HTTP(S) origin the agent's declared egress allows. Any other origin answers 403 from the
  egress gateway, and a WebSocket to a remote origin is refused.
- Never muster's in-cluster host: the toolchain's `chromium` refuses every name of it, short forms
  included (`ERR_NAME_NOT_RESOLVED`), redirects, workers and a request a Playwright route continues
  too. This holds only while Chromium resolves names itself, so it does not cover an explicit
  proxy (`--proxy-server`, a `proxy` launch option), a launch of another executable, a request
  Node sends (`route.fetch()`, the `request` fixture, `page.request`), or muster's address. Do not reach muster through
  any of them; its tools are the agent's MCP tools.

## Screenshots

Read a screenshot with the Read tool to judge a layout by sight. Show it to the person by attaching
it to the pull request or issue being worked on with gh's `--attach` (`gh pr create|edit|comment`,
`gh issue create|edit|comment`); gh uploads it as the person and references it in the body,
replacing a local path the body already names:

```bash
gh pr comment 42 --attach '/tmp/login.png#The login error state'
```

- The file types, sizes and counts gh takes come from `gh pr comment --help`.
- An upload cannot be undone: attach only what the person should see.
- No `--attach` in `gh pr comment --help` (an older gh), or gh refusing the token (an App
  installation token, `ghs_…`): keep the screenshot to the session and describe it.
- Write screenshots outside the repository (`/tmp`) so they are never committed.

## The repository's own Playwright suite

Install the repository's dependencies as its CI does (`npm ci`, `pnpm install --frozen-lockfile`,
…), then run, from the directory the repository runs `playwright test` in:

```bash
sh <this skill's directory>/scripts/playwright-test.sh [-c <playwright.config.*>] [<playwright test args>...]
```

The suite runs in the configuration's directory, as `playwright test` there would; paths in the
arguments are relative to it. For the run, the script writes `.playwright.platform-<pid>.config.*`
beside the repository's configuration, hidden in `.git/info/exclude` and removed afterwards, so no
file of the repository changes: it extends the repository's configuration, launches the toolchain's
Chromium headless on the Chromium projects (their other launch options kept), and leaves the other
projects (Firefox, WebKit) out of the run, saying which. A non-Chromium project a Chromium project
depends on fails the run, named. Arguments go to `playwright test` (`--project`, `--grep`, a test
file, `--reporter`). It refuses a repository whose Playwright expects a Chromium more than one
major version newer than the toolchain's, naming both, and warns about a much older one; report
that instead of changing the repository's Playwright pin.

Never add an `executablePath` or a platform path to the repository's tracked configuration.
