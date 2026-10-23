#!/bin/sh
# Run a repository's own Playwright suite on the node toolchain's Chromium,
# with no `playwright install` and no tracked change.
#
# Beside the repository's configuration it writes playwright.platform.config.ts,
# which extends it: the Chromium projects launch the toolchain's Chromium
# wrapper (headless, every other launch option kept), the other projects are
# left out of the run. The file is hidden with .git/info/exclude, and Playwright
# resolves testDir, outputDir and the reporters against the same directory as
# the repository's own configuration.
#
# Usage: playwright-test.sh [-c <repository config>] [<playwright test args>...]
# Run it from the directory the repository runs `playwright test` in, after its
# dependencies are installed (npm ci).
set -eu

chromium=/opt/kagent/tools/node/bin/chromium
override_name=playwright.platform.config.ts

die() { echo "playwright-test: $*" >&2; exit 1; }

[ -x "$chromium" ] || die "no Chromium at ${chromium}: the agent needs the node toolchain"

config=""
if [ "${1:-}" = "-c" ] || [ "${1:-}" = "--config" ]; then
  [ -n "${2:-}" ] || die "-c needs the repository's configuration file"
  config="$2"
  shift 2
else
  for name in playwright.config.ts playwright.config.mts playwright.config.cts \
    playwright.config.js playwright.config.mjs playwright.config.cjs; do
    if [ -f "$name" ]; then config="$name"; break; fi
  done
  [ -n "$config" ] || die "no playwright.config.* here: run from the directory that holds it, or pass -c <file>"
fi
[ -f "$config" ] || die "${config}: no such file"
dir=$(cd "$(dirname "$config")" && pwd)
base=$(basename "$config")
override="${dir}/${override_name}"

# The repository's Playwright may expect at most one major newer Chromium than
# the toolchain's: a Playwright release is built on the next Chromium, which
# drives the current one, and Alpine's Chromium follows the stable channel.
have=$("$chromium" --version | sed -n 's/^Chromium \([0-9][0-9]*\)\..*/\1/p')
want=$(cd "$dir" && node -e '
  const path = require("path");
  const from = (m, dirs) => require.resolve(m + "/package.json", { paths: dirs });
  let dirs = [process.cwd()];
  try { dirs = [path.dirname(from("@playwright/test", dirs))]; } catch {}
  const core = path.dirname(from("playwright-core", dirs));
  const c = require(path.join(core, "browsers.json")).browsers.find(b => b.name === "chromium");
  console.log(require(path.join(core, "package.json")).version + " " + c.browserVersion);
' 2>/dev/null) || die "the repository's Playwright is not installed: run its install step (npm ci) first, with no \`playwright install\`"
pw_version=${want% *}
want_major=$(echo "${want#* }" | cut -d. -f1)
if [ "$want_major" -gt $((have + 1)) ]; then
  die "the repository's Playwright ${pw_version} expects Chromium ${want_major}; the node toolchain's Chromium is ${have}, too old for it. Run the suite with a Playwright release built on Chromium $((have + 1)) or older, or wait for the toolchain's Chromium to move."
fi

cat >"$override" <<EOF
// Written by the playwright-browser skill (playwright-test.sh); not tracked.
// The repository's configuration, with its Chromium projects on the node
// toolchain's Chromium and every other project left out.
import base from './${base}';

const executablePath = '${chromium}';
const top = base.use ?? {};
const browserOf = (use) => use?.browserName ?? use?.defaultBrowserType;
const isChromium = (use) => (browserOf(use) ?? browserOf(top) ?? 'chromium') === 'chromium';
const onChromium = (use, fallback) => ({
  ...use,
  headless: true,
  launchOptions: { ...(use?.launchOptions ?? fallback), executablePath },
});

let config;
if (!base.projects?.length) {
  if (!isChromium(top)) throw new Error('playwright-test: the configuration runs no Chromium project');
  config = { ...base, use: onChromium(top) };
} else {
  const byName = new Map(base.projects.map((p) => [p.name, p]));
  const keep = new Set();
  const add = (p) => {
    if (!p || keep.has(p)) return;
    keep.add(p);
    for (const dep of p.dependencies ?? []) add(byName.get(dep));
    if (p.teardown) add(byName.get(p.teardown));
  };
  base.projects.filter((p) => isChromium(p.use)).forEach(add);
  const left = base.projects.filter((p) => !keep.has(p)).map((p) => p.name ?? '(unnamed)');
  if (left.length && !process.env.PLAYWRIGHT_PLATFORM_LEFT_OUT) {
    console.error('playwright-test: left out, not Chromium: ' + left.join(', '));
    process.env.PLAYWRIGHT_PLATFORM_LEFT_OUT = '1';
  }
  if (!keep.size) throw new Error('playwright-test: the configuration runs no Chromium project');
  config = {
    ...base,
    projects: base.projects
      .filter((p) => keep.has(p))
      .map((p) => (isChromium(p.use) ? { ...p, use: onChromium(p.use, top.launchOptions) } : p)),
  };
}
export default config;
EOF

# Hide it from git, in the exclude file of the checkout it lives in.
if top=$(cd "$dir" && git rev-parse --show-toplevel 2>/dev/null); then
  exclude=$(cd "$dir" && git rev-parse --path-format=absolute --git-path info/exclude)
  rel=${override#"${top}/"}
  mkdir -p "$(dirname "$exclude")"
  grep -qxF "/${rel}" "$exclude" 2>/dev/null || echo "/${rel}" >>"$exclude"
fi

exec npx --no-install playwright test -c "$override" "$@"
