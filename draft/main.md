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

PLACEHOLDER

# An AI-readiness assessment

PLACEHOLDER

# Discussion

PLACEHOLDER

# Conclusion

PLACEHOLDER

# Data availability

PLACEHOLDER
