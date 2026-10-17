"""
OpportunityOS — Resume upload from the intake form: stored on this Mac and set as the master resume or a variant.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.db import init_db
from apps.api.main import app


@pytest.mark.asyncio
async def test_resume_upload_sets_master_and_variant(tmp_path, monkeypatch):
    await init_db()
    monkeypatch.setattr("apps.worker.automation.OOS_HOME", tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        before = (await client.get("/api/intake")).json()["documents"]
        try:
            res = await client.post("/api/intake/resume", files={"file": ("My Resume (2026).pdf", b"%PDF-1.4 x", "application/pdf")})
            assert res.status_code == 200, res.text
            master = res.json()["documents"]["master_resume_path"]
            assert master == str((tmp_path / "resumes" / "My-Resume-2026.pdf").resolve())
            assert (tmp_path / "resumes" / "My-Resume-2026.pdf").read_bytes() == b"%PDF-1.4 x"

            res = await client.post("/api/intake/resume", data={"variant": "backend-v2"},
                                    files={"file": ("cv.docx", b"PK docx", "application/octet-stream")})
            docs = res.json()["documents"]
            assert docs["master_resume_path"] == master  # a variant leaves the master alone
            assert docs["resume_variants"]["backend-v2"].endswith("resumes/backend-v2-cv.docx")

            bad = await client.post("/api/intake/resume", files={"file": ("photo.png", b"png", "image/png")})
            assert bad.status_code == 400 and "PDF" in bad.json()["detail"]
            empty = await client.post("/api/intake/resume", files={"file": ("cv.pdf", b"", "application/pdf")})
            assert empty.status_code == 400
        finally:
            await client.put("/api/intake", json={"documents": before})
