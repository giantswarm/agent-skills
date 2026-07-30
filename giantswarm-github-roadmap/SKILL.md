---
name: giantswarm-github-roadmap
description: How to work with Giant Swarm's GitHub issues and project boards through the "pro" MCP server exposed via muster. Use when asked to query, report on, filter, triage, update fields/labels on, close/reopen, or create roadmap or customer board issues.
---

# Giant Swarm GitHub Roadmap

`pro` is an MCP server (run via **muster**) that exposes two Giant Swarm GitHub
Projects V2 boards to agents. This skill covers querying/reporting, triage and
field updates, and creating issues on those boards.

## The two boards

| Board | `board` value | Project | What it holds | Repositories |
|-------|---------------|---------|---------------|--------------|
| Roadmap Board | `roadmap` (**default**) | #273 | Company quarterly goals, team/SIG/WG issues | `giantswarm/roadmap` (**public**), `giantswarm/giantswarm` (private) |
| Customer Board | `customer` | #345 | Customer-related activities | `giantswarm/<customer-name>` (private) |

The `board` parameter is case-insensitive and defaults to `roadmap`. Any other
value errors out and lists the valid options.

## Three rules to internalize before anything else

1. **Read the schema first — never hardcode field names or option values.**
   Field definitions and the valid single-select option values (Status, etc.)
   are read at runtime from the board's schema resource, because they change on
   GitHub without code changes. At the start of a task, read:
   - `roadmap://schema` or `customer://schema` — fields + valid option values + repo/content policy
   - `roadmap://overview` or `customer://overview` — totals, status distribution, repo distribution (great for reports)

   Retrieve resources via muster's `get_resource` (URI = the `xxx://…` string).
   Filters and `update_issue_field` values must match the schema exactly (the
   server does resolve human-readable names to node IDs, but the *option value*
   must be a real one from the schema).

2. **`itemId` ≠ issue number.** Most tools operate on a **board item ID**
   (returned by `list_issues`), not a GitHub issue number or URL. Get the
   `itemId` from `list_issues` first, then feed it to `get_issue_details`,
   `update_issue_field`, `close_issue`, etc.

3. **Public-repo safety gate.** Writing to public content requires an explicit
   `confirmPublicSafe: true`:
   - `create_issue_in_project` when the repo resolves to **`giantswarm/roadmap`** (public)
   - `close_issue` / `reopen_issue` when a **`comment`** is posted on a public issue

   Only pass `confirmPublicSafe: true` after confirming the content is sanitized
   and contains **no customer-specific or confidential** information. When in
   doubt, target the private `giantswarm/giantswarm` repo instead, or ask.

## Tool cheat sheet

Read: `list_issues`, `get_issue_details`, `list_issue_comments`, `get_issue_timeline`
Write: `update_issue_field`, `update_issue_labels`, `create_issue_in_project`, `add_existing_issue`, `close_issue`, `reopen_issue`, `archive_item`

> Tool names are as `pro` exposes them. When reached through muster they may
> carry a server prefix — if a bare name isn't found, discover the exact name
> with muster's `filter_tools` / `list_tools` (search for `list_issues`,
> `roadmap`, or `board`) and use `describe_tool` for the live schema.

## Workflows

### Querying & reporting

1. Read the relevant `…://schema` (once) so you know the valid filter fields and
   option values; read `…://overview` if you need aggregate counts.
2. Use `list_issues` with the narrowest filters that answer the question:
   - `filters` — map of single-select **field → value** (e.g. `{ "Status": "In Progress" }`)
   - `emptyFields` — array of field names to find items **missing** that value
     (e.g. `["Status"]` to find untriaged issues)
   - plus `repository`, `assignee`, `label`, `state` (`open`/`closed`),
     `keyword`, `updated`, `created`, `closed`, `reason`
3. For detail, call `get_issue_details` per `itemId`; for discussion, batch up to
   **10** item IDs into `list_issue_comments` (use `since` to scope recency); for
   history, `get_issue_timeline`.
4. Report concisely — link issues, group by the field that answers the question,
   and don't dump raw tool output. Prefer GitHub markdown without hard line wraps.

### Triage & field updates

- Move a single-select field: `update_issue_field` with `itemId`, `fieldName`,
  `value` (value must exist in the schema). To empty a field, pass `clear: true`
  instead of `value`.
- Labels: `update_issue_labels` with `addLabels` and/or `removeLabels`
  (at least one required; non-existent labels are rejected).
- Close / reopen: `close_issue` (`stateReason` `completed` [default] or
  `not_planned`, optional `comment`) / `reopen_issue`. Remember the
  `confirmPublicSafe` gate when adding a comment on a public issue.
- Remove from the active board view without deleting the issue: `archive_item`.
- Find triage candidates first with `list_issues` + `emptyFields`, then batch the
  updates.

### Creating issues

1. Decide the repository deliberately:
   - Public roadmap item → `giantswarm/roadmap` (requires `confirmPublicSafe: true`, sanitized content).
   - Internal / anything sensitive → `giantswarm/giantswarm` (private).
   - Customer work → `giantswarm/<customer>` on the `customer` board.
2. `create_issue_in_project` with `repository`, `title`, optional `body`,
   `assignees`, `labels`, `initialStatus` (must be a valid Status from the schema),
   and `board`.
3. To pull an **existing** issue onto a board instead of creating one, use
   `add_existing_issue` with `issueUrl` or `issueNodeId`.

## Conventions

- Read-before-write: confirm the current field values with `get_issue_details`
  before mutating, and report what changed.
- For bulk changes, state the plan (which items, which field → value) before
  executing, and summarize results after.
- Keep the public/private boundary sacred: never leak customer or internal
  detail into a `giantswarm/roadmap` issue or a public comment.

## Links in GitHub issues, PRs, and comments

- GitHub auto-resolves issue and pull request references in Markdown (like ` see #123 `) with a proprietary certain logic. To avoid pointers to the wrong repository, use full issue and pull request URLs in issues, pull requests, and comments.

- GitHub automatically displays useful information for an issue or pull request URL when it's formatted as a list item. For example, this ...

   ```markdown
   - https://github.com/giantswarm/foo/pull/1
   ```

   ... gets resolved to `- <icon> <PR title> foo#1`, with the entire item being linked. The icon indicates the pull request status (open, merged, closed). Likeweise, for an issue URL, the icon shows the issue state (open, closed as done, closed as not planned).

   Make use of this when inserting links into issues, pull requests, comments.

## Images in issues, pull requests, comments

GitHub provides no programmatic way to upload an image for use in an issue, pull request, or comment.
Only users can do this via the GitHub web UI.
