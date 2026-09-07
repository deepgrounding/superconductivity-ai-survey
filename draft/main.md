---
title: "Mapping Superconductivity Research for AI: A Two-Axis Survey of 10,249 Preprints and Where Machine Learning Can Actually Help"
author:
  - Mingguang Chen
date: 2026-09-07
abstract: |
  PLACEHOLDER -- written last.
bibliography: combined.bib
link-citations: true
---

# Introduction

PLACEHOLDER -- written last, after the body delivers.

# Preliminaries and taxonomy

## Terms this field overloads

A survey that spans nine material families and five modes of work has to fix its
vocabulary first, because several of the terms below carry different meanings in
different corners of the literature.

**Critical temperature.** $T_c$ is quoted from several inequivalent operational
definitions: the onset of a resistive drop, the midpoint of the transition, the
zero-resistance point, and the temperature at which diamagnetic screening appears.
The gap between onset and zero resistance is small in clean conventional samples and
large in inhomogeneous ones, which is exactly where contested claims live. Throughout
this survey we say which definition a reported number uses when the distinction bears
on the claim, and we treat a resistive onset without a magnetic signature as weaker
evidence than the two together.

**Conventional and unconventional.** We use *conventional* to mean pairing mediated
by electron-phonon coupling and describable within Migdal-Eliashberg theory
[@bardeen1957theory], and *unconventional* to mean a gap function that changes sign
or breaks a lattice symmetry, whatever the glue. High-pressure hydrides are therefore
conventional in mechanism while being extreme in $T_c$, and this survey groups them
with the electron-phonon family rather than with the cuprates they are often
headlined against.

**Prediction versus discovery.** A computed structure with a favourable calculated
$T_c$ is a prediction. A material that has been made and measured is a discovery.
Papers routinely use "discovery" for the former, and the AI-for-materials literature
does so more often than the superconductivity literature does. We reserve *discovery*
for the experimental sense and say *predicted candidate* otherwise. This distinction
carries most of the weight in Section 5.

**AI-discovered.** We treat a material as AI-discovered only when a machine-learning
model selected or generated the candidate, the material was subsequently synthesised,
and superconductivity was measured. Weaker uses of the phrase -- a screen that ranked
a known compound highly, or a model that reproduced a $T_c$ after the fact -- are
described as such.

## The two axes

The taxonomy has two axes plus a lens (Figure 1).

**Axis 1, material family**, is what the paper is about: `conv` (conventional and
electron-phonon systems, including high-pressure hydrides), `cuprate`, `febased`,
`nickelate`, `unconv_other` (heavy fermion, ruthenate, organic, noncentrosymmetric
bulk systems), `lowd` (two-dimensional, interface, moiré and kagome systems), `topo`
(topological superconductivity and Majorana platforms), `device` (qubits, detectors,
magnets, cables, circuits), and `general` (material-agnostic theory, formalism and
instrumentation).

**Axis 2, mode of inquiry**, is how the work was done: `theory`, `abinitio`,
`discovery`, `synthesis`, `characterization`. This axis deliberately does not encode
whether a topic is applied. An earlier version of this taxonomy carried a sixth
value, `application`, and it failed a measurement: it mixed *how* the work was done
with *what it was for*, and characterization-versus-application was the single
largest source of disagreement both for keyword rules and for two independently
benchmarked language models. Application context is carried by the `device` family
instead, so a qubit paper is labelled theory, synthesis or characterization like any
other paper.

**The AI lens** applies only to papers that use a machine-learning method in their
own work: `surrogate` (regression and classification models, symbolic regression),
`gnn_potential` (graph networks and machine-learned interatomic potentials),
`generative` (diffusion, VAE, flow models for structures and compositions), `llm`
(language models, agents, literature mining), `nqs` (neural quantum states), and
`autonomous_exp` (self-driving laboratories, closed-loop active learning).

The axes are the contribution of this survey, and Sections 3 through 5 are organised
along them. Section 6 evaluates each cell for what AI can currently do in it.

## Positioning relative to existing surveys

Two bodies of review literature already cover parts of this ground, and neither
covers the join.

The first is per-family physics reviews. Recent examples treat nickelate
superconductivity [@wang2025recent; @zhang2026superconductivity] and the hydride
programme. These are authoritative on mechanism and materials, and they say little
about method infrastructure: what data exists, what is measurable at scale, where a
model could be trained or tested.

The second is machine-learning-for-superconductors reviews. Recent examples survey
materials-informatics approaches to superconductor discovery [@tran2025superconductor],
machine-learning searches for new superconductors [@adiga2025accelerating], AI-driven
high-throughput screening [@gashmard2025ai], and language-model workflows for
extraction and property prediction [@itani2025large; @li2026agentic]. These are
organised by method, and their material scope is dominated by the one task where
tabulated data happens to exist -- predicting $T_c$ from composition.

This survey takes the join as its subject. It maps the whole field onto a
family-by-mode grid, populates that grid from a systematically harvested corpus, and
then asks of each cell what would have to be true for a machine-learning method to
contribute there. The result is a statement about where the opportunities are *not*,
which the method-organised reviews cannot make because they only look where the
methods already are.

## Corpus construction

**Seed harvest.** Every arXiv preprint listed under `cond-mat.supr-con`, as primary
category or cross-list, submitted between 2021-09-01 and 2026-09-07, retrieved month
by month through the arXiv API. This is a systematic, not a keyword, harvest: the
selection criterion is the category label the authors themselves chose. It yields
10,303 records, of which 6,986 carry `cond-mat.supr-con` as primary category and
3,317 are cross-listed from elsewhere. Raw responses are cached per month so the
harvest is reproducible.

**Targeted supplement.** The seed necessarily misses AI-for-materials work that never
touches the superconductivity category. Two supplementary threads were harvested by
keyword: AI applied to superconductivity from adjacent categories, and general
AI-for-materials infrastructure needed for Section 6. These add 691 records tagged
`supplement_t1` and `supplement_t2`. **The supplement is recency-biased by
construction** -- its queries are capped and sorted by submission date -- so it is
excluded from every growth statistic and from Table 1's family-by-mode counts, where
it appears only as a separate column.

**Off-topic filtering.** 745 records were flagged as not about superconductivity and
excluded from all statistics. Within the systematically harvested seed the rate is
254 of 10,303, or **2.5%**, which is this corpus's measured query-bleed. The rate is
far higher in the supplement, as intended: the general AI-for-materials thread was
designed to reach outside the field. After exclusion the working corpus is **10,249
records: 10,049 seed and 200 supplement.**

**Labelling.** Both axes and the AI lens were assigned by a language-model pass over
title and abstract (`gemini-3.5-flash-lite`), after keyword rules were measured and
found inadequate. Agreement with a hand-labelled 150-record stratified sample:

| labels | family | mode of inquiry |
|---|---|---|
| keyword rules | 80.1% | 70.5% |
| language-model pass | 85.6% | 88.4% |

Per-class recall for the model is 96% (theory), 92% (characterization), 92% (ab
initio), 64% (synthesis) and 54% (discovery). The two small classes are the weak
ones, and no claim in this survey rests on their counts alone. The AI lens was
validated separately against 120 hand-labelled records, half drawn from each side of
the rule-based tag: 88% precision and 81% recall on the AI-versus-not decision, 84%
exact agreement on which method.

**Annotator disclosure.** All hand labels were produced by a single annotator. The
figures above are therefore agreement between one human pass and one model pass, not
accuracy against an external ground truth. Corpus, labels, prompts and scripts are
released so that both passes can be re-run and re-scored.

**Citation counts.** Citation data comes from OpenAlex, resolved for 8,280 of the
records. Over a five-year window raw counts favour older work mechanically, so where
this survey ranks papers it ranks by citations per month since submission, and
citation counts for work less than a year old are not read as impact at all.

**Limitations.** The corpus is arXiv-only, so it inherits arXiv's coverage: strong in
theory and condensed-matter experiment, weaker in applied-superconductivity
engineering that publishes in IEEE venues, and blind to unpublished industrial work,
which matters most for the device family. Category self-assignment means a paper
whose authors did not cross-list to `cond-mat.supr-con` is absent from the seed
regardless of content. Labels are single-label where reality is often multi-label: a
paper that grows a crystal and measures it gets one mode, chosen by which the
abstract presents as the contribution.

# Material families

PLACEHOLDER

# Modes of inquiry and their data infrastructure

PLACEHOLDER

# What AI has actually done in superconductivity

## How rare it still is

The first thing the corpus says about machine learning in superconductivity is how
little of it there is. Of the 10,049 on-topic preprints in the systematic seed, **120
use a machine-learning method in their own work: 1.2%.** The count grows -- 13 in
2022, 19 in 2023, 22 in 2024, 38 in 2025 -- but from a base so low that even a
tripling leaves the field's daily practice essentially untouched. A recent review of
computational superconductor discovery reaches the same conclusion from the opposite
direction, describing AI and machine-learning efforts in this field as remaining "in
its infant stage" while the predictive work continues to be carried by
Migdal-Eliashberg theory and its first-principles implementations
[@tran2025superconductor].

The distribution across modes of inquiry is more revealing than the total. Counting
the AI-tagged records across the whole working corpus, seed and supplement together
(Figure 5): 124 theory, 64 discovery, 48 characterization, 16 ab initio, and **1
synthesis.** Machine learning in this field is something that happens to a
calculation or to a dataset, almost never to a furnace.

## Predicting $T_c$, and what the screening pipelines actually deliver

The oldest and densest thread predicts $T_c$ from composition or structure. Its
anchors predate this survey's window: a composition-based classifier and regressor
trained on the SuperCon database [@stanev2018machine], and a widely reused
statistical model built on chemical-formula features [@hamidieh2018data]. Both are
honest about scope. The latter predicts a transition temperature only for materials
already known to superconduct, which is a different problem from finding new ones.

Within the window, the productive form of this thread is not the regressor alone but
the regressor used as a filter in front of density-functional perturbation theory.
The clearest example screens roughly 200,000 metallic compounds on or near the convex
hull with a model trained on about 7,000 electron-phonon calculations, validates the
survivors with first-principles calculations, and reports 545 compounds with $T_c$
above 10 K [@cerqueira2023sampling]. The same group applied the workflow to ambient-
pressure hydrides in a set of more than 150,000 compounds, finding around 50 systems
above 20 K, and reported that most of them sit slightly off the convex hull, so
synthesis would need conditions away from ambient equilibrium
[@cerqueira2024searching]. A companion study screened over a million compounds and
proposed the thermodynamically stable Mg$_2$XH$_6$ family, with X = Rh, Ir, Pd or Pt,
at 45-80 K and above 100 K with electron doping of the platinum compound
[@sanna2023prediction]. A deep-learning framework explored about 36 million ternary
hydride structures across 29 elements and identified 144 candidates above 200 K at
200 GPa, 129 of them new [@wang2025discoverya].

These are substantial results, and they are all predictions in this survey's sense.
None of the four papers reports a synthesised, measured superconductor. What the
machine learning buys is the ratio of candidates examined to calculations run: the
model is a cheap surrogate that lets an expensive but trusted method be pointed
somewhere useful. That is a real contribution, and it is a narrower one than "AI
discovers superconductors" suggests.

## Generative and language-model approaches

Generative models entered the field along the path they took in materials science
generally. An inverse-design workflow combining pre-trained models, diffusion and
first-principles calculation reported 74 dynamically stable materials with
model-predicted $T_c$ at or above 15 K, singling out B$_4$CN$_3$ at 24.08 K under 5
GPa and B$_5$CN$_2$ at 15.93 K at ambient pressure [@han2024invdesflow]. The same
engine later proposed cubic Li$_2$AuH$_6$, with a calculated ambient-pressure $T_c$
near 140 K and a suggested synthesis route from LiAu and LiH [@ouyang2025high].
Again: calculated, not measured.

Language models arrived more recently and in two distinct roles. The first is
extraction. A language-model workflow built an experimental database of 78,203
records covering 19,058 unique compositions from the literature, then fine-tuned
open-source models to classify superconductors, predict $T_c$, and generate
compositions conditioned on a target $T_c$ [@itani2025large]. The fine-tuned models
performed comparably to feature-based baselines and sometimes better; 28% of the
generated compositions were novel; applying the predictors to the GNoME database
[@merchant2023scaling] surfaced unreported candidates above 10 K. The authors label
these candidates unverified, which is the correct description and a rarer one than it
should be.

The second role is orchestration. An agentic framework couples a billion-parameter
atomic model for numerical work to language models for planning, rediscovers 66
experimentally verified superconductors absent from the SuperCon3D database, and
screens 2.4 million equilibrium crystals in 28 GPU hours [@li2026agentic]. It then
does the thing the rest of this literature does not: **four proposed compounds were
synthesised and measured** -- Zr$_3$ScRe$_8$ at $T_c$ = 6.5 K, HfZrRe$_4$ at 5.9 K,
Zr$_4$VRe$_7$ at 3.5 K, and Hf$_{21}$Re$_{25}$ at 2.5 K. These transition
temperatures are low, and that is the point worth holding onto. The one clearly
closed loop in the recent literature closed on compounds an order of magnitude below
the temperatures the screening papers advertise.

The earlier closed-loop demonstration is worth reading alongside it. Four cycles of
prediction, experimental test and retraining more than doubled the success rate of
superconductor discovery, found a new superconductor in the Zr-In-Ni system, and
recovered five superconductors absent from the training data [@pogue2022closed]. Its
lesson is about feedback rather than about model class.

## Neural quantum states and the theory side

The largest AI-tagged mode in the corpus is theory, and within it neural quantum
states are the most self-contained thread. Building on the demonstration that neural
networks can represent many-body wavefunctions [@carleo2017solving], recent work has
pushed the ansatz toward the models superconductivity actually cares about: the
two-dimensional $t$-$J$ model at finite doping [@lange2024simulating], the $t$-$t'$
Hubbard model with symmetry-preserving architectures [@rende2026superconductivity],
and the Hofstadter-Hubbard model at scale [@roth2026large]. This thread is unusual in
the survey because its validation is internal: a variational energy can be compared
against other methods without anyone growing a crystal. That is precisely why it
moves faster than the rest.

## Characterization: the quiet, working case

Characterization is where machine learning is least discussed and most routinely
useful. The pattern is a model that turns an instrument's raw output into a physical
quantity: unsupervised learning of nematicity from scanning-tunnelling data on
magic-angle bilayer graphene [@taranto2022unsupervised], convolutional networks
detecting charge jumps in superconducting qubits in real time
[@gaytanvillarreal2026real], and machine-learned qubit readout deployed on FPGAs for
mid-circuit measurement [@vora2024ml; @otting2026multi]. These papers rarely present
themselves as AI-for-science. They are instrument engineering, they are validated
against a ground truth the instrument already provides, and they work.

## The critical literature

Three strands of criticism bear directly on how the results above should be read, and
a survey that omitted them would misrepresent the field.

The first is about what a computational "discovery" is worth. A perspective on the
GNoME result argued that scaled-up stability prediction had not been shown to yield
the compounds an experimentalist would call new, and questioned how many of the
predicted structures are meaningfully distinct [@cheetham2024artificial]. The second
concerns autonomous synthesis: an analysis of the A-Lab result
[@szymanski2023autonomous] disputed the claim of autonomously discovered novel
materials, arguing that the automated phase identification did not support the
conclusions drawn from it [@leeman2024challenges]. Neither critique says the
programme is worthless. Both say the validation step is where the difficulty lives,
which is the same thing this survey's corpus says about superconductivity
specifically.

The third strand is superconductivity's own reproducibility record, and it is
unusually harsh. Two prominent claims in this field's recent history were retracted:
room-temperature superconductivity in carbonaceous sulfur hydride [@snider2020retracted]
and near-ambient superconductivity in nitrogen-doped lutetium hydride
[@dasenbrock2023retracted]. The LK-99 episode [@lee2023lk99] generated a burst of
replication attempts visible as a spike in this corpus's 2023Q3 activity. On the
theoretical side, first-principles work found no stable near-ambient phase in the
Lu-N-H system capable of supporting high-$T_c$ superconductivity, while identifying
metastable templates at higher pressure [@fang2023assessing]. The relevant point for
this survey is structural: a field whose flagship experimental claims have repeatedly
failed replication is a field where a model's training labels are unreliable in
exactly the high-$T_c$ region where the predictions matter most.

## Assessment

Machine learning in superconductivity is currently a way of making expensive
calculations cheaper and instrument data more usable. It has not yet become a way of
finding superconductors. The evidence for that reading is the shape of the corpus
rather than any single paper: 1.2% penetration in the systematic seed, one AI-tagged
synthesis paper, and exactly one recent closed loop -- delivering compounds at 2.5 to
6.5 K while the screening literature advertises predictions above 200 K. The next
section asks, cell by cell, what would have to change.

# An AI-readiness assessment

## What is being scored, and what it is not

Section 5 described what has happened. This section asks what could. For each cell of
the taxonomy that the survey discusses, Figure 4 scores three properties on a 0-3
scale and names the constraint that currently binds.

**Data availability** asks whether enough machine-readable, labelled data exists to
train or evaluate a model. **Benchmark maturity** asks whether a shared task with an
agreed metric and a held-out set exists, so that two methods can be compared without
re-running each other's pipelines. **Cheap validation** asks what it costs to find
out whether a prediction was right -- a score of 3 means a calculation settles it, a
0 means a hard experiment is required. The **binding bottleneck** names which of
data, compute, theory or experiment is the constraint that would have to move first.

These scores are the author's judgement, not measurements, and they should be read as
a structured argument rather than as data. They are stated on a coarse scale
precisely because a finer one would imply a precision that is not there. The corpus
counts inform them but do not determine them: a cell can be crowded and unready, and
Section 7 argues that several are.

## The three regimes

Read down Figure 4 and the cells sort into three groups.

**Cheap-validation cells, where progress is fastest and already visible.**
Conventional and hydride ab initio work scores highest: the data exists in the form
of hundreds of thousands of electron-phonon calculations, an accepted target quantity
exists in the Eliashberg $T_c$, and a prediction can be checked by running the
calculation the model was trained to approximate. Material-agnostic theory sits
alongside it: a neural quantum state's variational energy is checkable against other
methods on the same Hamiltonian. Both cells are compute-limited rather than
data-limited, and both are where the corpus already shows the most AI activity. This
is not a coincidence, and it is the single strongest regularity in the survey:
**machine learning has penetrated exactly those cells where a machine can grade its
own homework.**

**Data-limited cells, where the obstacle is that measurements are not in a usable
form.** Characterization across cuprates, hydrides, two-dimensional systems and
devices falls here. The raw material is abundant -- decades of ARPES, scanning
tunnelling, transport and neutron data -- but it lives in figures inside PDFs, in
per-group formats, and in supplementary files without schemas. The one recent
large-scale attempt to fix this for superconductivity extracted 78,203 records with a
language-model workflow [@itani2025large], which is both an encouraging result and a
measure of how absent such resources were. Device characterization scores best in
this group because qubit and detector metrology already produces standardised,
high-volume, machine-generated data, which is why the working applications in Section
5 cluster there.

**Experiment-limited cells, where nothing else is the bottleneck.** Every synthesis
cell scores 1, 0, 0. There is no shared dataset of attempted syntheses with their
outcomes, no benchmark, and validation requires making the material. The corpus
carries the corresponding signature: one AI-tagged synthesis paper in 10,249 records.
This is where the general AI-for-materials programme has invested most visibly, in
autonomous laboratories [@szymanski2023autonomous], and where the criticism has been
sharpest [@leeman2024challenges]. Superconductivity makes the problem harder than the
oxide-powder case those systems target: nickelate films require topotactic reduction,
hydrides require diamond anvil cells at hundreds of gigapascals, and moiré devices
require stacking with angular precision. None of these is a pipetting robot's problem.

## Where the theory bottleneck sits

Two cells are labelled theory-limited, and the label means something specific:
additional data would not help, because there is no target quantity a model could
learn to predict. Cuprate theory is the canonical case. Four decades of data have not
produced an agreed mechanism, so there is no equivalent of the Eliashberg function to
regress against. Nickelate ab initio work has the opposite problem in the same
family: the calculations are tractable and increasingly standard, but which
calculated quantity predicts $T_c$ in a multi-orbital correlated system is exactly
what is unsettled.

Machine learning can still contribute in these cells, and the corpus shows how: not
by predicting $T_c$ but by solving the models themselves. Neural quantum states
applied to the $t$-$J$ and Hubbard models [@lange2024simulating;
@rende2026superconductivity] address the theory bottleneck directly, because the
obstacle there is the cost of solving a well-posed problem rather than the absence of
a label.

## What the ranking implies

Ordering the cells by summed score produces a priority list, and it is not the list
the field's activity implies. The highest-scoring opportunities are ab initio
screening, device characterization and material-agnostic theory -- two of which are
barely discussed in the machine-learning-for-superconductors literature, which
concentrates instead on composition-to-$T_c$ regression. The lowest-scoring are the
synthesis cells, which is where AI-for-materials rhetoric concentrates most heavily.

Three consequences follow, and each is a claim that could be checked rather than a
prediction we are confident in.

**Characterization inversion is the most under-exploited opportunity.** Spectroscopic
and microscopy data is abundant, the mapping from spectrum to physical parameter is
well-posed, and validation is cheap because independent measurements of the same
sample exist. What is missing is not method but infrastructure: standardised,
openly-released, labelled spectra. This is a dataset problem that a coordinated effort
could solve in a way that no amount of model development will.

**Synthesis will not yield to autonomous laboratories in this field on the current
design.** The binding constraint is that superconductivity's important syntheses are
extreme-condition and low-throughput. The tractable version of the problem is
narrower and more useful: predicting whether a computationally proposed compound can
be made at all. The screening literature already generates this need -- one study
noted that most of its promising ambient-pressure hydrides sit slightly off the convex
hull [@cerqueira2024searching] -- and a synthesizability model trained on attempted
syntheses, including the failures, would be worth more to that pipeline than another
increment of $T_c$-regression accuracy.

**The field needs a held-out benchmark with experimental resolution.** No cell in
Figure 4 scores 3 on benchmark maturity. The screening papers cannot be compared
against each other, because each reports its own candidate list validated by its own
calculations. A benchmark built from post-2024 experimentally confirmed
superconductors, with predictions time-stamped before confirmation, would separate
methods that generalise from methods that interpolate their training set. The
retraction record [@snider2020retracted; @dasenbrock2023retracted] makes the label
quality problem acute, and therefore makes the benchmark more valuable, not less.

## Assessment

The pattern across Figure 4 is that AI adoption in this field tracks validation cost
far more closely than it tracks either data volume or scientific importance. Where a
calculation can check a prediction, methods have arrived. Where an experiment is
needed, they have not, regardless of how much has been written about the cell. If
that reading is right, the highest-leverage interventions are the unglamorous ones:
release labelled characterization data, build a time-stamped benchmark, and model
synthesizability rather than synthesis.

# Discussion

PLACEHOLDER

# Conclusion

PLACEHOLDER

# Data availability

PLACEHOLDER
