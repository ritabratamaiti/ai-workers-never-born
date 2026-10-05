# The demographic drag AI has to cancel out: data and code

This repository reproduces every chart and number in the essay [*AI has to replace the workers who were never born*](https://toex.substack.com/p/ai-workers-never-born). Everything uses public data, and every number the text quotes is written to [`numbers.md`](numbers.md) by the code that computes it.

| # | Chart | File |
|---|---|---|
| 1 | Two in three people now live where fertility is below replacement | `figures/01_below_replacement.png` |
| 2 | Fertility has fallen everywhere, and furthest in East Asia | `figures/02_fertility_rates.png` |
| 3 | Working-age populations have peaked in most big economies | `figures/03_peak_workers.png` |
| 4 | South Korea is heading for one working-age adult per retiree | `figures/04_workers_per_retiree.png` |
| 5 | Aging will swallow most of the past decade's productivity growth | `figures/05_demographic_drag.png` |
| 6 | Only the boldest AI forecasts would offset South Korea's aging | `figures/06_ai_vs_drag.png` |
| 7 | Hiring is harder for young graduates, but also for older ones | `figures/07_young_graduates.png` |
| 8 | Employers now want more carers and fewer coders | `figures/08_postings_vs_exposure.png` |
| 9 | Births have collapsed among women in their twenties | `figures/09_births_by_age.png` |

Each chart is saved as a 1456-pixel-wide PNG and as an SVG.

## Run it

```bash
pip install -r requirements.txt
python story.py                 # downloads ~130 MB once into data/raw/, then runs in seconds
```

`story.py` is also a notebook: VS Code and Jupyter open its `# %%` cells directly. To rebuild the executed `story.ipynb`:

```bash
pip install -r requirements-notebook.txt
python build_notebook.py
```

Downloads are cached in `data/raw/`; set `REFRESH=1` to fetch fresh copies. Tidy versions of every table the charts use are written to `data/processed/`, and the source URLs and retrieval dates go to `data/sources.json`.

## Data

| Dataset | Publisher | Used for | Terms |
|---|---|---|---|
| World Population Prospects 2024: demographic indicators, population by 5-year age group, fertility by age (medium variant) | UN DESA, Population Division | fertility, population by age, projections to 2100 | cite *United Nations, DESA, Population Division (2024). World Population Prospects 2024* |
| World Development Indicators: GDP per person employed (constant 2021 PPP $), `SL.GDP.PCAP.EM.KD` | World Bank (ILO modelled employment) | productivity growth, 2014-24 | CC BY 4.0 |
| Current Population Survey unemployment rates: `CGBD2024`, `CGBD25O`, `LNS14024887`, `LNS14000060` | US Bureau of Labor Statistics, via FRED | young vs older graduates | BLS data are public domain |
| Job postings index by sector, US | Indeed Hiring Lab | postings vs 1 Feb 2020 | CC BY 4.0, cite Indeed Hiring Lab |
| Occupation-level exposure to LLMs (`occ_level.csv`) | Eloundou, Manning, Mishkin & Rock (2023), *GPTs are GPTs*; github.com/openai/GPTs-are-GPTs | sector exposure scores | MIT |
| AI productivity forecasts | the publications listed in `data/ai_estimates.csv` | chart 6 | quoted with sources |

## Method

**Below replacement (chart 1).** For each year, the population of countries and areas with a total fertility rate below 2.1, divided by world population. The stricter net-reproduction-rate test (NRR below 1) is reported as a check.

**The demographic drag (charts 5 and 6).** GDP per person is the product of three terms:
- GDP per worker;
- workers per working-age person;
- the working-age share of the population.

We hold the middle term constant. The drag is then the annualised log change in the working-age (15-64) share between 2025 and 2050, in the UN medium variant. Adding it to growth in GDP per person employed over 2014-24 gives the growth in GDP per person if productivity keeps its recent pace and nothing else changes. There are two sensitivity cases, both in `data/processed/demographic_drag.csv`:
- working ages 20-64 throughout;
- "work to 70", with working ages 20-69 in 2050 and 20-64 in 2025.

**AI forecasts (chart 6).** Published estimates of AI's boost to annual productivity growth, in percentage points. Where a source gives a cumulative level effect, it is annualised. Acemoglu's TFP estimate is converted to labour productivity by multiplying by 1.5-1.6, the ratio implied by the OECD's own TFP and labour-productivity ranges. Every row in `data/ai_estimates.csv` records its basis and URL.

**Exposure (chart 8).** Exposure is the β measure from Eloundou et al.:
- **E1:** the share of an occupation's tasks that an LLM alone could do at least 50% faster at equal quality;
- **E2:** the share where software built on LLMs could do so;
- **β = E1 + 0.5 × E2**, using the human annotators' ratings.

Each Indeed sector is mapped by hand to a few representative SOC 2018 occupations (`data/sector_soc_map.csv`). Sector exposure is the unweighted mean across those occupations.

## Limitations

- **UN figures are estimates.** They are projections, and where censuses are old or missing they are model-based. The medium variant already assumes some fertility recovery and continued migration.
- **The drag is an accounting identity, not a forecast.** It assumes employment rates within each age band don't change. In practice participation, retirement ages and migration all move, and the "work to 70" case shows how much later retirement alone could offset.
- **Productivity is measured per person employed, not per hour,** and pandemic-era swings sit inside the 2014-24 window. The 2000-19 rate is in `demographic_drag.csv` for comparison.
- **Most AI forecasts are for the US.** The OECD expects somewhat smaller gains where adoption is slower. These are forecasts, not measurements.
- **The jobs data are suggestive, not causal.**
  - Postings fell across almost every sector after the 2021-22 hiring boom.
  - The relationship with AI exposure is weak: a correlation of -0.33 for levels and -0.27 for the change since November 2022.
  - The sector-to-occupation map is a judgement call.
- **Young-graduate unemployment comes from a small survey sample.** It is shown as a 12-month moving average.

## License

- **Code** (`*.py`, `story.ipynb`): [PolyForm Noncommercial 1.0.0](LICENSE.md). You may use, change and share it for any noncommercial purpose.
- **Charts and `numbers.md`**: [CC BY-NC 4.0](LICENSE-CHARTS.txt). Credit "Ritabrata Maiti" and link back here.
- **Data**: the files in `data/` come from the publishers listed above and stay under their own terms; the noncommercial licences above do not apply to them.
