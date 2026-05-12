"""Tests for v0.6.0 MCP capability surface modules.

Covers: surface.mcp_resources, mcp_prompts, mcp_sampling, mcp_auth,
and surface.capability.
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

from myco.boundary.surface import (
    capability,
    mcp_auth,
    mcp_prompts,
    mcp_resources,
    mcp_sampling,
)

# ---------------------------------------------------------------------------
# mcp_resources
# ---------------------------------------------------------------------------


def _ctx_with_root(root: Path):
    """Minimal MycoContext-shaped object.

    v0.8.4 root-cleanup (2026-05-12): mcp_resources now accesses
    ``ctx.substrate.paths.notes`` (the canon-configurable notes dir).
    The fake ctx needs a SubstratePaths instance with default
    ``notes_dir="notes"`` so fixture-substrate tests behave as before.
    """
    from myco.core.paths import SubstratePaths

    return SimpleNamespace(
        substrate=SimpleNamespace(root=root, paths=SubstratePaths(root=root)),
    )


def test_uri_schemes_are_stable():
    schemes = mcp_resources.URI_SCHEMES
    assert "myco://canon" in schemes
    assert "myco://contract" in schemes


def test_list_resources_with_canon(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.list_resources(ctx)
    uris = {r["uri"] for r in out}
    assert "myco://canon" in uris


def test_list_resources_with_contract(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    cdir = tmp_path / "docs" / "architecture" / "L1_CONTRACT"
    cdir.mkdir(parents=True)
    (cdir / "protocol.md").write_text("# protocol", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.list_resources(ctx)
    uris = {r["uri"] for r in out}
    assert "myco://contract" in uris


def test_list_resources_with_integrated(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    integ = tmp_path / "notes" / "integrated"
    integ.mkdir(parents=True)
    (integ / "n_test.md").write_text("# test", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.list_resources(ctx)
    uris = {r["uri"] for r in out}
    assert any(u.startswith("myco://notes/integrated/") for u in uris)


def test_list_resources_with_primordia(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    pri = tmp_path / "docs" / "primordia"
    pri.mkdir(parents=True)
    (pri / "v0_x_craft_2026-01-01.md").write_text("# craft", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.list_resources(ctx)
    uris = {r["uri"] for r in out}
    assert any(u.startswith("myco://docs/primordia/") for u in uris)


def test_read_resource_canon_redacted(tmp_path: Path):
    canon_text = """schema_version: '2'
identity:
  substrate_id: "test"
  federation_peers: ["secret-internal-url"]
  tags: ["secret-tag"]
system:
  governance:
    secret: "shh"
  resource_redaction:
    paths:
      protected:
        - "identity.federation_peers"
        - "identity.tags"
        - "system.governance"
"""
    (tmp_path / "_canon.yaml").write_text(canon_text, encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://canon", scope="protected")
    # Either redacted or content was emitted in scope='private' mode
    # which is the test's protected default — but read_resource defaults
    # to protected, applying paths.protected redaction.
    assert "REDACTED" in out["content"] or "secret-internal-url" not in out["content"]


def test_read_resource_canon_raw_denies_without_scope(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://canon/raw", scope="protected")
    assert "ACCESS DENIED" in out["content"]


def test_read_resource_canon_raw_with_scope(tmp_path: Path):
    (tmp_path / "_canon.yaml").write_text("schema_version: '2'\n", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://canon/raw", scope="private")
    assert "schema_version" in out["content"]


def test_read_resource_contract(tmp_path: Path):
    cdir = tmp_path / "docs" / "architecture" / "L1_CONTRACT"
    cdir.mkdir(parents=True)
    (cdir / "protocol.md").write_text("# R1-R7", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://contract")
    assert "R1-R7" in out["content"]


def test_read_resource_integrated_note(tmp_path: Path):
    integ = tmp_path / "notes" / "integrated"
    integ.mkdir(parents=True)
    (integ / "n_test.md").write_text("# test note", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://notes/integrated/test")
    assert "test note" in out["content"]


def test_read_resource_primordium(tmp_path: Path):
    pri = tmp_path / "docs" / "primordia"
    pri.mkdir(parents=True)
    (pri / "x.md").write_text("# craft", encoding="utf-8")
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://docs/primordia/x")
    assert "craft" in out["content"]


def test_read_resource_unknown_uri(tmp_path: Path):
    ctx = _ctx_with_root(tmp_path)
    out = mcp_resources.read_resource(ctx, "myco://unknown/whatever")
    assert out["uri"] == "myco://unknown/whatever"


# ---------------------------------------------------------------------------
# mcp_prompts
# ---------------------------------------------------------------------------


def _fake_command(name: str, summary: str = "S", description: str = "D", args=()):
    return {"name": name, "summary": summary, "description": description, "args": args}


def test_list_prompts_includes_workflows():
    cmds = [_fake_command("hunger"), _fake_command("eat")]
    out = mcp_prompts.list_prompts(cmds)
    names = [p["name"] for p in out]
    assert "verb-guide:hunger" in names
    assert "verb-guide:eat" in names
    assert "myco-bootstrap" in names
    assert "myco-contract-r1-r7" in names


def test_list_prompts_with_args():
    cmds = [
        _fake_command(
            "eat",
            args=[
                {"name": "content", "help": "the content", "required": True},
                {"name": "tags", "help": "tag list"},
            ],
        )
    ]
    out = mcp_prompts.list_prompts(cmds)
    eat_guide = next(p for p in out if p["name"] == "verb-guide:eat")
    arg_names = {a["name"] for a in eat_guide["arguments"]}
    assert "content" in arg_names


def test_get_prompt_bootstrap():
    out = mcp_prompts.get_prompt("myco-bootstrap", [])
    assert "messages" in out
    assert len(out["messages"]) > 0


def test_get_prompt_contract():
    out = mcp_prompts.get_prompt("myco-contract-r1-r7", [])
    text = "\n".join(
        m["content"]["text"] for m in out["messages"] if isinstance(m["content"], dict)
    )
    assert "R1" in text


def test_get_prompt_verb_guide():
    cmds = [_fake_command("hunger", description="Hunger description")]
    out = mcp_prompts.get_prompt("verb-guide:hunger", cmds)
    assert "messages" in out
    assert any(
        "Hunger description" in m["content"]["text"]
        for m in out["messages"]
        if isinstance(m.get("content"), dict)
    )


def test_get_prompt_unknown():
    out = mcp_prompts.get_prompt("does-not-exist", [])
    assert "Unknown prompt" in out["description"]


# ---------------------------------------------------------------------------
# mcp_sampling
# ---------------------------------------------------------------------------


def test_should_advertise_sampling_forbidden():
    assert mcp_sampling.should_advertise_sampling({"llm_policy": "forbidden"}) is False


def test_should_advertise_sampling_opt_in():
    assert mcp_sampling.should_advertise_sampling({"llm_policy": "opt-in"}) is True


def test_should_advertise_sampling_default():
    """No llm_policy field → defaults to forbidden."""
    assert mcp_sampling.should_advertise_sampling({}) is False


def test_request_sampling_function_signature():
    """Just ensure the function is callable/coroutine — no real LLM call here."""
    import inspect

    assert inspect.iscoroutinefunction(mcp_sampling.request_sampling_completion)


# ---------------------------------------------------------------------------
# mcp_auth
# ---------------------------------------------------------------------------


def test_redact_in_logs_bearer_token():
    msg = "Bearer abcdef0123456789abcdef0123456789"
    out = mcp_auth._redact_in_logs(msg)
    assert "REDACTED-TOKEN" in out


def test_redact_in_logs_access_token():
    msg = 'access_token="abcdef0123456789abcdef0123456789"'
    out = mcp_auth._redact_in_logs(msg)
    assert "REDACTED-TOKEN" in out


def test_redact_in_logs_no_token():
    msg = "regular log line, nothing sensitive"
    assert mcp_auth._redact_in_logs(msg) == msg


def test_clear_token_after_call_dict():
    holder = {"access_token": "secret", "other": "keep"}
    mcp_auth._clear_token_after_call(holder)
    assert holder["access_token"] is None
    assert holder["other"] == "keep"


def test_clear_token_after_call_object():
    class _Session:
        access_token = "secret"
        other = "keep"

    s = _Session()
    mcp_auth._clear_token_after_call(s)
    assert s.access_token is None
    assert s.other == "keep"


def test_clear_token_after_call_none():
    mcp_auth._clear_token_after_call(None)  # no exception


def test_validate_aud_claim_str():
    assert mcp_auth.validate_aud_claim({"aud": "myco"}, "myco") is True
    assert mcp_auth.validate_aud_claim({"aud": "other"}, "myco") is False


def test_validate_aud_claim_list():
    assert mcp_auth.validate_aud_claim({"aud": ["a", "myco"]}, "myco") is True
    assert mcp_auth.validate_aud_claim({"aud": []}, "myco") is False


def test_validate_aud_claim_missing():
    assert mcp_auth.validate_aud_claim({}, "myco") is False


def test_ensure_pkce_method_s256():
    assert mcp_auth.ensure_pkce_method("S256") is True
    assert mcp_auth.ensure_pkce_method("plain") is False
    assert mcp_auth.ensure_pkce_method(None) is False


def test_oauth_provider_dataclass_default():
    p = mcp_auth.MycoOAuthProvider(
        issuer_url="https://x", audience="a", jwks_url="https://x/jwks"
    )
    assert p.refresh_token_rotation_grace_seconds == 30
    assert p.token_redaction_required is True
    assert p.pkce_required_method == "S256"


def test_configure_logging_redaction():
    logger = logging.getLogger("test_myco_redact")
    mcp_auth.configure_logging_redaction(logger)
    assert any(f.__class__.__name__ == "_RedactFilter" for f in logger.filters)


# ---------------------------------------------------------------------------
# capability protocol
# ---------------------------------------------------------------------------


def test_default_capabilities_returns_four():
    caps = list(capability.default_capabilities(manifest=None))
    assert len(caps) == 4
    ids = [c.capability_id for c in caps]
    assert "tools" in ids
    assert "resources" in ids
    assert "prompts" in ids
    assert "sampling" in ids


def test_tool_capability_register_noop():
    cap = capability.ToolCapability(manifest=None)
    cap.register(server=None, ctx=None)


def test_resource_capability_register_noop():
    cap = capability.ResourceCapability()
    cap.register(server=None, ctx=None)


def test_prompt_capability_register_noop():
    cap = capability.PromptCapability()
    cap.register(server=None, ctx=None)


def test_sampling_capability_skips_when_forbidden():
    cap = capability.SamplingCapability()
    ctx = SimpleNamespace(
        substrate=SimpleNamespace(
            canon=SimpleNamespace(system={"llm_policy": "forbidden"})
        )
    )
    # Should not raise when forbidden.
    cap.register(server=None, ctx=ctx)


def test_sampling_capability_with_opt_in():
    cap = capability.SamplingCapability()
    ctx = SimpleNamespace(
        substrate=SimpleNamespace(
            canon=SimpleNamespace(system={"llm_policy": "opt-in"})
        )
    )
    cap.register(server=None, ctx=ctx)


def test_sampling_capability_with_allow_when_forbidden():
    cap = capability.SamplingCapability(allow_when_forbidden=True)
    ctx = SimpleNamespace(
        substrate=SimpleNamespace(
            canon=SimpleNamespace(system={"llm_policy": "forbidden"})
        )
    )
    cap.register(server=None, ctx=ctx)


def test_sampling_capability_handles_broken_ctx():
    cap = capability.SamplingCapability()
    cap.register(server=None, ctx=None)  # no exception
