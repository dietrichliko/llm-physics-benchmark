# ⚛️ llm-physics-benchmark

[![CI](https://github.com/youruser/llm-physics-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/youruser/llm-physics-benchmark/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)

Benchmark local LLMs via **Ollama** on **expert-level particle physics questions** from CMS Data Analysis, ALICE, Belle II, Detector Development, Exotic Atoms, Gravitational Waves, Machine Learning, Precision Experiments, Rare Event Searches, Theoretical Physics, and Historic Activities (DELPHI at LEP, NA48, UA1, NA36), and General Public Outreach.

Measures both:

- **Speed** — tokens/second, time-to-first-token, total response time
- **Quality** — LLM-judge scoring: Accuracy, Completeness, Clarity, Technical Depth

Designed for the **NVIDIA DGX Spark** and consumer-grade GPU setups (RTX 3090 / 4090 etc.).

---

## Repository structure

```text
llm-physics-benchmark/
├── src/llm_physics_benchmark/   # installable package
│   ├── __init__.py
│   ├── cli.py                   # physics-bench entry point
│   ├── report.py                # physics-report entry point
│   ├── client.py                # Ollama HTTP client
│   ├── judge.py                 # LLM-judge scoring
│   ├── runner.py                # benchmark orchestration
│   ├── model_lists.py           # consumer / high-end model lists
│   └── models.py                # dataclasses
├── data/
│   └── physics_qa_bank.yaml     # 70 Q&A pairs (12 topic areas)
├── results/                     # benchmark outputs (gitignored)
├── tests/
│   └── test_benchmark.py
├── .github/workflows/ci.yml
├── pyproject.toml
└── LICENSE
```

---

## Installation

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Ollama](https://ollama.com/) running locally

### Install

```bash
git clone https://github.com/youruser/llm-physics-benchmark
cd llm-physics-benchmark

# Create venv and install (uv handles everything)
uv sync

# With dev dependencies (tests, linting)
uv sync --extra dev
```

---

## Quick start

```bash
# Pull a judge model first (if not already available)
ollama pull qwen2.5:7b

# Run consumer-grade benchmark (models ≤ 12 GB VRAM)
uv run physics-bench --tier consumer

# Run high-end benchmark (DGX Spark / 70B+ models)
uv run physics-bench --tier highend

# Test specific models
uv run physics-bench --models llama3.3:70b qwen2.5:72b deepseek-r1:70b

# Auto-pull missing models
uv run physics-bench --tier consumer --pull

# Use a stronger judge
uv run physics-bench --tier highend --judge llama3.3:70b

# Remote Ollama (e.g. DGX from your laptop)
uv run physics-bench --host http://dgx-spark.local:11434 --tier highend

# List available models
uv run physics-bench --list-models
```

### Generate HTML report

```bash
uv run physics-report --latest
# → results/report_<run_id>.html
```

---

## Output files

All results go to `./results/` (configurable via `--output-dir`):

| File | Contents |
| ---- | -------- |
| `responses_<run_id>.jsonl` | Raw answers + speed metrics per model/question |
| `scores_<run_id>.jsonl` | Judge scores per model/question |
| `summary_<run_id>.json` | Aggregated averages |
| `report_<run_id>.html` | Visual dark-themed HTML report |

### Response record

```json
{
  "model": "llama3.1:8b",
  "question_id": "cms_001",
  "answer": "...",
  "prompt_tokens": 120,
  "response_tokens": 487,
  "time_to_first_token_s": 0.312,
  "total_time_s": 14.2,
  "tokens_per_second": 34.3
}
```

### Score record

```json
{
  "model": "llama3.1:8b",
  "question_id": "cms_001",
  "judge_model": "qwen2.5:7b",
  "accuracy_score": 8,
  "completeness_score": 7,
  "clarity_score": 9,
  "technical_depth_score": 7,
  "overall_score": 7.7,
  "judge_reasoning": "Correct pixel sensor description and good b-tagging coverage, but missed 3D pixel discussion for HL-LHC."
}
```

---

## Questions included

### CMS Data Analysis Group (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `cms_001` | Higgs Physics | Hard | H→ττ final states, SVfit mass, BDT categories, Z→ττ background |
| `cms_002` | Long-Lived Particles | Hard | Dark photon from Higgs portal, displaced muon pairs, inner tracker + muon spectrometer |
| `cms_003` | Top Quark Physics | Hard | SMEFT tZ/tγ operators, anomalous dipole moments, tt̄Z and tt̄γ differential cross sections |
| `cms_004` | Missing Energy | Medium | p_T^miss significance, pile-up robustness, application to compressed SUSY |
| `cms_005` | SUSY Searches | Hard | MT2(ll) endpoint, compressed spectra, SModelS simplified model decomposition |

### ALICE Experiment (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `alice_001` | QGP Phenomenology | Hard | QCD phase diagram, deconfinement signatures |
| `alice_002` | QGP Phenomenology | Hard | Elliptic flow v₂, viscous hydrodynamics, η/s |
| `alice_003` | Hadronisation | Medium | Lund strings vs. thermal model, baryon anomaly |
| `alice_004` | Detector Technology | Hard | TPC tracking, dE/dx PID, GEM upgrade for Run 3 |
| `alice_005` | Heavy-Ion Collisions | Hard | Nuclear modification factor R_AA, jet quenching, J/ψ regeneration |

### Belle / Belle II Experiment (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `belle_001` | CKM Matrix | Hard | \|Vcb\|, \|Vub\|, unitarity triangle, inclusive vs. exclusive tension |
| `belle_002` | CP Violation | Hard | Time-dependent CP asymmetry, sin 2β, golden channel |
| `belle_003` | Rare Decays | Hard | b→sℓ⁺ℓ⁻ Wilson coefficients, R_K and R_K* |
| `belle_004` | Silicon Vertex Detector | Hard | SVD geometry, DSSDs, SuperKEKB background challenges |
| `belle_005` | Semileptonic Decays | Medium | Hadronic tagging (FEI), w variable, zero-recoil limit |

### Detector Development (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `detdev_001` | DMAPS | Hard | Depleted monolithic pixels vs. hybrid detectors |
| `detdev_002` | LGAD | Hard | Internal gain mechanism, 4D tracking, acceptor removal |
| `detdev_003` | Silicon Carbide | Medium | 4H-SiC properties, radiation hardness, practical limits |
| `detdev_004` | Medical Applications | Medium | Proton/ion therapy, proton CT, range uncertainty |
| `detdev_005` | Radiation Damage | Hard | TID vs. NIEL, type inversion, depletion voltage evolution |

### Exotic Atoms (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `exotic_001` | Positronium | Medium | Para-Ps / ortho-Ps lifetimes, C-symmetry, bound-state QED |
| `exotic_002` | CPT Theorem | Hard | CPT theorem, antihydrogen predictions, SME parametrisation |
| `exotic_003` | Antihydrogen Formation | Hard | AD/ELENA, three-body recombination, Rydberg H̄ |
| `exotic_004` | Antihydrogen Spectroscopy | Hard | 1S–2S two-photon spectroscopy, ASACUSA cusp-trap HFS |
| `exotic_005` | Matter-Antimatter Asymmetry | Medium | Sakharov conditions, SM shortcomings, low-energy CPT tests |

### Gravitational Waves (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `gw_001` | Detector Technology | Hard | Advanced LIGO interferometer, Fabry-Perot cavities, quantum noise |
| `gw_002` | IMBH Physics | Hard | Intermediate-mass black holes, formation channels, GW signatures |
| `gw_003` | Einstein Telescope | Hard | ET design (triangle, cryogenics, xylophone), new science cases |
| `gw_004` | Data Analysis | Hard | Matched filtering, template banks, ML/FPGA acceleration |
| `gw_005` | Dark Matter | Medium | DM effects on IMBH waveforms, dynamical friction, boson clouds |

### Machine Learning (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `ml_001` | Fast Simulation | Hard | Generative models for calorimeter showers, GANs vs. normalizing flows |
| `ml_002` | Monte Carlo Enhancement | Hard | Normalizing flows for importance sampling in Sherpa/MadGraph |
| `ml_003` | CaloChallenge | Medium | CaloChallenge datasets, evaluation metrics, generation speed |
| `ml_004` | Anomaly Detection | Hard | CATHODE method, conditional generative background estimation |
| `ml_005` | BSM Searches | Medium | Supervised vs. weakly supervised vs. unsupervised, likelihood-ratio optimality |

### Precision Experiments (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `prec_001` | Antiprotonic Helium | Hard | p̄He⁺ metastability, stimulated Raman spectroscopy, antiproton mass ratio |
| `prec_002` | ASACUSA HFS | Hard | Rabi-method beam scheme, systematics, CPT and SME bounds |
| `prec_003` | HYDRA | Hard | H/D hyperfine spectroscopy, Lorentz invariance, sidereal variation |
| `prec_004` | GRASIAN | Medium | Gravitational quantum states, WEP test with antihydrogen |
| `prec_005` | Protonium | Medium | pp̄ formation, cascade, complex energy shift and NN̄ interaction |

### Rare Event Searches (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `res_001` | CRESST | Hard | CaWO₄ cryogenic bolometer, phonon+light dual channel, particle discrimination |
| `res_002` | COSINUS | Hard | DAMA/LIBRA annual modulation, NaI cryogenic test, model-independent comparison |
| `res_003` | NUCLEUS | Hard | CEνNS cross section, coherence condition, BSM probes at reactor |
| `res_004` | DANAE | Hard | DEPFET-RNDR sub-electron noise, DM-electron scattering, sub-GeV DM |
| `res_005` | Underground Physics | Medium | Muon suppression at LNGS, residual backgrounds, bolometer discrimination strategies |

### Theoretical Physics (5 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `theo_001` | QCD Mass Generation | Hard | Chiral symmetry breaking, quark condensate, pion as Goldstone boson, trace anomaly |
| `theo_002` | SUSY Phenomenology | Hard | Hierarchy problem, squark/gluino production, flavour-violating decays, LHC limits |
| `theo_003` | Dark Photon | Hard | Kinetic mixing, parameter space, stellar bounds, dark-photon DM absorption |
| `theo_004` | Migdal Effect | Hard | Non-adiabatic atomic response, electronic signal from nuclear recoil, mass reach in xenon |
| `theo_005` | Big Bang Nucleosynthesis | Medium | BBN sequence, ⁴He yield, N_eff, constraints on light dark-sector particles |

### Historic Activities — DELPHI, NA48, UA1, NA36 (10 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `hist_001` | DELPHI / Electroweak Precision | Hard | Z lineshape 5-parameter fit, Γ_inv, N_ν = 2.984 ± 0.008, LEP energy calibration |
| `hist_002` | DELPHI / Silicon Tracking | Hard | HEPHY Very Forward Tracker, DSSDs, b-tagging to 11°, LEP2 Higgs and WW physics |
| `hist_003` | DELPHI / W Boson and TGCs | Hard | WW threshold scan, M_W reconstruction, colour reconnection, anomalous TGCs Δκ_γ λ_γ |
| `hist_004` | NA48 / Direct CP Violation | Hard | Simultaneous K_S K_L beams, quadruple ratio, LKr calorimeter, Re(ε'/ε) = (14.7 ± 2.2)×10⁻⁴ |
| `hist_005` | NA48/2 / Charged Kaon CP | Medium | Simultaneous K⁺K⁻ beams, Dalitz slope asymmetry A_g, π⁰π⁰ cusp and ππ scattering lengths |
| `hist_006` | UA1 / W Boson Discovery | Hard | Gondola ECAL (HEPHY PM calibration), missing E_T^miss, isolation cuts, M_T Jacobian edge |
| `hist_007` | UA1 / Z Boson and EW Tests | Hard | Z→ee and Z→μμ reconstruction, W/Z ratio constraining sin²θ_W, stochastic cooling and AA |
| `hist_008` | UA1 / Jets and SUSY Search | Hard | Dijet cross sections, monojet events, W→τν vs SUSY gluino interpretation, resolution |
| `hist_009` | NA36 / Strangeness and QGP | Hard | Rafelski-Müller prediction, TPC V⁰ and cascade reconstruction, Λ K⁰ Ξ enhancement in S+S |
| `hist_010` | NA36 / Energy Density | Medium | Bjorken ε_Bj formula, Glauber N_part, thermal model T_ch and γ_s strangeness saturation |

### General Public Outreach (10 questions)

| ID | Domain | Difficulty | Topic |
| -- | ------ | ---------- | ----- |
| `public_001` | Outreach — Accelerators | Easy | What the LHC is, how it works, scale and purpose |
| `public_002` | Outreach — Higgs Boson | Easy | Higgs field, origin of mass, 2012 discovery and Nobel Prize |
| `public_003` | Outreach — LHC Safety | Easy | Black hole fears debunked, cosmic-ray argument, CERN safety studies |
| `public_004` | Outreach — Energy and Sustainability | Easy | LHC electricity consumption (~1.3 TWh/yr), grid sourcing, sustainability programme |
| `public_005` | Outreach — CERN Discoveries | Easy | W/Z bosons, quarks, LEP precision, matter-antimatter, World Wide Web |
| `public_006` | Outreach — Standard Model | Easy | 12 matter particles, force carriers, what the model leaves unexplained |
| `public_007` | Outreach — Antimatter | Easy | Antiparticles, annihilation, PET scanners, matter-antimatter asymmetry mystery |
| `public_008` | Outreach — Dark Matter and Dark Energy | Easy | 5% visible universe, WIMP candidates, LHC missing-energy searches, dark energy |
| `public_009` | Outreach — Real-World Applications | Easy | WWW, PET/hadron therapy, superconducting magnets, silicon sensors, grid computing |
| `public_010` | Outreach — Future of Particle Physics | Easy | HL-LHC, FCC-ee/hh (100 TeV, 100 km), ILC, muon collider, open questions |

---

## Model lists

### Consumer tier (≤12 GB VRAM)

| Model | ~VRAM | Notes |
| ----- | ----- | ----- |
| `llama3.2:3b` | 2 GB | Fast baseline |
| `llama3.1:8b` | 5 GB | Good all-rounder |
| `mistral:7b` | 5 GB | Strong instruction following |
| `gemma2:9b` | 6 GB | Google, strong STEM |
| `qwen2.5:7b` | 5 GB | Alibaba, excellent science |
| `phi4:14b` | 9 GB | Microsoft, compact but capable |
| `deepseek-r1:8b` | 5 GB | Chain-of-thought reasoning |

### High-end tier (DGX Spark / 128 GB unified memory)

| Model | ~VRAM | Notes |
| ----- | ----- | ----- |
| `qwq:32b` | 20 GB | QwQ reasoning |
| `deepseek-r1:32b` | 20 GB | DeepSeek reasoning 32B |
| `llama3.3:70b` | 40 GB | Meta flagship |
| `qwen2.5:72b` | 41 GB | Alibaba 72B |
| `deepseek-r1:70b` | 40 GB | DeepSeek reasoning 70B |
| `mistral-large:latest` | 47 GB | Mistral Large 2 |
| `mixtral:8x22b` | 80 GB | Mistral MoE |

---

## Score weights

| Dimension | Weight | Description |
| --------- | ------ | ----------- |
| Accuracy | 40% | Factual correctness — right numbers, formulae, names |
| Completeness | 30% | Coverage of key concepts from the reference answer |
| Clarity | 15% | Structure and readability |
| Technical Depth | 15% | Appropriate detail for a physics expert |

---

## Adding custom questions

Edit `data/physics_qa_bank.yaml`:

```toml
[[questions]]
id = "unique_id"
domain = "Topic area"
difficulty = "easy|medium|hard"
question = "Your question text"
reference_answer = "Expert reference answer with key facts and numbers"
```

Better reference answers → more meaningful judge scores.

---

## Development

```bash
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

---

## License

[MIT](LICENSE) © 2025 Dietrich Liko, Austrian Academy of Sciences
