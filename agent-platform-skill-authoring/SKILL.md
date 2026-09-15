---
name: agent-platform-skill-authoring
description: Use when asked to write, review, fix or explain a skill for an agent on the Giant Swarm Agent Platform — the SKILL.md frontmatter (agentskills.io), the folder layout with references/, scripts/ and assets/, how a skill reaches an agent (a git commit or an OCI digest pinned on the agent's release), how the runtime loads it (load_skill, load_skill_resource, bash under /skills), and what in a skill breaks an agent's boot.
metadata:
  version: "1.0.0"
---

# Authoring skills

A skill is a folder with a `SKILL.md` and optional resources, written to the agentskills.io
specification (https://agentskills.io/specification). The platform's public skills live in
https://github.com/giantswarm/agent-skills, one directory per skill at the repository root; a
team's skills can live in any git repository or an OCI image.

## The format

```markdown
---
name: my-skill
description: Use when … (the trigger: when should the agent load this? — not a summary)
metadata:
  version: "1.0.0"
---

# Title

Instructions, knowledge, rules. Tables for lookups. Point to references/ for depth.
```

- **Frontmatter fields the runtime knows**: `name`, `description`, `license`, `compatibility`,
  `metadata` (string → string), `allowed-tools`. Since kagent line `0.11.0-gs.11` other fields are
  ignored; on an older line a field such as Claude Code's `user-invocable` or `argument-hint`
  fails the whole agent's boot, so keep to the set above.
- **`name`**: lowercase letters, digits and hyphens, ≤ 64 characters, equal to the directory name;
  unique among the agent's skills (the agent's release may mount it under another `name`).
- **`description`**: ≤ 1024 characters, written for the model: the situations that should make it
  load the skill ("Use when asked to …"). This line and the name are all the agent sees until it
  loads the skill — the trigger has to carry the decision.
- **Body**: instructions, not prose about the topic. Under about 500 lines; longer goes into
  `references/`.
- **Folders**: `references/` (documentation the agent reads on demand), `scripts/` (run with the
  runtime's `bash`), `assets/` (templates, data). Any layout under the skill directory works; the
  three names are the convention the runtime's instructions mention.

## How the runtime uses a skill

Skills are materialised into the golden snapshot at `/skills/<name>` (read-only) when the agent
compiles. At run time the Go ADK runtime:

1. injects every skill's `name` and `description` into the system prompt with the instruction to
   load a relevant skill before acting;
2. offers `list_skills`, `load_skill(name)` (returns the `SKILL.md` body) and
   `load_skill_resource(name, path)` (returns a file from the skill directory, e.g.
   `references/architecture.md`);
3. offers `read_file`, `write_file`, `edit_file` and `bash`, which run in a per-session directory
   (`/tmp/kagent/<session>/`, with `uploads/`, `outputs/` and a `skills` symlink) — `bash` commands
   time out after 30 s, Python after 60 s; a skill's Python modules are importable by skill name
   (`importlib.import_module('skill-name.module')` when the name carries a hyphen).

Consequences for authoring: put the decision-making content in `SKILL.md` and the long tables in
`references/`, name the reference files in `SKILL.md` so the agent knows what to load; a script the
agent should run gets a one-line usage in `SKILL.md`; nothing in a skill can depend on network
access or on files outside `/skills` and the session directory.

## How a skill reaches an agent

The agent's release lists skills, each **pinned**: `{name, path, git: {url, commit}}` with a full
40- or 64-hex commit, or `{name, oci: <ref@sha256:…>}`. The chart refuses a branch, a tag, a short
SHA or an OCI tag. The composers do the pinning: the portal's skills step and agent-manager's
`create_agent`/`update_agent` resolve a `ref` to its head commit at write time (`list_skills` shows
the head of every configured repository; `update_agent` with `refreshSkills: true` re-pins every git
skill to its default-branch head). A GitOps release pins by hand. **A new commit of the skill
repository changes nothing on any agent** until that agent is re-pinned — which is what makes an
agent version reproducible.

Discovery: the portal and agent-manager list every `SKILL.md` of the configured repositories
(`agentPlatform.skills.repositories` in the portal, the same list in agent-manager's
`skillsRepositories`; `https://github.com/giantswarm/agent-skills` on Giant Swarm installations).
A skill in another public repository is still usable — pass its `url` and `path` — it is only not
offered in the wizard.

Private repositories: the boot fetches with git; a GitOps release supplies one read token for all
its private git skills (`skillsGitAuthSecretRef.name`, a Secret in the agent's namespace with key
`token`, rendered as `credentialRef` on every git skill, offered on challenge only). The portal and
agent-manager pass no credential yet, so a private skill chosen there leaves the agent at
`Ready=False ActorTemplatePending` with `could not read Username for 'https://github.com'` in the
golden worker's log.

## Writing a good one

- **Trigger, not summary.** The description answers "when do I load this?".
- **Do not state the obvious.** Say what the model would get wrong without the skill: contracts,
  exact names, gotchas, the order that matters. Cut what it already knows.
- **Progressive disclosure.** Short `SKILL.md` with a table of which reference answers what;
  depth in `references/`.
- **Declarative.** Describe outcomes and constraints; leave tool order and mechanics to the agent,
  except where a specific order is the point (the Muster `call_tool` contract).
- **One skill, one topic.** Several small skills load cheaper than one large one; the agent loads
  only what the question needs.
- **Stable names.** Renaming a skill or a reference file breaks the agents pinned to it only when
  they re-pin; still, treat names as an interface.
- **Public content only** in a public repository: no customer names, no internal hostnames beyond
  the platform's own, no credentials.
- **Check the frontmatter** parses as YAML with `name` and `description` present; the runtime
  reports a `SKILL.md` it cannot parse and the agent does not boot.

## Reviewing a skill: the checklist

1. Frontmatter: only known fields; `name` = directory; description is a trigger under 1024 chars.
2. Body loads in one read and tells the agent which reference to open for what.
3. Every fact the agent must get exactly right (a name, an argument, a URL) is stated exactly once.
4. Nothing requires network, a shell outside the session directory, or a tool the agent's toolset
   does not include.
5. Pin: the agent's release points at a commit that contains this version.
