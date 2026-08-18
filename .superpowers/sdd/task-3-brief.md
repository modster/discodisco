### Task 3: Docs — spec + glossary

**Files:**

- Modify: `docs/spec.md`
- Modify: `CONTEXT.md`

- [ ] **Step 1: Update `docs/spec.md`**

In §1 Architecture, change the stepper line to reflect a static ball with a
comet chase. In §5 Mapping laws, replace the "BPM → stepper" law with a "BPM →
chase speed" law. In §8 build order step 6, note the light-rotation change.

- [ ] **Step 2: Update `CONTEXT.md`**

Add a term for the comet chase:

```markdown
**Comet chase**: The light-only rotation effect — a bright head LED with a
fading trail that chases around the LED ring, driven by BPM. Replaces the
stepper for rotation. _Avoid_: spinner, rotator
```

- [ ] **Step 3: Commit**

```bash
git add docs/spec.md CONTEXT.md
git commit -m "docs: document light-only rotation (comet chase)"
```

