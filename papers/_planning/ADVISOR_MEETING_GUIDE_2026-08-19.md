# How to Explain This to Your Advisors

A conversation guide, not just the email. Use this for the actual meeting/call, where they can
push back and you need to respond in real time — the email gets them oriented beforehand, this
is what you actually say.

## Opening move

Don't lead with "here are three papers, please review." Lead with the portfolio story:
*"These three papers form one arc — P1 studies the neuron mechanism, P2 validates a reference
implementation of it, P3 applies it to real control and gets the strongest result. I want to
walk you through where each one stands, what I'm confident about, and where I specifically need
your call."* This frames you as someone managing a program, not asking for a grade — and it's
true, not spin.

## Suggested order: P2 → P1 → P3

Not the numeric order. Reasons:
- **P2 first** because it's your most ready, most defensible paper (91%, every claim
  evidence-backed). Starting with your strongest, most buttoned-up work sets the tone and buys
  credibility for the harder conversations that follow.
- **P1 second** because it's solid and mostly just needs their sign-off on scope (six claims,
  the convres limitation) — a shorter conversation.
- **P3 last** because it's the one with real open decisions (fusion, missing code, venue) and
  benefits from having earned trust in the first two conversations before asking for judgment
  calls on the messier one.

## P2 — what to say

**Lead with**: "This is 91% ready by my own audit — every claim is tied to a specific evidence
file, I can show you any of them." Hand them `P2_RESULTS_AUDIT.md` directly; it's designed to
be read by someone else, not just you.

**Be upfront about**: The TNNLS rejection. Don't wait for them to bring it up — say it yourself:
*"An earlier related draft was rejected by TNNLS for 'practical advantage unclear.' This is a
different contribution — validated infrastructure, not a performance claim — but I want your
read on whether that reframing is enough, or whether we should target a different venue
entirely."*

**Ask them for**: A venue decision. Give them the two options straight: stay in TNNLS-adjacent
territory with an explicit "this is the substrate the rest of the program depends on" framing,
or go to a NEF/Nengo-specific venue where the practical-advantage question doesn't apply. Don't
pre-decide this for them — it's genuinely their call given publication strategy considerations
you may not have full visibility into (their history with the venue, timing, etc.).

## P1 — what to say

**Lead with**: The six claims and the ALIF finding specifically — *"ALIF actually wins two of
the four baseline-shortlist settings, and I kept that in the paper rather than hiding it,
because the story is 'HyperLIF is a strong, state-rich mechanism,' not 'HyperLIF wins
everything.'"* This preempts the most obvious reviewer objection and shows judgment, not just
results.

**Be upfront about**: The convres (deep residual) failure case is real and unresolved, and the
Julia/APEX cross-check is weak in absolute terms. Don't undersell these — say them plainly, then
pivot to why they don't undermine the core claims (the paper already scopes them correctly).

**Ask them for**: Whether six claims is right for one paper, or whether some should move to
supplementary material / a follow-up paper. This is a scope call, not a correctness call — they
may have venue-specific intuition about claim density you don't.

## P3 — what to say (this one needs the most care)

**Lead with the number, but immediately follow with the ladder**: *"+86.7% on CF2, beats a
hand-tuned adaptive baseline, generalizes to Skydio where that baseline fails. But the real
story is the three-step ladder underneath it — fixed is safe, adaptive is provably redundant,
learned is where the performance comes from. Right now that's two separate papers instead of
one, and fusing them is the single highest-leverage thing I can do to make this land."*

**Be upfront about, in this order**:
1. **The missing code.** Say it before they ask: *"The learned-gate result's generating code
   isn't recoverable from this machine or my backup drive. I need to find it — GitHub, another
   old machine, wherever — before this goes to a reviewer who asks for it."* This is the single
   most important thing to flag proactively in this whole conversation. A reviewer finding this
   out themselves is far worse than you naming it first.
2. **The internal contradiction you found and fixed.** Frame it as diligence, not as confessing
   a mistake: *"I found and fixed a place where the intro contradicted the paper's own results
   section — worth mentioning because it means this draft hadn't had a full read-through before,
   so I'd like a fresh pair of eyes on the rest before we send it anywhere."*
3. **Simulation-only for the headline result.** The fixed-decode result has real hardware
   validation; the learned-decode headline doesn't yet. Ask directly whether hardware validation
   is a blocker for submission or can follow in a revision cycle — venue-dependent, and they'll
   know the norms for wherever you're targeting.

**Ask them for**: The fusion plan's 4 open scope questions (venue, hardware-as-pillar,
cross-substrate depth, learned-gate-as-main-result) — hand them `P3_FUSION_PLAN.md` directly and
say *"I don't want to fuse these without your input on these four calls — doing it wrong means
redoing the fusion."* Then the venue question: RA-L/TRO (controls-focused, sidesteps the
learning-systems "practical advantage" framing entirely) versus another attempt at a
learning-systems journal.

## If they ask "why should I trust these numbers"

You have a genuinely strong answer, not a defensive one: every number across all three papers
was checked tonight against raw registries and result files, not just read off the PDF — the
two P1 tables that had gone untraceable for weeks were tracked down to a specific HPC job and
verified by direct aggregation of per-seed data, not eyeballed. Say this plainly if it comes up;
it's true and it's exactly the kind of diligence advisors want to hear happened before, not
after, they're asked to review.

## Closing ask

End with the specific decisions you need, as a short list, not buried in conversation:
1. P2 venue call
2. P1 claim-scope call (keep six vs. trim)
3. P3 fusion go-ahead + the 4 scope questions
4. P3 venue call (RA-L/TRO vs. another learning-systems attempt)

Concrete, answerable asks close meetings faster than open-ended "what do you think."
