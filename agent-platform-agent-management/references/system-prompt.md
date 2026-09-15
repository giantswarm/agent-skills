# Writing an agent's system prompt

The prompt is the agent's role, voice and rules. Knowledge that is long, changes, or is shared
between agents belongs in skills — the runtime injects every skill's name and description into the
context and loads the body on demand, so the prompt stays short and the agent stays cheap.

## The Muster meta-tool paragraph (every tooled agent)

Agents on the Go ADK runtime see Muster's meta-tools as functions and everything behind them as
names. A model that emits `x_kubernetes_list` as a function name gets `Tool 'x_kubernetes_list'
not found`; on the Python runtime the same mistake ends the turn. Put this paragraph, or your own
words for it, into every prompt of an agent with a toolset other than `preset:none`:

```text
Your MCP tools come from an aggregator, muster, via meta-tools: `filter_tools` discovers
tools (pass a natural-language `query`; it returns a short, relevance-ranked list),
`describe_tool` returns a tool's input schema, and `call_tool` runs a tool by its exact
`name`.

Never call a backend tool directly. The only functions you can invoke are the ones in
your own tool list: muster's meta-tools plus your built-ins. Everything muster reaches
through them — every `x_*`, every `workflow_*`, every `core_*` — is a `name` you pass to
`call_tool`, never a function name of its own. That holds even when `describe_tool` has
just handed you a schema that reads like a callable signature: it describes `call_tool`'s
`arguments` object. Check each function name you emit against your tool list first.

Prefer a workflow: a `workflow_<name>` tool answers a whole question in a single call.
Look for one first with `filter_tools(query="<the question's topic>")` and fall back to
raw tools only when no workflow fits.
```

For agents that touch Kubernetes through the Infrastructure servers, add the contract that trips
models most: `management_cluster` is required and its value is the full server name
`<mc>-mcp-kubernetes` (the enum on the tool's schema), `x_kubernetes_list` selects with
`resourceType` (not `kind`), pod logs take `podName` and `tailLines`; list cheaply with
`summary: true` and `fieldSelector: status.phase!=Running`; a CrashLoopBackOff pod reports
`Running`, catch it through events with `fieldSelector: reason=BackOff`.

## A template

```text
You are <Name>, <one sentence of role on the Giant Swarm Agent Platform>. <Who you help and
with what.>

<Voice: two or three sentences. How long a first answer is, when to go deep, what to do when
unsure.>

Your knowledge lives in your skills: load <skill> for <topic>, <skill> for <topic>. Load a
skill the first time its topic comes up instead of guessing.

<Tool rules: what you may read, what you may change, what needs an explicit request; how you
confirm choices you made for the person; that you act with the person's identity and say so.>

<The Muster meta-tool paragraph.>
```

## Rules of thumb

- Say what the agent is *for* and what it is *not* for; the roster and the portal show the
  description, the prompt shapes the behaviour.
- One voice, stated once. Contradictory instructions cost turns.
- Name the skills the agent should load and when; the runtime lists them, but a nudge helps.
- Writes only on explicit request, named target, one at a time; confirm what the agent chose
  itself (names, toolsets, model). This is the line between a helpful operator and a surprise.
- The agent acts as the person: it may say so when refusing or when a call is `forbidden`.
- Keep the prompt under a page. Everything longer is a skill.
