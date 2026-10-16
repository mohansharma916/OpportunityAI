"""
LinkedIn profile snapshot: what the candidate's profile looks like right now.
Filled either by screen-reading the live profile (apps/worker/linkedin.py) or from
LinkedIn's "Get a copy of your data" export. A field that could not be read is None,
so the audit can say "unknown" instead of guessing.
"""

import csv
import io
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Experience(BaseModel):
    title: str = ""
    company: str = ""
    description: str = ""
    location: str = ""
    start: str = ""
    end: str = ""


class ProfileSnapshot(BaseModel):
    source: str = "SCREEN"  # SCREEN or EXPORT
    name: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
    open_to_work: Optional[bool] = None
    has_photo: Optional[bool] = None
    has_banner: Optional[bool] = None
    experiences: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    featured_count: Optional[int] = None
    recommendations_count: Optional[int] = None
    education_count: Optional[int] = None
    certifications_count: Optional[int] = None


def _rows(text: str, must_have: str) -> List[Dict[str, str]]:
    """Parse a LinkedIn export CSV; some files carry note lines before the header."""
    lines = text.lstrip("﻿").splitlines()
    start = next((i for i, line in enumerate(lines) if must_have in line), None)
    if start is None:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def _read_export_files(path: Path) -> Dict[str, str]:
    files: Dict[str, str] = {}
    if path.is_dir():
        for p in path.rglob("*.csv"):
            files[p.name] = p.read_text(encoding="utf-8", errors="replace")
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".csv"):
                    files[Path(name).name] = zf.read(name).decode("utf-8", errors="replace")
    else:
        raise ValueError(f"{path} is not a LinkedIn export folder or .zip")
    return files


def parse_export(path: str) -> ProfileSnapshot:
    """Build a snapshot from LinkedIn's data export (zip or extracted folder)."""
    files = _read_export_files(Path(path).expanduser())
    if "Profile.csv" not in files:
        raise ValueError("Profile.csv not found in the export. Request 'Profile' data from LinkedIn.")

    profile = (_rows(files["Profile.csv"], "First Name") or [{}])[0]
    name = " ".join(p for p in (profile.get("First Name"), profile.get("Last Name")) if p) or None

    experiences = [
        Experience(
            title=r.get("Title", ""),
            company=r.get("Company Name", ""),
            description=r.get("Description", ""),
            location=r.get("Location", ""),
            start=r.get("Started On", ""),
            end=r.get("Finished On", ""),
        )
        for r in _rows(files.get("Positions.csv", ""), "Company Name")
    ]
    skills = [r["Name"] for r in _rows(files.get("Skills.csv", ""), "Name") if r.get("Name")]

    def count(filename: str, header: str) -> Optional[int]:
        return len(_rows(files[filename], header)) if filename in files else None

    return ProfileSnapshot(
        source="EXPORT",
        name=name,
        headline=profile.get("Headline") or None,
        about=profile.get("Summary") or None,
        location=profile.get("Geo Location") or None,
        experiences=experiences,
        skills=skills,
        recommendations_count=count("Recommendations_Received.csv", "First Name"),
        education_count=count("Education.csv", "School Name"),
        certifications_count=count("Certifications.csv", "Name"),
        # Not in the export: photo, banner, open-to-work, featured, custom URL
    )
