# ADEC — meeting prep

**Contacts:** [technical lead] (primary) · [director] (existing relationship) · **Target:** [date] · **Prepared:** 25 Sep 2026
**Ask:** 30 minutes. **Goal:** a founding-partner commitment: a letter of intent for a regional licence, conditional on validation, plus access to their gauge, ADCP or buoy records.
**Deck:** `oma-pitch-adec.pptx`, 21 slides (build: `python3 make_adec_deck.py`).

---

## 1. What makes this meeting different

They are not a cold prospect, and they are not an asset owner. Four facts shape everything:

1. **They are a consultancy.** They run their own nearshore models and deliver the client's study. What you sell sits *behind* their work: regional design data, turbidity, climate horizons. Never offer port-scale downscaling to them. That is their business, and offering it turns a supplier into a competitor.
2. **They are a past client.** They know how you work. The opening is the relationship, not the model.
3. **The product does not exist yet.** Today: a 10-year circulation hindcast (2015–2025) and one year of coupled waves (2016). The 40-year record, validated extremes, turbidity climatology and climate horizons are the 2027 build. The deck says so on two slides; say it out loud as well.
4. **The meeting serves the funding case as much as the sale.** A letter of intent or a data-sharing agreement from ADEC is the evidence the business plan for John is missing. Either one makes this meeting a success.

---

## 2. Before the meeting: the email

**Don't cc the director on the first email.** On a first ask, a cc can read as going over the technical lead's head, and it turns a technical conversation into a commercial one before there is anything to decide.

- **Email the technical lead** with the deck as a PDF exported from PowerPoint. Never send the .pptx: the speaker notes travel with it.
- **The same day, send the director a short personal note** (draft below). This keeps the director warm without making them part of the first ask.
- **Get the director into the room before the founding-partner ask.** A letter of intent and a licence are the director's decisions. Aim for the second meeting, or the first if the technical lead suggests it.

### Draft: technical lead

> **Subject:** Gulf design data — would value 30 minutes of your view
>
> Hi [name],
>
> I hope things are well at ADEC. Since we last worked together I've built a
> physics-based model of the whole Gulf: circulation, water level and surge,
> waves, and sediment-driven turbidity. It runs a forecast daily and has a
> ten-year hindcast tested against tide gauges and satellite data. The surge
> in particular holds up well.
>
> Next year I'm turning it into a validated 40-year design-conditions dataset
> for the Gulf, with extremes, a turbidity climatology, and climate horizons at
> 2050 and 2100, extractable at any site in days. Before I fix its scope I'd
> like to understand how consultancies like ADEC source this data today and
> what would actually be useful to you.
>
> A short deck is attached. Could we find 30 minutes in the next few weeks?
>
> Best,
> Giles

### Draft: director

> Hi [name], I hope you're well. I've just written to [technical lead] about a
> Gulf design-data project I'm starting next year that I think could be useful
> for ADEC's work. Once they've had a look, I'd value 20 minutes with you both.
> Deck attached in case it's of interest.

---

## 3. Opening move: the relationship, then "what's changed"

Two minutes on the relationship and what they're working on now. Then slide 2 (*"A model of the whole Gulf, running every day"*). Set up the meeting as research:

> "I'm about to spend six months turning this into a design dataset for the
> Gulf. Before I fix what it covers, I'd rather hear from the people who'd use
> it. I'm not here to sell you something finished, because it isn't."

Saying that disarms the question you would otherwise face at slide 16: "so does this exist or not?" It also makes the founding-partner ask at the end feel natural rather than sprung on them.

**Go through section 01 (the model) quickly.** They are technical, so let them stop you. The chain is mostly there to show that the ocean, waves and sediment come out of one consistent set of runs.

---

## 4. Lead with the surge, not the waves

Waves are what they already buy, and they have a comparator for them. The surge is where you are strongest and where they are probably guessing.

- **Salmiya (slide 13):** r 0.88, RMSE 8.7 cm for the non-tidal residual, event by event.
- **Khalifa (slide 14):** nine years of modelled surge at an Abu Dhabi port, with set-downs below −0.25 m about four times a year. The caption states that there is no UAE gauge in the comparison.

**Slide 14 is your pivot into the data ask.** Say it plainly:

> "The gap in my evidence is a UAE gauge. If you hold one, that's the most
> useful thing you could give me, and the validation would be at your site."

### MERCATOR is deliberately left off

The ports deck's Salmiya slide draws MERCATOR beside CROCO to argue for the operational ensemble. This deck uses a CROCO-only version (gauge against model, r 0.88, RMSE 8.7 cm), because the argument here is design data, not forecasting.

**If they raise CMEMS / GLORYS as the free alternative:**
- **GLORYS, the long-duration reanalysis, saves only daily means.** A daily mean cannot represent a surge peak, so it is not usable for design water levels. ← strongest argument
- **It has no tide and no air-pressure forcing.** The design water level is tide plus surge plus waves, *interacting in shallow water*, at the site.
- **Only a coupled hourly model gives all three together, over 40 years, at the site.**
- Operationally, the forecast does blend our model with MERCATOR's short-range hourly forecast. That's fine to say if forecasting comes up, but it isn't this meeting's product.

**Don't bring up Majis.** The ports deck has it and MERCATOR is clearly stronger there. It is honest and fine to discuss if asked, but it is not your lead.

---

## 5. Questions to ask (discovery)

These questions also supply the market numbers the business plan's sales scenarios lack. **Write the answers down.**

| Question | Why it matters |
|---|---|
| How do you source metocean design conditions today, from whom, and roughly what do you pay per project? | Sets the price and names the incumbent. They may use a commercial hindcast portal, free global reanalysis (ERA5 waves; global tide–surge reanalysis on Copernicus), or run their own regional model |
| How many projects a year need offshore design conditions or boundary data? | Sizes the licence against per-project pricing |
| What do you use for climate-change allowances, and do clients or authorities ask for them? | Tests the climate module's pull |
| Do you have dredging, reclamation or EIA work with turbidity limits? What do you use for background turbidity? | Turbidity as a consultancy product, not only a desal one |
| What gauge, ADCP or buoy records do you hold, where, and for which years? | The UAE validation gap. **Years matter:** see §8 |
| What would the data have to show for you to rely on it in a design basis? | Defines the validation bar in their words, which becomes the letter-of-intent condition |
| What can you buy without a tender, and who approves it? | A licence under that threshold is a six-week decision; above it, twelve months |
| Which model do you run nearshore, and in what format do you want boundary data? | Delivery format; also tells you which incumbent to price against |

---

## 6. Pricing

**Never quote in the first meeting unless asked.** If asked, give a range. Prices appear nowhere in the deck or its notes.

### Rate card

| Item | Price (USD) |
|---|---|
| **Project data**: offshore design conditions, boundary series, skill appendix, one site | 3–8K (floor ~5K) |
| **Design basis**: project data plus climate horizons and a report | 15–25K |
| **Regional licence**: unlimited extractions for ADEC's own projects for a year | **decide before the meeting**; anchor 25–50K/yr |
| **Specialist study**: turbidity or dredge-plume baseline | 20–30K, fixed price |
| **Climate module** attached to a study | 8–15K |
| **Founding rate**: first-year licence | 30–50% off, **only** in exchange for LOI + data access + reference rights |

**The licence anchor.** Price it at roughly 5–10 per-project purchases a year. Their answer to "how many projects a year?" tells you whether 25K or 50K is right. That's another reason to ask before quoting.

**The discount must buy something** (same rule as Engie). If there is no data access and no reference, there is no founding rate, just the list price. Discount scope, never price.

**Never itemise by effort.** "It's a day's work per site" is true internally and fatal externally: the argument is lost permanently. You are selling a 40-year validated record, not an hour's query.

**Structure:** fixed price, never day rate. For studies, milestones 40/30/30. The licence is annual, invoiced up front.

### Licence terms, settled in advance

- Use for ADEC's own projects; project deliverables may include the extracted data the study needs.
- No redistribution of the dataset, and no resale.
- Ocean Motion Analytics keeps the model, the configuration and the dataset.
- **No exclusivity, for any period.** An exclusive licence destroys the build-once, sell-many model the whole business plan rests on.
- Liability capped at the fee; the engineer of record keeps design responsibility.

---

## 7. Sequence the offers: commitment now, licence on validation

The licence can't start until the dataset exists and clears their bar. So the sequence is:

1. **Now: the letter of intent plus data access.** The LOI is *conditional*: "we'll take a founding licence at [rate] if the validation meets [the bar they defined in §5]." That's easy to sign because it costs nothing unless you deliver.
2. **Mid-2027: validation delivered** against their bar, at their stations.
3. **Licence starts.**

**In the meantime, a live project can still be served,** but as a small scoped study from the existing 10-year hindcast, priced as a study. Don't present it as the dataset (see traps).

---

## 8. The likely landing

Expect one of three responses.

### A. "Interesting. Come back when it's built."

This is the most likely. Don't accept it as the end. The point of *now* is that they shape it and it is validated at their stations:

> "That's fair, and I will. But the validation is being designed now. If your
> gauge is in it, the extremes are checked at your site rather than in Kuwait.
> Would you share the record on that basis alone?"

**The minimum acceptable outcome is data access.** It costs them nothing, and it fixes the biggest gap in your evidence.

### B. "Show us it works at our gauge first."

**Do it, as a blind comparison whose price is their data.** This is the Engie playbook, and it's cheaper here because surge is already in the hindcast.

- **Check coverage first.** CROCO water level is hourly for 2015–2025, so a surge comparison at any of their gauges in that window is an extraction, not a compute campaign. **Waves exist only for 2016**, so a wave comparison is only possible if their buoy covers 2016. Don't offer waves until you know.
- **Run it blind.** Deliver the model series at their gauge location before seeing their record, then let them compare. This kills "you tuned it" permanently.
- **Agree the bar in advance** (e.g. residual r and RMSE, and peak error on the N largest events). Otherwise "not good enough" can't be tested.
- **Agree the next step before you run:** the conditional LOI in §7. Without it this is free work with no door at the end.
- **Say what it can't show.** A ~3 km grid at a gauge inside a harbour or behind an island may miss local effects. That is resolution, not physics, and it's exactly where their own nearshore model takes over.

### C. "We have a live project that needs surge and waves now."

That's good news, but scope it honestly:

- It is a **study from the 10-year hindcast**, priced as one, not the dataset.
- **Ten years does not support 1-in-100 design values.** Offer the record, its statistics and a clearly caveated extreme-value fit. Do not provide design extremes from a decade of data (climate plan, decision 2).
- Waves are one year only. For a wave design basis it is too early; say so.

---

## 9. Traps: quick checklist

- ❌ **Letting the dataset sound finished.** "In build, 2027" on the slide; say it again in the room.
- ❌ **Design extremes from 10 years.** Not until the 40-year record exists.
- ❌ **Offering port-scale downscaling.** That's their work. You supply what's behind it.
- ❌ **"One day per site"** or any effort-based pricing.
- ❌ **Exclusivity, even "just for the UAE" or "just for a year."**
- ❌ **Serving both SEVRA and ADEC on the same bid.** The rule is one side per bid. If asked whether you work with other consultancies: yes, non-exclusively. Don't name SEVRA unless asked directly.
- ❌ **A roadmap in writing beyond the deck.** The founding-partner slide says "first half of 2027". That is a dated commitment in writing, and it's acceptable only because the LOI is conditional on delivery. **If the build funding is not secured, change it to "2027"** before sending (§10).
- ❌ **Pitching HAB or chlorophyll.** Turbidity is sediment-driven only.
- ⚠️ **Liability.** No design data leaves before PI cover and a capped-liability clause are in place. An LOI doesn't need either; a licence does.
- ⚠️ **Past engagement.** If the earlier consulting was through a former employer, be clear this is Ocean Motion Analytics' own offer, and check nothing in that engagement's terms touches it.

---

## 10. Before the meeting

- [ ] **Decide the licence price** (§6) and the founding rate. Do it before you're asked.
- [ ] **Decide what to say if asked "is this funded?"** An honest answer is: "It's going ahead in 2027; founding partners shape the scope." Don't claim funding you don't have.
- [ ] **If John's funding is not agreed by the send date,** change "first half of 2027" to "2027" on slides 16 and 20 (`make_adec_deck.py`, rebuild).
- [ ] **Look up ADEC's recent projects.** Pick one Abu Dhabi site they worked on and have its offshore surge statistics from the hindcast ready as a verbal example. Don't put it on a slide.
- [ ] **Know your comparators:** what the free global surge and wave reanalyses give at an Abu Dhabi point, and their resolution. You need the one-sentence difference ready.
- [ ] **Check hindcast coverage** for any gauge or buoy they're likely to name (§8B).
- [ ] **Export the PDF from PowerPoint** and flip through it. The check render was LibreOffice.
- [ ] **Fill in the header:** names and date.

---

## 11. Deck state (`oma-pitch-adec.pptx`, 21 slides)

| # | Slide | Source |
|---|---|---|
| 1 | Title: *Regional ocean data for your Gulf projects* | desal deck, reworded |
| 2 | Since we last worked together: three cards | new |
| 3 | Contents | desal, reworded |
| 4–11 | 01: divider, inputs, grid, circulation, waves, turbidity ×3 | desal, kept as sent |
| 12 | 02 divider | new |
| 13 | Salmiya surge, event by event: gauge against CROCO only (no MERCATOR) | new; figure from `make_water_levels.py --croco-only` |
| 14 | Nine years of surge at Khalifa Port: "no UAE gauge yet" | new, from ports figure |
| 15 | 03 divider | new |
| 16 | A design dataset for the whole Gulf: status stated | desal offering slide, reworded |
| 17 | Design conditions at 2050 and 2100, ready to cite | desal climate slide, reworded; method now "delta (pseudo-global-warming)" |
| 18 | 04 divider | new |
| 19 | Three ways to work together: project data / regional licence / specialist modelling | desal offerings slide, reworded |
| 20 | Founding partner, 2027: what ADEC gets / what we'd ask / where it stands | new |
| 21 | Closing | desal, kept |

- **Speaker notes:** turbidity is framed as dredging and EIA baselines; status caveats are on 10 and 16. No prices anywhere in the deck.
- **Not in the deck, deliberately:** MERCATOR, Majis, the dashboard, subscriptions, port-scale downscaling.
- The deck is built from `oma-pitch-desal-2026-09-23.pptx`. If that file is hand-edited, rebuild and check the shape-id lookups.

---

## The line to remember

Leave with a letter of intent or a gauge record — ideally both. Anything they get before the dataset exists is paid for in data or in commitment, never in more of your time.
