# MYCO.md — minimal-example substrate entry page

> You are an LLM agent reading this at session start. This is a
> minimal example substrate — demonstrating the shape, not holding
> real working content. Everything in this tree is for you.

## What this substrate is

A deliberately-empty Myco substrate carried in the Myco repo's
`examples/minimal/` directory. Real substrates look like this on
day one; as you `myco eat` material in, it grows.

## What to do first

1. Call `python -m myco hunger`. This is R1 of the hard contract.
   On a fresh substrate it reports "substrate quiet; no action
   required" and writes a boot brief to
   `.myco_state/boot_brief.md`.
2. Read [the full Myco README](https://github.com/Battam1111/Myco/blob/main/README.md)
   if you haven't yet. It explains the 19-verb surface + the
   five L0 principles + R1 through R7 of the hard contract.
3. When you have something to capture, call
   `python -m myco eat --content "<your insight>"`.

## What's already here

```
_canon.yaml          contract + identity + write_surface
MYCO.md              this file
notes/raw/           empty (eat populates)
notes/integrated/    empty (assimilate populates)
docs/                empty (fruit populates)
```

## What to do at session end

`python -m myco senesce` before `/compact` or Ctrl+D. That runs
assimilate + `immune --fix` so the next session starts from a
consolidated state.

## Further reading

- Five root principles: [L0_VISION.md](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L0_VISION.md)
- R1-R7 rules: [protocol.md](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L1_CONTRACT/protocol.md)
- Full verb list: [manifest.yaml](https://github.com/Battam1111/Myco/blob/main/src/myco/surface/manifest.yaml)
