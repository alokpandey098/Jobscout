#!/usr/bin/env python3
"""Fetch fresh jobs from free sources and write jobs.json (run by GitHub Actions).

Sources (all optional except the two keyless ones):
  Remotive   keyless   remote jobs worldwide (data is 24h delayed by Remotive)
  Arbeitnow  keyless   Europe (mostly Germany)
  Adzuna     keys      US, India, Australia, UK, Canada, Singapore, DE, NL, FR
  Jooble     key       Dubai / UAE

Secrets (GitHub repo -> Settings -> Secrets): ADZUNA_ID, ADZUNA_KEY, JOOBLE_KEY.
Missing keys just skip that source. A run that finds zero jobs never overwrites jobs.json.
"""
import hashlib, html, json, os, re, sys, time
from datetime import datetime, timezone, timedelta
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "JobScout/1.0 (personal job search; +https://github.com)"}
TAG = re.compile(r"<[^>]+>")


def http_get(url, **kw):
    return requests.get(url, headers=UA, timeout=30, **kw)


def http_post(url, **kw):
    return requests.post(url, headers=UA, timeout=30, **kw)


def text(s, limit):
    s = html.unescape(TAG.sub(" ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:limit]


def iso(v):
    """Return an ISO-8601 UTC string, or None if v is not a usable date."""
    try:
        if isinstance(v, (int, float)):
            d = datetime.fromtimestamp(v / 1000 if v > 1e12 else v, timezone.utc)
        else:
            v = str(v).strip().replace("Z", "+00:00")
            d = datetime.fromisoformat(v)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            d = d.astimezone(timezone.utc)
        if d > datetime.now(timezone.utc) + timedelta(hours=1):
            return None
        return d.isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def job(source, ext_id, title, company, country, location, posted, url, desc, cfg):
    p = iso(posted)
    if not (title and url and p and str(url).startswith(("http://", "https://"))):
        return None
    return {
        "id": source[0].lower() + hashlib.sha1(f"{source}{ext_id or url}".encode()).hexdigest()[:12],
        "title": text(title, 140), "company": text(company, 80) or "Company",
        "country": country, "location": text(location, 80), "posted": p, "url": url,
        "description": text(desc, cfg["desc_chars"]), "source": source,
    }


def remotive(cfg):
    d = http_get("https://remotive.com/api/remote-jobs", params={"limit": 300}).json()
    return [job("Remotive", x.get("id"), x.get("title"), x.get("company_name"), "Remote",
                x.get("candidate_required_location") or "Remote", x.get("publication_date"),
                x.get("url"), x.get("description"), cfg) for x in d.get("jobs", [])]


def arbeitnow(cfg):
    out = []
    for page in (1, 2):
        d = http_get("https://www.arbeitnow.com/api/job-board-api", params={"page": page}).json()
        out += [job("Arbeitnow", x.get("slug"), x.get("title"), x.get("company_name"), "Europe",
                    x.get("location") or "Europe", x.get("created_at"), x.get("url"),
                    x.get("description"), cfg) for x in d.get("data", [])]
        time.sleep(0.5)
    return out


def adzuna(cfg, app_id, app_key):
    out = []
    for label, codes in cfg["adzuna_countries"].items():
        for code in ([codes] if isinstance(codes, str) else codes):
            for kw in cfg["keywords"]:
                try:
                    r = http_get(f"https://api.adzuna.com/v1/api/jobs/{code}/search/1", params={
                        "app_id": app_id, "app_key": app_key, "results_per_page": 50, "what": kw,
                        "max_days_old": cfg["max_days_old"], "sort_by": "date"})
                    r.raise_for_status()
                    for x in r.json().get("results", []):
                        out.append(job("Adzuna", x.get("id"), x.get("title"),
                                       (x.get("company") or {}).get("display_name"), label,
                                       (x.get("location") or {}).get("display_name"), x.get("created"),
                                       x.get("redirect_url"), x.get("description"), cfg))
                except Exception as e:
                    print(f"  adzuna {code} '{kw}': {e}", file=sys.stderr)
                time.sleep(0.4)
    return out


def jooble(cfg, key):
    out = []
    for label, loc in cfg["jooble_locations"].items():
        for kw in cfg["keywords"]:
            try:
                r = http_post(f"https://jooble.org/api/{key}", json={"keywords": kw, "location": loc})
                r.raise_for_status()
                for x in r.json().get("jobs", []):
                    out.append(job("Jooble", x.get("id"), x.get("title"), x.get("company"), label,
                                   x.get("location") or loc, x.get("updated"), x.get("link"),
                                   x.get("snippet"), cfg))
            except Exception as e:
                print(f"  jooble '{kw}': {e}", file=sys.stderr)
            time.sleep(0.4)
    return out


def main(out_path=None):
    cfg = json.load(open(os.path.join(ROOT, "config.json")))
    out_path = out_path or os.path.join(ROOT, "jobs.json")
    sources = [("Remotive", lambda: remotive(cfg)), ("Arbeitnow", lambda: arbeitnow(cfg))]
    if os.getenv("ADZUNA_ID") and os.getenv("ADZUNA_KEY"):
        sources.append(("Adzuna", lambda: adzuna(cfg, os.environ["ADZUNA_ID"], os.environ["ADZUNA_KEY"])))
    else:
        print("ADZUNA_ID / ADZUNA_KEY not set: skipping Adzuna (US, India, Australia, UK, Canada, Singapore)")
    if os.getenv("JOOBLE_KEY"):
        sources.append(("Jooble", lambda: jooble(cfg, os.environ["JOOBLE_KEY"])))
    else:
        print("JOOBLE_KEY not set: skipping Jooble (Dubai/UAE)")

    jobs, counts = {}, {}
    for name, fn in sources:
        try:
            got = [j for j in fn() if j]
        except Exception as e:
            print(f"{name} failed: {e}", file=sys.stderr)
            got = []
        counts[name] = len(got)
        print(f"{name}: {len(got)} jobs")
        for j in got:
            jobs.setdefault(j["url"], j)

    cutoff = datetime.now(timezone.utc) - timedelta(days=cfg["max_days_old"])
    keep = [j for j in jobs.values() if datetime.fromisoformat(j["posted"].replace("Z", "+00:00")) >= cutoff]
    keep.sort(key=lambda j: j["posted"], reverse=True)
    keep = keep[: cfg["max_jobs"]]
    if not keep:
        print("No jobs fetched. Keeping the existing jobs.json.", file=sys.stderr)
        return 1
    data = {"updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "counts": counts, "jobs": keep}
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    print(f"Wrote {len(keep)} jobs to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
