# Publish guide — Project 2

**Do not start until every item in `docs/VERIFICATION.md` is checked.** Release only after the real-data run, your verification, and the authorship discussion.

## 0. Pre-flight (about 5 minutes)

```bash
grep -rn "DRAFT\|\[VERIFY\|PLACEHOLDER\|SYNTHETIC" README.md CITATION.cff AUTHORS.json manuscript docs | head
```

Clear each hit, or decide on purpose to keep it:
- **ORCID:** replace `PLACEHOLDER` in `AUTHORS.json` and `CITATION.cff` with your ORCID iD.
- **Co-authors:** fill in only after the Merchant authorship discussion.
- **Version:** set `version: 1.0.0` in `CITATION.cff` and `pyproject.toml`.

## 1. GitHub (about 5 minutes)

```bash
cd p2-yrbs-provenance
git remote add origin https://github.com/<your-user>/p2-yrbs-provenance.git
git push -u origin main          # or master, whichever branch name git shows
git tag -a v1.0.0 -m "Project 2 v1.0.0" && git push origin v1.0.0
```

1. Create the empty repository on github.com first (no README).
2. **Never commit `data/raw`, `data/interim`, `data/processed`, or `results/preds`.** `.gitignore` already excludes them. Only aggregate outputs belong in the repository.

## 2. Zenodo DOI (about 10 minutes)

1. Sign in at zenodo.org with your ORCID.
2. Under Settings → GitHub, switch on the repository.
3. On GitHub, publish a Release from tag `v1.0.0`. Zenodo archives it and mints a DOI.
4. Edit the Zenodo record:
   - creators from `AUTHORS.json`, with ORCID;
   - license: MIT;
   - keywords: YRBS, missing data, survey methodology, suicide prevention, prediction;
   - related identifier: the CDC YRBS data page.
5. Add the DOI badge to `README.md`, and the DOI to `CITATION.cff`. Commit and push.

## 3. Log it

Record each step the same day:
- URL;
- DOI;
- date;
- screenshot of the confirmation.

## What I can automate

If you give me a GitHub token (scope: `repo`) and a Zenodo token (scopes: `deposit:write`, `deposit:actions`) for one session, I can do steps 1 and 2 myself. Use the Zenodo sandbox first, then revoke both tokens afterwards.

**Not automatable:** journal submission and the CSTE abstract. Both require your personal attestation.
