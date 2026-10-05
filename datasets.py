"""Download, cache and tidy the public datasets behind the story.

Raw downloads are cached in data/raw/ (delete a file, or set REFRESH=1, to fetch it again).
Every loader also writes the tidy table it returns to data/processed/, so each number in the
charts can be checked without running any code. URLs and retrieval dates are recorded in
data/sources.json.
"""
from __future__ import annotations

import json
import os
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
PROCESSED = HERE / "data" / "processed"
USER_AGENT = "demography-ai-analysis/1.0 (reproducible data journalism)"
REFRESH = os.environ.get("REFRESH") == "1"

COUNTRIES = {
    "KOR": "South Korea", "JPN": "Japan", "CHN": "China", "ITA": "Italy", "ESP": "Spain", "DEU": "Germany",
    "FRA": "France", "GBR": "Britain", "USA": "United States", "BRA": "Brazil", "IND": "India", "NGA": "Nigeria",
}
WORLD = "WLD"
NAMES = {**COUNTRIES, WORLD: "World"}
LAST_ESTIMATE_YEAR = 2023  # WPP 2024 has estimates through 2023 and medium-variant projections after

WPP = "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/"
URLS = {
    "wpp_indicators": WPP + "WPP2024_Demographic_Indicators_Medium.csv.gz",
    "wpp_age5": WPP + "WPP2024_PopulationByAge5GroupSex_Medium.csv.gz",
    "wpp_asfr5": WPP + "WPP2024_Fertility_by_Age5.csv.gz",
    "indeed_sectors": "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/job_postings_by_sector_US.csv",
    "indeed_total": "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/aggregate_job_postings_US.csv",
    "gpts_exposure": "https://raw.githubusercontent.com/openai/GPTs-are-GPTs/main/data/occ_level.csv",
}


# --------------------------------------------------------------------------- plumbing

def _log_source(name: str, url: str, path: Path) -> None:
    log = RAW.parent / "sources.json"
    entries = json.loads(log.read_text("utf-8")) if log.exists() else {}
    entries[name] = {"url": url, "file": f"data/raw/{path.name}", "bytes": path.stat().st_size,
                     "retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    log.write_text(json.dumps(dict(sorted(entries.items())), indent=2) + "\n", "utf-8")


def download(name: str, url: str | None = None, filename: str | None = None) -> Path:
    """Fetch url into data/raw/ once; later calls reuse the file."""
    url = url or URLS[name]
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / (filename or url.rsplit("/", 1)[-1])
    if REFRESH or not path.exists():
        print(f"downloading {url}")
        tmp = path.with_name(path.name + ".part")
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=600) as response, open(tmp, "wb") as out:
            shutil.copyfileobj(response, out)
        tmp.replace(path)
        _log_source(name, url, path)
    return path


def _cached(name: str, raws: list, build) -> pd.DataFrame:
    """Return data/processed/<name>.csv, rebuilding it when any raw input is newer."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / f"{name}.csv"
    if not (out.exists() and out.stat().st_mtime >= max(p.stat().st_mtime for p in raws)):
        build().to_csv(out, index=False)
    return pd.read_csv(out)


def _wpp_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the world and individual countries/areas; give the world the code WLD."""
    df = df[df.LocTypeName.isin(["World", "Country/Area"])].copy()
    df.loc[df.LocTypeName == "World", "ISO3_code"] = WORLD
    return df


# Explicit text dtypes: chunked reads with usecols crash in pandas when it has to guess mixed types.
WPP_TEXT = {"ISO3_code": str, "LocTypeName": str, "Location": str, "Variant": str, "AgeGrp": str}


# --------------------------------------------------------------------------- UN World Population Prospects 2024

def wpp_indicators() -> pd.DataFrame:
    """Population, fertility (TFR, NRR, mean age at childbearing) for every country and the world, 1950-2100."""
    raw = download("wpp_indicators")

    def build():
        cols = ["ISO3_code", "LocTypeName", "Location", "Time", "TPopulation1July", "TFR", "NRR", "MAC",
                "Births", "MedianAgePop"]
        df = _wpp_locations(pd.read_csv(raw, usecols=cols, dtype=WPP_TEXT))
        return df.rename(columns={"ISO3_code": "iso3", "LocTypeName": "loc_type", "Location": "name", "Time": "year",
                                  "TPopulation1July": "pop_thousands", "TFR": "tfr", "NRR": "nrr", "MAC": "mac",
                                  "Births": "births_thousands", "MedianAgePop": "median_age"})

    return _cached("wpp_indicators", [raw], build)


AGE_BANDS = {  # column: (first age, last age), summed from 5-year groups
    "pop_0_14": (0, 14), "pop_15_64": (15, 64), "pop_20_64": (20, 64), "pop_20_69": (20, 69), "pop_65p": (65, 200),
}


def wpp_broad_ages() -> pd.DataFrame:
    """Population by broad age band (thousands) and derived shares, every country and the world, 1950-2100."""
    raw = download("wpp_age5")

    def build():
        cols = ["ISO3_code", "LocTypeName", "Location", "Time", "AgeGrpStart", "PopTotal"]
        df = pd.concat([_wpp_locations(c) for c in pd.read_csv(raw, usecols=cols, chunksize=500_000, dtype=WPP_TEXT)],
                       ignore_index=True)
        start = df.AgeGrpStart
        df = df.assign(**{band: df.PopTotal.where((start >= lo) & (start + 4 <= hi), 0)
                          for band, (lo, hi) in AGE_BANDS.items()})
        out = (df.groupby(["ISO3_code", "LocTypeName", "Location", "Time"])[["PopTotal", *AGE_BANDS]]
               .sum().reset_index()
               .rename(columns={"ISO3_code": "iso3", "LocTypeName": "loc_type", "Location": "name", "Time": "year",
                                "PopTotal": "pop_total"}))
        for band in ("pop_15_64", "pop_20_64", "pop_20_69"):
            out[band.replace("pop_", "share_")] = out[band] / out.pop_total
        out["support_20_64"] = out.pop_20_64 / out.pop_65p
        return out

    return _cached("wpp_broad_ages", [raw], build)


def wpp_asfr() -> pd.DataFrame:
    """Births per 1,000 women by 5-year age group, selected countries and the world, 1950-2100 (medium variant)."""
    raw = download("wpp_asfr5")
    keep = set(COUNTRIES) | {WORLD}

    def build():
        cols = ["ISO3_code", "LocTypeName", "Location", "Variant", "Time", "AgeGrp", "AgeGrpStart", "ASFR"]
        parts = []
        for chunk in pd.read_csv(raw, usecols=cols, chunksize=500_000, dtype=WPP_TEXT):
            chunk = _wpp_locations(chunk[chunk.Variant == "Medium"])
            parts.append(chunk[chunk.ISO3_code.isin(keep)])
        df = pd.concat(parts, ignore_index=True)
        return df.rename(columns={"ISO3_code": "iso3", "Location": "name", "Time": "year", "AgeGrp": "age_group",
                                  "AgeGrpStart": "age_start", "ASFR": "asfr"}).drop(columns=["LocTypeName", "Variant"])

    return _cached("wpp_asfr", [raw], build)


# --------------------------------------------------------------------------- World Bank, FRED

def worldbank(indicator: str, start: int, end: int, source: int | None = None) -> pd.DataFrame:
    """A World Development Indicators series for the selected countries and the world (iso3, year, value)."""
    codes = ";".join([*COUNTRIES, WORLD])
    url = (f"https://api.worldbank.org/v2/country/{codes}/indicator/{indicator}"
           f"?format=json&per_page=20000&date={start}:{end}" + (f"&source={source}" if source else ""))
    suffix = f"_source{source}" if source else ""
    raw = download(f"worldbank_{indicator}{suffix}", url, f"worldbank_{indicator}_{start}-{end}{suffix}.json")

    def build():
        payload = json.loads(raw.read_text("utf-8"))
        rows = [{"iso3": r["countryiso3code"], "year": int(r["date"]), "value": r["value"]}
                for r in payload[1] or [] if r["value"] is not None]
        return pd.DataFrame(rows).sort_values(["iso3", "year"])

    return _cached(f"worldbank_{indicator}{suffix}", [raw], build)


def fred(series: list) -> pd.DataFrame:
    """Monthly FRED series in long form (date, series, value)."""
    frames = []
    for sid in series:
        raw = download(f"fred_{sid}", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", f"fred_{sid}.csv")
        df = pd.read_csv(raw)
        df.columns = ["date", "value"]
        frames.append(df.assign(series=sid, value=pd.to_numeric(df.value, errors="coerce")))
    out = pd.concat(frames, ignore_index=True).dropna()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED / "fred.csv", index=False)
    out["date"] = pd.to_datetime(out.date)
    return out


# --------------------------------------------------------------------------- jobs data

def indeed_sectors() -> pd.DataFrame:
    """Indeed US job postings index by sector (1 Feb 2020 = 100), daily, total postings."""
    raw = download("indeed_sectors")

    def build():
        df = pd.read_csv(raw)
        df = df[df.variable == "total postings"]
        return df.rename(columns={"display_name": "sector", "indeed_job_postings_index": "index"})[
            ["date", "sector", "index"]]

    df = _cached("indeed_sectors", [raw], build)
    df["date"] = pd.to_datetime(df.date)
    return df


def indeed_total() -> pd.DataFrame:
    """Indeed US job postings index, all postings, seasonally adjusted (1 Feb 2020 = 100), daily."""
    raw = download("indeed_total")

    def build():
        df = pd.read_csv(raw)
        df = df[df.variable == "total postings"]
        return df.rename(columns={"indeed_job_postings_index_SA": "index"})[["date", "index"]]

    df = _cached("indeed_total", [raw], build)
    df["date"] = pd.to_datetime(df.date)
    return df


def sector_exposure() -> pd.DataFrame:
    """Mean LLM exposure (Eloundou et al. 2023) of the occupations mapped to each Indeed sector.

    Exposure is the paper's beta measure, E1 + 0.5 * E2: E1 is the share of an occupation's tasks an LLM
    alone could do at least 50% faster at equal quality, E2 the share where LLM-powered software could.
    The sector-to-occupation map in data/sector_soc_map.csv is hand-built from SOC 2018 codes; it is a
    judgement call.
    """
    raw = download("gpts_exposure")
    occ = pd.read_csv(raw).rename(columns={"O*NET-SOC Code": "onet_soc", "Title": "title"})
    occ["soc"] = occ.onet_soc.str[:7]
    mapping = pd.read_csv(HERE / "data" / "sector_soc_map.csv")
    rows = []
    for rec in mapping.itertuples():
        codes = [c.strip() for c in rec.soc_codes.split(";") if c.strip()]
        matched = occ[occ.soc.isin(codes)]
        missing = sorted(set(codes) - set(matched.soc))
        if missing:
            print(f"warning: {rec.sector}: no exposure score for SOC {missing}")
        rows.append({"sector": rec.sector, "group": rec.group, "occupations": len(matched),
                     "exposure_human": matched.human_rating_beta.mean(),
                     "exposure_gpt4": matched.dv_rating_beta.mean()})
    out = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED / "sector_exposure.csv", index=False)
    return out
