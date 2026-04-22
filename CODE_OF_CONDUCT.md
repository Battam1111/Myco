# Code of Conduct

Myco is a cognitive substrate **for LLM agents**; the human
community around it is small by design (L0 principle 1 —
humans speak natural language to the agent; they don't browse
here). Still, when humans DO interact around this project —
issues, PRs, discussions, security reports — we hold ourselves
to a direct-but-respectful bar.

## The short version

1. **Address the work, not the person.** "This approach breaks
   R6" is fine. "You clearly don't understand R6" is not.
2. **Be specific.** Disagreement is welcome; vague hand-waving
   is not. Name the file, the rule, the test, the exit code —
   whatever anchor the discussion rests on.
3. **Assume the other party has read the doctrine.** Point them
   at the specific L0/L1/L2 page rather than re-explaining it
   from scratch. If they haven't read it, that's OK; link and
   move on.
4. **No bigotry, harassment, threats, or sustained hostility.**
   Zero tolerance. Maintainers will lock threads, remove content,
   and block accounts without warning if the line is crossed.
5. **Credit and name honestly.** If someone surfaces a bug, file
   an audit finding, or ships a fix, record their contribution in
   `CHANGELOG.md` or the relevant security advisory. Don't
   silently absorb other people's work.

## Scope

This applies to every Myco-project surface:

- GitHub issues, pull requests, discussions, advisories
- Any sibling Myco-ecosystem repo (e.g. substrates that depend on
  Myco when their maintainers participate in Myco-upstream threads)
- Community channels (Discord / matrix / mailing list if/when they
  exist; they don't at v0.5.x)

It does not apply to: your own substrate's private channels (your
rules there); your interactions with your LLM agent (that's between
you and the agent); or third-party platforms you post Myco content
to (but don't misrepresent Myco-maintainer positions if you
post there).

## Reporting

- **Security vulnerabilities**: see [`SECURITY.md`](SECURITY.md).
  Those go through the Security Advisory flow, not through
  conduct channels.
- **Conduct concerns**: email the maintainer address in the repo's
  `pyproject.toml` `[project].authors` block with "conduct: " as
  the subject prefix.

## Enforcement

The maintainer (currently Battam1111) is the sole enforcement
authority. Enforcement actions can include: private warning,
thread lock, content removal, account block, ban from future
participation. Decisions are final and are not typically
explained publicly (to protect reporter confidentiality).

If you believe enforcement was unfair, you may state so in a
reply email; the maintainer commits to re-reading it at least
once before leaving the ruling in place.

## Why this code is short

Long codes of conduct become unreadable and unread. This one is
deliberately five lines of substance because humans interact
with Myco rarely and briefly. If interaction volume grows and a
longer code is needed, we'll update via normal governance
(fruit + molt, same as any other change to contract-adjacent
text).

Adapted from the spirit of the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)
and the [Django CoC](https://www.djangoproject.com/conduct/),
but compressed and Myco-specific.
