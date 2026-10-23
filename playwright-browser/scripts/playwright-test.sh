#!/bin/sh
# Run a repository's own Playwright suite on the node toolchain's Chromium,
# with no `playwright install` and no tracked change.
#
# Beside the repository's configuration it writes an override configuration,
# .playwright.platform-<pid>.config.<ts|mts>, which extends it: the Chromium
# projects launch the toolchain's Chromium wrapper (headless, every other
# launch option kept), the other projects are left out of the run. Playwright
# resolves testDir, outputDir and the reporters against the same directory as
# the repository's own configuration. The file is hidden with
# .git/info/exclude while the run lasts and removed after it.
#
# Usage: playwright-test.sh [-c|--config <repository config>] [<playwright test args>...]
# The suite runs in the configuration's directory, as `playwright test` there
# would, after the repository's dependencies are installed (npm ci): paths in
# the arguments are relative to it.
set -eu

chromium=/opt/kagent/tools/node/bin/chromium
# A Playwright release this many Chromium majors older than the toolchain's
# gets a warning: its protocol client and launch flags may no longer fit.
old_majors=4

die() { echo "playwright-test: $*" >&2; exit 1; }
is_number() { case "$1" in '' | *[!0-9]*) return 1 ;; *) return 0 ;; esac; }

[ -x "$chromium" ] || die "no Chromium at ${chromium}: the agent needs the node toolchain"

# The repository's configuration, wherever -c, --config or --config= stands;
# every other argument goes to `playwright test`.
config=""
n=$#
while [ "$n" -gt 0 ]; do
  arg=$1
  shift
  n=$((n - 1))
  case "$arg" in
    -c | --config)
      [ "$n" -gt 0 ] || die "${arg} needs the repository's configuration file"
      config=$1
      shift
      n=$((n - 1))
      ;;
    --config=*) config=${arg#--config=} ;;
    *) set -- "$@" "$arg" ;;
  esac
done
if [ -z "$config" ]; then
  for name in playwright.config.ts playwright.config.mts playwright.config.cts \
    playwright.config.js playwright.config.mjs playwright.config.cjs; do
    if [ -f "$name" ]; then config=$name; break; fi
  done
  [ -n "$config" ] || die "no playwright.config.* here: run from the directory that holds it, or pass -c <file>"
fi
[ -f "$config" ] || die "${config}: no such file"
# The physical path, as git reports it, so the exclude entry matches.
dir=$(cd "$(dirname "$config")" && pwd -P)
base=$(basename "$config")
cd "$dir"

# The Playwright the suite runs on: @playwright/test -> playwright -> playwright-core.
want=$(node -e '
  const path = require("path");
  const dirOf = (m, from) => path.dirname(require.resolve(m + "/package.json", { paths: [from] }));
  let from = process.cwd();
  for (const m of ["@playwright/test", "playwright"]) {
    try { from = dirOf(m, from); } catch {}
  }
  const core = dirOf("playwright-core", from);
  const c = require(path.join(core, "browsers.json")).browsers.find(b => b.name === "chromium");
  console.log(require(path.join(core, "package.json")).version + " " + c.browserVersion);
') || die "the repository's Playwright is not installed here (${dir}): run its install step (npm ci) first, with no \`playwright install\`"
pw_version=${want% *}
want_major=$(echo "${want#* }" | cut -d. -f1)
have=$("$chromium" --version 2>/dev/null | sed -n 's/^Chromium \([0-9][0-9]*\)[. ].*/\1/p' | head -n 1)
is_number "$have" || die "cannot read the toolchain's Chromium version from \`${chromium} --version\`"
is_number "$want_major" || die "cannot read the Chromium version the repository's Playwright ${pw_version} expects"
# A Playwright release is built on the next Chromium, which drives the current
# one: Alpine's Chromium follows the stable channel, so one major ahead passes.
if [ "$want_major" -gt $((have + 1)) ]; then
  die "the repository's Playwright ${pw_version} expects Chromium ${want_major}; the node toolchain's Chromium is ${have}, too old for it. Run the suite with a Playwright release built on Chromium $((have + 1)) or older, or wait for the toolchain's Chromium to move."
fi
if [ "$want_major" -lt $((have - old_majors)) ]; then
  echo "playwright-test: warning: the repository's Playwright ${pw_version} is built on Chromium ${want_major}, the node toolchain's Chromium is ${have}: a protocol error in the run may be this mismatch, not the test" >&2
fi

case "$base" in
  *.mjs | *.mts) ext=mts ;;
  *) ext=ts ;;
esac
override_name=".playwright.platform-$$.config.${ext}"
override="${dir}/${override_name}"
trap 'rm -f "$override"' EXIT
trap 'exit 130' INT TERM

cat >"$override" <<EOF
// @ts-nocheck
// Written by the playwright-browser skill (playwright-test.sh) for one run;
// not tracked, removed after it. The repository's configuration, with its
// Chromium projects on the node toolchain's Chromium and every other project
// left out.
import base from './${base}';

const executablePath = '${chromium}';
const top = base.use ?? {};
// Playwright merges a project's use over the top-level one, and browserName
// beats a device's defaultBrowserType.
const browserOf = (use) =>
  use?.browserName ?? top.browserName ?? use?.defaultBrowserType ?? top.defaultBrowserType ?? 'chromium';
const isChromium = (use) => browserOf(use) === 'chromium';
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
  const add = (p, from) => {
    if (!p || keep.has(p)) return;
    if (!isChromium(p.use)) {
      throw new Error('playwright-test: project ' + (p.name ?? '(unnamed)') + ' (' + browserOf(p.use) + ') is a dependency of the Chromium project ' + from + ', and the node toolchain has only Chromium');
    }
    keep.add(p);
    for (const dep of p.dependencies ?? []) add(byName.get(dep), p.name);
    if (p.teardown) add(byName.get(p.teardown), p.name);
  };
  base.projects.filter((p) => isChromium(p.use)).forEach((p) => add(p, p.name));
  const left = base.projects.filter((p) => !keep.has(p)).map((p) => p.name ?? '(unnamed)');
  if (left.length && !process.env.PLAYWRIGHT_PLATFORM_LEFT_OUT) {
    console.error('playwright-test: left out, not Chromium: ' + left.join(', '));
    process.env.PLAYWRIGHT_PLATFORM_LEFT_OUT = '1';
  }
  if (!keep.size) throw new Error('playwright-test: the configuration runs no Chromium project');
  config = {
    ...base,
    projects: base.projects.filter((p) => keep.has(p)).map((p) => ({ ...p, use: onChromium(p.use, top.launchOptions) })),
  };
}
export default config;
EOF

# Hide it from git while the run lasts, in the exclude file of its checkout.
if top_dir=$(git rev-parse --show-toplevel 2>/dev/null); then
  exclude=$(git rev-parse --git-path info/exclude)
  case "$exclude" in /*) ;; *) exclude="${dir}/${exclude}" ;; esac
  rel=${dir#"${top_dir}"}
  entry="${rel}/.playwright.platform-*.config.*"
  mkdir -p "$(dirname "$exclude")"
  grep -qxF "$entry" "$exclude" 2>/dev/null || echo "$entry" >>"$exclude"
fi

npx --no-install playwright test -c "$override_name" "$@"
