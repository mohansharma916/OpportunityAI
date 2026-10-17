"""
OpportunityOS — Discovery filters and scoring (pivot plan, Pillar 1a).

Hard filters: remote, eligible from the candidate's country, salary floor, excluded companies,
freshness, and a title that matches a target title.
Score 0-100: skills 40, title & seniority 25, salary 15, employer 10, freshness 10.
70+ goes to the apply queue, 50-69 to the "maybe" list, below 50 is dropped.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from packages.connectors.job_feeds import JobPosting

QUEUE_THRESHOLD = 70
MAYBE_THRESHOLD = 50
MAX_AGE_DAYS_BOARD = 14
MAX_AGE_DAYS_COMPANY = 60  # company pages remove filled roles; their dates are often the original post date

GENERIC_TITLE_WORDS = {
    "engineer", "developer", "senior", "junior", "lead", "staff", "principal", "software", "manager",
    "head", "and", "the", "remote", "intern", "associate", "sr", "jr", "ii", "iii", "iv", "of", "for",
}
ROLE_NOUNS = re.compile(r"\b(engineer|developer|programmer|architect|sre|devops|swe)\b", re.I)

WORLDWIDE = re.compile(r"\b(worldwide|anywhere|global|world|international)\b", re.I)
_EUROPE = ["europe", "eu", "emea", "european union", "eea"]
_LATAM = ["latam", "latin america", "south america", "americas"]
_APAC = ["apac", "asia", "asia pacific", "asia-pacific"]
REGION_ALIASES: Dict[str, List[str]] = {
    "india": ["india", "south asia", "ist", "utc+5:30", "gmt+5:30"] + _APAC,
    "united states": ["us", "usa", "u.s.", "united states", "north america", "americas"],
    "canada": ["canada", "north america", "americas"],
    "united kingdom": ["uk", "united kingdom", "great britain", "britain", "england"] + _EUROPE,
    "australia": ["australia", "oceania", "anz"] + _APAC,
    "philippines": ["philippines", "southeast asia", "sea"] + _APAC,
    "singapore": ["singapore", "southeast asia", "sea"] + _APAC,
    "pakistan": ["pakistan", "south asia"] + _APAC,
    "bangladesh": ["bangladesh", "south asia"] + _APAC,
    "brazil": ["brazil", "brasil"] + _LATAM,
    "mexico": ["mexico", "north america"] + _LATAM,
    "argentina": ["argentina"] + _LATAM,
    "colombia": ["colombia"] + _LATAM,
    "nigeria": ["nigeria", "africa", "emea"],
    "kenya": ["kenya", "africa", "emea"],
    "south africa": ["south africa", "africa", "emea"],
}
_EU_COUNTRIES = ["germany", "france", "spain", "italy", "netherlands", "poland", "portugal", "ireland", "sweden",
                 "denmark", "finland", "austria", "belgium", "czechia", "czech republic", "romania", "greece", "hungary"]
for _c in _EU_COUNTRIES:
    REGION_ALIASES[_c] = [_c] + _EUROPE

TECH_TERMS = [
    "Python", "Django", "Flask", "FastAPI", "Java", "Kotlin", "Scala", "Go", "Golang", "Rust", "C++", "C#", ".NET",
    "Ruby", "Rails", "PHP", "Laravel", "Elixir", "JavaScript", "TypeScript", "Node.js", "React", "Next.js", "Vue",
    "Angular", "Svelte", "GraphQL", "REST", "gRPC", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "RabbitMQ",
    "Elasticsearch", "ClickHouse", "Snowflake", "BigQuery", "dbt", "Airflow", "Spark", "AWS", "GCP", "Azure",
    "Kubernetes", "Docker", "Terraform", "Ansible", "Linux", "CI/CD", "Microservices", "Distributed Systems",
    "Machine Learning", "PyTorch", "TensorFlow", "LLM", "iOS", "Android", "Swift", "React Native", "Flutter", "SQL",
]


@dataclass
class CandidatePrefs:
    target_titles: List[str] = field(default_factory=list)
    seniority: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    country: Optional[str] = None
    remote_scope: str = "WORLDWIDE"
    allowed_regions: List[str] = field(default_factory=list)
    min_salary: Optional[float] = None  # empty: any pay is fine
    salary_currency: Optional[str] = None
    excluded_companies: List[str] = field(default_factory=list)
    role_min_salary: Dict[str, float] = field(default_factory=dict)  # target title -> its own floor


def parse_role_floors(raw: Any) -> Dict[str, float]:
    """{"Backend Engineer": "40000"} from the intake; blank or non-numeric entries are dropped."""
    out: Dict[str, float] = {}
    for title, value in (raw or {}).items() if isinstance(raw, dict) else ():
        try:
            amount = float(str(value).replace(",", "").strip())
        except ValueError:
            continue
        if title.strip() and amount > 0:
            out[title.strip()] = amount
    return out


def salary_floor(title: str, prefs: CandidatePrefs) -> Optional[float]:
    """The floor for this role: its own entry if the title matches one, else the general minimum (or none)."""
    if prefs.role_min_salary:
        fit, matched = title_fit(title, CandidatePrefs(target_titles=list(prefs.role_min_salary)))
        if matched and fit >= 0.5:
            return prefs.role_min_salary[matched]
    return prefs.min_salary or None


@dataclass
class Evaluation:
    eligible: bool
    reason: str = ""
    score: int = 0
    breakdown: Dict[str, int] = field(default_factory=dict)
    matched_skills: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def bucket(self) -> str:
        if not self.eligible or self.score < MAYBE_THRESHOLD:
            return "DROP"
        return "QUEUE" if self.score >= QUEUE_THRESHOLD else "MAYBE"


def normalize_title(title: str) -> str:
    t = (title or "").lower().replace("-", " ").replace("/", " ")
    for a, b in (("back end", "backend"), ("front end", "frontend"), ("full stack", "fullstack"),
                 ("site reliability", "sre"), ("dev ops", "devops")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9+#. ]", " ", t)


def _contains_term(text: str, term: str) -> bool:
    flags = 0 if len(term) <= 2 else re.I  # "Go", "C#" and friends only in their exact case
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, flags) is not None


def title_fit(title: str, prefs: CandidatePrefs) -> Tuple[float, Optional[str]]:
    norm = normalize_title(title)
    words = set(norm.split())
    if not prefs.target_titles:
        return (0.6 if ROLE_NOUNS.search(norm) else 0.0), None
    best, best_title = 0.0, None
    for target in prefs.target_titles:
        tw = set(normalize_title(target).split())
        specific = tw - GENERIC_TITLE_WORDS
        role_ok = bool(ROLE_NOUNS.search(norm)) or not ROLE_NOUNS.search(target)
        if specific:
            hit = len(specific & words) / len(specific)
        else:  # e.g. "Software Engineer": every word is generic
            hit = len(tw & words) / len(tw) if tw else 0.0
        fit = hit if role_ok else hit * 0.4
        if fit > best:
            best, best_title = fit, target
    return best, best_title


_SENIOR_RANK = {"junior": 0, "mid": 1, "senior": 2, "staff": 3, "principal": 4, "lead / manager": 3}


def seniority_factor(title: str, seniority: Optional[str]) -> float:
    if not seniority:
        return 1.0
    rank = _SENIOR_RANK.get(seniority.lower(), 1)
    t = normalize_title(title)
    if re.search(r"\b(intern|junior|jr|graduate|entry)\b", t) and rank >= 2:
        return 0.5
    if re.search(r"\b(principal|director|vp|head|distinguished)\b", t) and rank <= 1:
        return 0.6
    if re.search(r"\b(staff)\b", t) and rank == 0:
        return 0.6
    if re.search(r"\b(senior|sr)\b", t) and rank == 0:
        return 0.8
    return 1.0


def region_eligible(regions: List[str], prefs: CandidatePrefs) -> Tuple[bool, str]:
    if not regions:
        return True, "Region not stated"
    text = " | ".join(regions).lower()
    if WORLDWIDE.search(text):
        return True, ""
    if not prefs.country:
        return True, "Set your country in the intake to filter by region"
    aliases = REGION_ALIASES.get(prefs.country.lower(), [prefs.country.lower()])
    aliases = aliases + [r.lower() for r in prefs.allowed_regions]
    for alias in aliases:
        if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", text):
            return True, ""
    return False, f"Restricted to {', '.join(regions)[:80]}"


def annual_salary(p: JobPosting) -> Optional[float]:
    top = p.salary_max or p.salary_min
    if not top:
        return None
    return top * 2000 if p.salary_period == "hour" else top


def evaluate(p: JobPosting, prefs: CandidatePrefs, remote_first: bool = False, now: Optional[datetime] = None) -> Evaluation:
    now = now or datetime.utcnow()
    company = (p.company or "").strip().lower()

    if any(company == x.strip().lower() for x in prefs.excluded_companies if x.strip()):
        return Evaluation(False, "Excluded company")
    if p.remote is False:
        return Evaluation(False, "Not remote")
    ok, region_note = region_eligible(p.regions, prefs)
    if not ok:
        return Evaluation(False, region_note)
    max_age = MAX_AGE_DAYS_COMPANY if p.is_company_board else MAX_AGE_DAYS_BOARD
    age_days = (now - p.posted_at).days if p.posted_at else None
    if age_days is not None and age_days > max_age:
        return Evaluation(False, f"Posted {age_days} days ago")

    fit, matched_title = title_fit(p.title, prefs)
    if fit < 0.5:
        return Evaluation(False, "Title doesn't match your target titles")
    salary = annual_salary(p)
    floor = salary_floor(p.title, prefs)
    same_currency = not prefs.salary_currency or not p.salary_currency or p.salary_currency.upper() == prefs.salary_currency.upper()
    if salary and floor and same_currency and salary < floor:
        return Evaluation(False, f"Pays up to {salary:,.0f}, below your floor of {floor:,.0f} for this role")

    # Skills: how much of what the job asks for the candidate already has
    text = f"{p.title}\n{' '.join(p.tags)}\n{p.description}"
    vocab = {t.lower(): t for t in TECH_TERMS}
    vocab.update({s.lower(): s for s in prefs.skills})
    job_skills = [v for v in vocab.values() if _contains_term(text, v)]
    have: Set[str] = {s.lower() for s in prefs.skills}
    matched = [s for s in job_skills if s.lower() in have]
    if job_skills:
        skills_ratio = len(matched) / min(len(job_skills), 8)
    else:
        skills_ratio = 0.5
    skills_pts = round(40 * min(1.0, skills_ratio))

    title_pts = round(25 * fit * seniority_factor(p.title, prefs.seniority))

    if not floor:
        salary_pts = 12
    elif salary is None or not same_currency:
        salary_pts = 9
    else:
        salary_pts = 15

    employer_pts = 10 if remote_first else (7 if p.is_company_board else 5)

    if age_days is None:
        fresh_pts = 5
    else:
        fresh_pts = 10 if age_days <= 2 else 8 if age_days <= 7 else 6 if age_days <= 14 else 4 if age_days <= 30 else 2

    breakdown = {"skills": skills_pts, "title": title_pts, "salary": salary_pts, "employer": employer_pts, "freshness": fresh_pts}
    notes = [n for n in (region_note,) if n]
    if matched_title:
        notes.append(f"Matches '{matched_title}'")
    return Evaluation(True, "", sum(breakdown.values()), breakdown, matched, notes)
