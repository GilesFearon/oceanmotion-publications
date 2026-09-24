# Engie — meeting prep

**Contacts:** Latifa, Mohamed · **Target:** week of 5 Oct 2026 · **Prepared:** 23 Sep 2026
**Ask:** 30 minutes. **Goal:** a scoped, paid site characterisation study at one intake.

---

## 1. What makes this meeting different

They are not a cold prospect. Three facts shape everything:

1. **Prior relationship via Foresea**, where the work was part-funded by Engie and not refunded. They know how that ended.
2. **They independently assessed the hindcast T and S and judged it not good enough.** This is the single most important fact in the room.
3. **Turbidity is new.** It has never been put in front of them, and it is the only thing here with no comparator.

They are a *qualified evaluator* — most prospects cannot tell you whether your model is any good, and these ones ran their own check. That cuts both ways, and it is mostly an advantage: a pass here means something, and the bar is knowable.

---

## 2. Opening move — own the assessment in the first two minutes

Non-negotiable. If they remember and you did not raise it, you look like you hoped they had forgotten — which costs more than the original result. If they raise it first, you spend the meeting reacting.

> "Before anything else — your team ran an independent check on the hindcast T and S and it didn't clear your bar. I know. I've spent a fair part of the last year on the specific reasons why, and I'd like to tell you what I think they were."

Then **ask for their assessment**: what they measured, against what record, and what would have counted as passing. This is free, specific, third-party data, it defines the bar for everything that follows, and asking proves you are not afraid of it.

---

## 3. Lead with turbidity — do not re-enter through T and S

"Prove it's good enough" is a T/S argument: a variable they measure, hold records for, and have already judged you on. You cannot win it quickly and you should not try.

Turbidity has **no incumbent** — no alternative product, no existing forecast, possibly no measurements. There is nothing for "good enough" to be relative to except a satellite that sees only the surface.

**The technical separation you are entitled to make** (state it plainly, do not overclaim):
bed stress is driven by waves and near-bed currents — wind, bathymetry, orbital velocity — not by how well the model reproduces thermohaline structure. The variable they assessed and the variable you are here about fail for **different reasons**. Related, not unrelated.

---

## 4. The T/S answer — and one trap

Name the causes as **diagnosis, not promises**. No dates, no commitments. An unbuilt roadmap recited to a client becomes a debt.

- **Better bathymetry — the one worth spending on.** Near-bed orbital velocity is strongly depth-sensitive, so it serves turbidity *and* coastal T/S from one piece of work. Already the v1.1 headline in `publication-assets.md`.
- **Wind bias correction** — the cheap second.
- **SST data assimilation — do not promise this.** `business-model.md` deferred it deliberately: it improves the lowest decision-value variable, is weakest exactly at shallow coastal intakes, does nothing for turbidity, and makes ops stateful and fragile. Letting an old client objection set the roadmap is the mistake here.

**The real answer to their T/S objection is the learned point correction against their own sensor** — now slide 22. Their criticism and your newest slide are the same conversation. Cheaper, better for *their* number, and it creates the data-sharing incentive.

---

## 5. Questions to ask (discovery)

| Question | Why it matters |
|---|---|
| Can you share your assessment — what you measured, against what? | Defines the bar; free third-party spec |
| Do you hold intake sensor records — NTU or temperature — and how far back? | Decides whether the correction is live; you need this data anyway |
| Where exactly are the plants you care about? | Nest sharing drives multi-site pricing. Gulf of Oman = different domain, not a nest |
| What's your delegated authority threshold — the value a manager can approve without tender? | Frequently the difference between 6 weeks and 12 months. A tender is lost to PRDW on brand |
| What thresholds do your operators actually act on, and in what units? | Feeds the dashboard and proves you build around them |

---

## 6. Pricing

**Anchors** (`business-model.md`): hindcast study desal **$20–30K** · subscription **$60–100K/yr/plant** · first reference client **30–50% off in exchange for case-study and reference rights**.

**Their $20K comparator is a desktop analysis from public data.** That is the commodity floor, and it is good news: a budget line exists, a procurement path exists, and the threshold is at least $20K.

**Do not match it. Use it as the discount anchor:**

> "List for this is $30K. For a first reference client it's $20K — what you'd pay for a desktop study. Except it isn't one."

**The discount must buy something.** If they will not give reference rights, there is no discount — just a smaller scope. Discount scope, never price.

**Structure:** fixed price, never day rate. Milestones 40/30/30.

### What a public-data desktop study cannot do

- GLORYS at 1/12° (~8 km) — the nearest wet cell may be kilometres offshore in different depth. It is not their intake.
- **It is daily means.** The Jan 2022 event went wind-peak to brown water in 12 hours. A daily mean *cannot* represent it in principle. ← strongest argument
- ERA5 at 0.25° understates shamal peaks and smears land–sea contrast.
- No tides, no wave–current interaction, no nesting.
- **No turbidity at all.** There is no public sediment product.
- Surface-weighted; their intake draws from depth — "the smaller half."

### Multi-site rate card

| Item | Price |
|---|---|
| Site 1 | $30K list → ~$20K reference terms |
| Additional site, same nest | $10–12K |
| Additional site, own nest | $18–20K |
| Additional location — data + QC + technical note only | $5–8K (≈$5K admin floor) |
| Outside the domain (e.g. Gulf of Oman) | Quoted separately as a domain build — never on spec |

Three southern-Gulf sites ≈ **$40–45K** with reference terms.

**Put additional-location pricing on the rate card in the first proposal** so it is never negotiated ad hoc. **Never itemise by effort** — "it's only a day's work" loses the argument permanently.

**Add a deliverable instead of discounting harder:** with 2–3 sites you can rank their intakes by exposure, event frequency and duration. A portfolio question no single report answers and nobody else can produce.

**Phase it.** Agree the rate card for all sites up front, deliver **site 1 first**, then exercise the rest. At one day a week, reputation with client #1 is the whole asset.

---

## 7. Sequence the offers — study before pilot

Their objection is accuracy. A free dashboard pilot **cannot** resolve accuracy — no events, no benchmark. The hindcast study can, against their own records, and it is paid.

**Rung 1 (paid study) → Rung 2 (dashboard subscription).** The pilot becomes the cheap bridge afterwards, because the study already produced the configuration. This is a deliberate departure from the desal-is-subscription-first default, justified because the relationship needs proof before it can carry a recurring commitment.

**On the dashboard:** two co-design sessions are now on slide 21. Bounded by *sessions*, not satisfaction. Say the line once, early and lightly:
choosing variables, depths, thresholds, units, alarm rules, layout = design, included.
Historian/SCADA integration, alarm routing, SSO = a build, and that is the paid engagement.

---

## 8. The likely landing — a blind validation at an existing site

Expect: *"We want a study at a new site, but first show us how good turbidity is where we already have data — and we won't pay upfront."*

**Do it. Not as a taster — as a bounded blind test whose price is their data.**

You need the two seasons more than they need the free run: your entire turbidity calibration rests on one location at 6 m, which `FINDINGS` flags as the standing limitation. A second site materially strengthens Asset 2, your cold-start asset for every other prospect.

**The danger:** a coarse parent run, un-nested, calibrated elsewhere, will likely get timing roughly right and **magnitude wrong** — and magnitude is what they care about. Handed over as "how good my model is," that is a second failed assessment at the same client. Do not let it be framed that way.

**Define what it can prove, before running:**

> "Un-nested and un-calibrated at your site, this can show whether the model puts events in the right place at the right time. It cannot get absolute NTU right — that's what bathymetry refinement and calibration against your record buy, and that's the study."

**The exit clause — use the precise version:**

> "If the model puts events at the wrong time and the winds and waves themselves check out, then it's the physics and the study won't save it — don't commission it. If the drivers are right but it's missing events at your intake, that's resolution and bathymetry, and that's precisely what the study buys. Either way we'll be able to tell which, and I'll show you the working."

Do **not** say the blunter "if timing fails the study won't save it" — a coarse grid can miss real events purely from resolution, and that *is* fixable. You would be conceding ground you do not have and backpedalling later.

**Run it blind** — deliver before seeing their record, then let them compare. Kills the "you tuned it to match" objection permanently, mirrors the pre-registered event protocol in the Asset 2 plan, costs nothing. (Blind means not seeing *their* data — you can still sanity-check your own output against winds and satellite first.)

**Do not run two continuous seasons.** Coupled WW3 + hourly CROCO + sediment overlap is currently Dec 2021 – Feb 2022. Arbitrary seasons = a compute campaign, not an extraction. **Check coverage before offering anything.** Offer **6–8 events selected before you see their data** — cheaper, and per the Asset 2 reasoning, better evidence than a continuous record.

**Terms to fix before starting:**
1. The data is the price — shared after the comparison if they prefer.
2. The bar, in advance (e.g. flags N of M events with X hours warning). Otherwise "not good enough" is unfalsifiable.
3. One time, time-boxed, named as such.
4. **The next step, priced and agreed before you run.** Without this it is free work with no door at the end.

If they will not share data, will not pay, *and* will not commit to a next step if it passes — there is no trade, and you are benchmarking someone else's procurement. Better to learn that in week one.

---

## 9. Traps — quick checklist

- ❌ Selling a study to improve your own hindcast. Nobody funds a vendor fixing their own product. Sell the **question** (intake exposure at Plant X); the improvements are absorbed, unpriced, unitemised.
- ❌ A second free pilot after "not accurate enough." Round two is paid in money or paid in data — ideally both.
- ❌ Unbounded "good enough." Make them state: good enough for *what decision*, measured *how*, against *what record*.
- ❌ Pricing additional points at marginal cost. You are selling a decade-long calibrated hindcast, not an hour's query.
- ❌ Promising SST DA.
- ❌ A roadmap in writing. **Limitations belong in the deck; roadmaps belong in the room.**
- ❌ Over-committing scope: slide 19 promises 10 years of hourly NTU. You have 3 months coupled. Scope study v1 to a **stratified event sample** (~16 events), not a climatology.
- ⚠️ Seasonality: Gulf turbidity is essentially Nov–Mar. Any pilot judged on live events must be in season, or judged on a hindcast of past winters.

---

## 10. Before the meeting

- [ ] **Verify the ~45 NTU Jan 2022 figure** against `calib_02` mem05 before it goes in the email. A wrong number in the one sentence carrying your credibility is the worst place to have one.
- [ ] **Build the daily-mean figure.** Hourly NTU through the Jan 2022 event, overplotted with the daily mean of the same series — the peak vanishes. ~1 hour's work, and it argues the entire price difference without you making the argument. Nothing about it depends on the model being right.
- [ ] **Check coupled coverage** for any period they are likely to name.
- [ ] **Decide on the Offering 01 bullet** (below) — still open.
- [ ] Replace `[ REPLACE WITH DASHBOARD SCREENSHOT ]` on slide 21.
- [ ] In *your Google Slides version* (not this template): fix `currentS` ×2, "the your outfall", cover-title commas, and replace the roadworks placeholder icon with a caption — `ILLUSTRATIVE — EXISTING PUBLIC VIEW`. The cone reads as "unfinished," not "indicative," and it is the only clipart in the deck.

### Open decision — Offering 01 bullet

Proposed as **bullet 2** on slide 19 (measured to fit, not yet applied):

> — The model is refined to your site first — bathymetry, local forcing, and calibration against whatever you already measure.

Generic on the slide because the deck is a template that goes to other prospects. The Engie-specific half is **verbal**, on that slide:

> "This bullet is the one that matters for you. What your team assessed was the regional hindcast — this step is where the gaps they found get addressed, at your intake specifically. It's included in the study, not billed as a fix."

---

## 11. Deck state (`oma-pitch-desal.pptx`, 25 slides)

- **Slide 21** — added 5th bullet: *"Two design sessions: one before it goes live, one once you have lived with it. After that it is yours to judge."*
- **Slide 22 (new)** — `OFFERING 02 · WITH YOUR DATA` / *"The forecast gets sharper the longer it runs."* Learned point correction (MOS, not "ML"), `WHAT IT NEEDS` spec block, `WHAT THIS WILL NOT FIX` callout. Data governance sits in the spec block, because every callout in this deck is an honest limitation.
- Not yet rendered visually — LibreOffice unavailable. Text fit was verified against the real font metrics, but **eyeball both slides once**.

---

## The line to remember

Free buys the first look. Everything after that is paid in money or paid in data — ideally both, and never in another six weeks of your time.
