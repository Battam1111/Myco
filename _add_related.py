"""Add Related sections to 24 orphaned notes."""
import os

edits = {
    'n_20260410T231817_1108.md': [
        ('n_20260412T064100_45e3.md', 'Wave 33 decisions — auto-excretion prune design', 'prune uses excrete_reason enforced by L10'),
        ('n_20260412T030457_6717.md', 'Wave 27 — Forward Compression primitive design craft', 'compression doctrine this rule supports'),
        ('n_20260412T232248_6396.md', 'Compressed synthesis — compression design + nomenclature', 'compression pipeline context'),
    ],
    'n_20260410T231817_1ee2.md': [
        ('n_20260410T231817_5405.md', 'Zero-friction capture > careful taxonomy', 'shared philosophy: event-driven design over rigid structure'),
        ('n_20260412T231239_eeb6.md', 'Time threshold correction: 1 day = new, not 7 days', 'same anti-calendar-time principle applied to thresholds'),
        ('n_20260412T233541_e3c9.md', 'Compressed synthesis — founding design decisions', 'event-driven design philosophy origin'),
    ],
    'n_20260411T001033_9976.md': [
        ('n_20260412T232151_e1a7.md', 'Compressed synthesis — protocol + friction + meta', 'protocol enforcement evolution after v1.0'),
        ('n_20260410T231817_126a.md', 'Meta-lesson: never skip attack phase', 'protocol design debate that preceded v1.0'),
        ('n_20260412T233531_a72c.md', 'Compressed synthesis — identity + architecture + agent-first', 'structural enforcement doctrine this protocol embodies'),
    ],
    'n_20260411T172204_5d39.md': [
        ('n_20260411T172204_a79d.md', 'Upstream: Myco template migration guide friction', 'sibling upstream bundle from same ASCC absorption'),
        ('n_20260411T173125_f153.md', 'Wave 9 Upstream Absorb Craft ACTIVE', 'the craft session that absorbed this bundle'),
        ('n_20260412T232151_e1a7.md', 'Compressed synthesis — protocol + upstream + wave9', 'upstream friction synthesis'),
    ],
    'n_20260411T172204_a79d.md': [
        ('n_20260411T172204_5d39.md', 'Upstream: L1 Reference Integrity scanner friction', 'sibling upstream bundle from same ASCC absorption'),
        ('n_20260411T173125_f153.md', 'Wave 9 Upstream Absorb Craft ACTIVE', 'the craft session that absorbed this bundle'),
        ('n_20260412T232151_e1a7.md', 'Compressed synthesis — protocol + upstream + wave9', 'upstream friction synthesis'),
    ],
    'n_20260411T181616_8ea3.md': [
        ('n_20260411T180646_3875.md', 'L14 forage orphan-check blind to directory subtrees', 'sibling wave9 forage friction'),
        ('n_20260412T232151_e1a7.md', 'Compressed synthesis — protocol + friction + wave9', 'wave9 friction synthesis context'),
        ('n_20260412T232251_e8ac.md', 'Compressed synthesis — forage + d-layer + prune', 'forage digest pipeline evolution'),
    ],
    'n_20260412T015258_bdf8.md': [
        ('n_20260412T024944_3e32.md', 'Wave 26 landed — Vision Re-Audit + doctrine reconciliation', 'next wave in landing sequence'),
        ('n_20260412T030457_6717.md', 'Wave 27 landed — Forward Compression primitive design', 'subsequent landing in same session'),
        ('n_20260412T232248_6396.md', 'Compressed synthesis — engineering craftsmanship waves', 'hermes absorption wave cluster synthesis'),
    ],
    'n_20260412T093247_885d.md': [
        ('n_20260412T084315_7eb1.md', 'Wave 38 — L19 Lint Dimension Count Consistency', 'preceding lint wave decisions'),
        ('n_20260412T090405_8f76.md', 'Wave 39 — L20 Translation Mirror Consistency lint', 'preceding lint wave decisions'),
        ('n_20260412T100940_0cc7.md', 'Wave 41 — wave-seed lifecycle lint', 'following lint wave in sequence'),
    ],
    'n_20260412T222958_acd9.md': [
        ('n_20260412T223102_9531.md', 'User feedback: maximize throughput, take initiative', 'sibling user feedback on agent behavior'),
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'behavioral constraints these feedback notes feed into'),
        ('n_20260412T182513_f104.md', 'PUA skill installation — agent self-discipline', 'tooling response to agent discipline feedback'),
    ],
    'n_20260412T223102_9531.md': [
        ('n_20260412T222958_acd9.md', 'User feedback: parallel agents improve efficiency', 'sibling user feedback on agent behavior'),
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'behavioral constraints these feedback notes feed into'),
        ('n_20260412T232210_1b63.md', 'Compressed synthesis — agent discipline + dogfood', 'agent discipline synthesis'),
    ],
    'n_20260412T230456_825b.md': [
        ('n_20260412T231239_eeb6.md', 'Time threshold correction: 1 day = new, not 7 days', 'specific non-negotiable on time perception'),
        ('n_20260412T234750_7e84.md', 'User 9-point directive — priorities for execution', 'actionable directives from same standards'),
        ('n_20260412T185455_9f03.md', 'Skill injection breakthrough — Agent-First pattern', 'agent-first architecture these standards demand'),
    ],
    'n_20260412T230505_4caf.md': [
        ('n_20260410T231616_b930.md', 'Phase 1 first eaten note', 'dogfood origin — first note that proved the system works'),
        ('n_20260410T231817_3174.md', 'Trigger-condition list > imperative description for MCP tools', 'MCP tool design principle used in this dogfood'),
        ('n_20260412T235228_a071.md', 'evolve.py first production mutation', 'sibling first-production milestone'),
    ],
    'n_20260412T231239_eeb6.md': [
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'parent standard this threshold correction belongs to'),
        ('n_20260412T234750_7e84.md', 'User 9-point directive — priorities for execution', 'sibling user directives'),
        ('n_20260412T232355_fae9.md', 'Automation deployment gaps — user directive', 'sibling feedback on deployment pace'),
    ],
    'n_20260412T232355_fae9.md': [
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'parent standard these gaps violate'),
        ('n_20260412T233805_1219.md', 'Claude Code hooks system reference', 'automation mechanism for closing these gaps'),
        ('n_20260412T234750_7e84.md', 'User 9-point directive — priorities for execution', 'sibling user directives with automation priorities'),
    ],
    'n_20260412T232947_caa1.md': [
        ('n_20260412T232210_1b63.md', 'Compressed synthesis — self-correction + dogfood', 'session learnings feed into self-correction synthesis'),
        ('n_20260412T232151_e1a7.md', 'Compressed synthesis — protocol + retrospective', 'retrospective synthesis context'),
        ('n_20260412T193244_b501.md', 'User 6-point directive gap analysis', 'gap analysis this session reflection responds to'),
    ],
    'n_20260412T233805_1219.md': [
        ('n_20260412T232355_fae9.md', 'Automation deployment gaps — user directive', 'gaps this hooks reference helps close'),
        ('n_20260412T233541_e3c9.md', 'Compressed synthesis — design + automation + CLI', 'automation design context'),
        ('n_20260412T230505_4caf.md', 'MCP server first successful dogfood', 'MCP boot sequence that hooks complement'),
    ],
    'n_20260412T234750_7e84.md': [
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'parent behavioral constraints these directives extend'),
        ('n_20260412T232355_fae9.md', 'Automation deployment gaps — user directive', 'sibling directive on automation'),
        ('n_20260412T235626_8d9e.md', 'Mycelium scope: entire project, not just notes', 'directive #2 expanded here: mycelium is most critical'),
    ],
    'n_20260412T235216_6a75.md': [
        ('n_20260412T235348_f3ea.md', 'Inlet — Mem0 vs Zep vs LangMem comparison', 'competitive landscape: detailed product comparison'),
        ('n_20260412T235252_6d14.md', 'Inlet — Karpathy LLM Wiki architecture', 'competitive landscape: architectural validation'),
        ('n_20260412T232227_2796.md', 'Compressed synthesis — forage digest batch', 'forage synthesis with market positioning context'),
    ],
    'n_20260412T235228_a071.md': [
        ('n_20260412T203459_8dfb.md', 'Metamorphosis plan complete — all phases landed', 'milestone context: evolve.py was part of metamorphosis'),
        ('n_20260412T230505_4caf.md', 'MCP server first successful dogfood', 'sibling first-production milestone'),
        ('n_20260412T233533_5fef.md', 'Compressed synthesis — dogfood + vision + planning', 'dogfood context where self-evolution was deployed'),
    ],
    'n_20260412T235252_6d14.md': [
        ('n_20260412T235348_f3ea.md', 'Inlet — Mem0 vs Zep vs LangMem comparison', 'competitive landscape: product-level comparison'),
        ('n_20260412T235216_6a75.md', 'Inlet — State of AI Agent Memory 2026', 'competitive landscape: market overview'),
        ('n_20260412T232227_2796.md', 'Compressed synthesis — forage digest + Karpathy', 'Karpathy LLM Wiki analysis in forage context'),
    ],
    'n_20260412T235321_7bb5.md': [
        ('n_20260412T235216_6a75.md', 'Inlet — State of AI Agent Memory 2026', 'sibling discovery inlet — memory systems landscape'),
        ('n_20260412T235252_6d14.md', 'Inlet — Karpathy LLM Wiki architecture', 'sibling discovery inlet — strategic architecture'),
        ('n_20260412T230505_4caf.md', 'MCP server first successful dogfood', 'MCP implementation context for roadmap evaluation'),
    ],
    'n_20260412T235348_f3ea.md': [
        ('n_20260412T235252_6d14.md', 'Inlet — Karpathy LLM Wiki architecture', 'competitive landscape: architectural comparison'),
        ('n_20260412T235216_6a75.md', 'Inlet — State of AI Agent Memory 2026', 'competitive landscape: market overview'),
        ('n_20260412T232227_2796.md', 'Compressed synthesis — forage digest + market positioning', 'market positioning synthesis context'),
    ],
    'n_20260412T235626_8d9e.md': [
        ('n_20260412T235707_d4cf.md', 'Mycelium as first-class architectural mechanism', 'design direction that implements this scope correction'),
        ('n_20260412T230456_825b.md', 'User non-negotiable standards', 'parent standards this scope correction serves'),
        ('n_20260412T234750_7e84.md', 'User 9-point directive — priorities for execution', 'directive #7: mycelium is most critical'),
    ],
    'n_20260412T235707_d4cf.md': [
        ('n_20260412T235626_8d9e.md', 'Mycelium scope: entire project, not just notes', 'scope correction this design direction implements'),
        ('n_20260412T233531_a72c.md', 'Compressed synthesis — identity + architecture', 'architecture synthesis context'),
        ('n_20260412T185455_9f03.md', 'Skill injection breakthrough — Agent-First pattern', 'architectural mechanism for auto-injection'),
    ],
}

for fname, links in edits.items():
    path = 'notes/' + fname
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    related = '\n\n## Related\n'
    for target, title, desc in links:
        related += f'- [{title}]({target}) \u2014 {desc}\n'

    content = content.rstrip() + related

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'OK: {fname} -> {len(links)} links added')

print(f'\nDone: {len(edits)} notes edited')
