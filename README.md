# JobScout

Resume upload karo -> skills aur experience level apne aap nikalte hain -> fresh jobs skill match, freshness aur level se rank hoti hain -> cover letter + application tracker.

- Resume sirf aapke browser me padha jata hai. Kisi server par upload nahi hota.
- Free hosting: GitHub Pages. Jobs ka data: GitHub Actions har 12 ghante me `jobs.json` update karta hai.
- Phone par app ki tarah install hota hai (PWA).

## Files

| File | Kaam |
|---|---|
| `index.html` | Poora app (UI, resume padhna, ranking, tracker) |
| `jobs.json` | Fresh jobs ka data (Actions isse bharta hai) |
| `config.json` | Aapke keywords aur countries. **Isse apne field ke hisaab se badlo** |
| `scripts/fetch_jobs.py` | Jobs fetch karne wali script |
| `.github/workflows/refresh-jobs.yml` | 12 ghante wala schedule |
| `vendor/` | PDF aur DOCX padhne ki libraries (licenses `vendor/LICENSES.txt`) |
| `manifest.webmanifest`, `sw.js`, `icons/` | Phone par install aur offline |

## Setup (short)

1. GitHub par naya **public** repo banao, naam `jobscout`.
2. Ye saari files (hidden `.github` folder ke saath) us repo me daalo.
3. Settings -> Pages -> Source: `Deploy from a branch` -> `main` / `(root)`.
4. Settings -> Secrets and variables -> Actions me keys daalo (optional par zaroori hain US, India, Australia, UK, Canada, Singapore, Dubai ke liye):
   - `ADZUNA_ID`, `ADZUNA_KEY` (developer.adzuna.com, free)
   - `JOOBLE_KEY` (jooble.org/api/about, free)
5. Actions tab -> `Refresh jobs` -> `Run workflow`.
6. App: `https://<aapka-username>.github.io/jobscout/`

## Experience level

Jobs tab me Sab, Fresher, Mid, Senior, Lead / Manager tabs hain. Level job ke title aur description se pehchana jata hai (jaise Intern, Junior, Senior, Lead, "5+ years experience"). Job me level na likha ho to use Mid maana jata hai. Aapka level resume ke saalon se nikalta hai, aur Profile tab me badla ja sakta hai.

## Jo data milta hai

- Remotive (remote jobs, 24 ghante delayed) aur Arbeitnow (Europe): bina key ke.
- Adzuna: US, India, Australia, UK, Canada, Singapore, Germany, Netherlands, France.
- Jooble: Dubai/UAE.
- Applicant count kisi free source me nahi aata. Isliye "kam applicants" ka andaza posting ki freshness se lagaya jata hai.

## Optional: AI cover letter

Profile tab me apni Anthropic API key daalo. Key sirf aapke browser me rehti hai aur seedha Anthropic ko jati hai. Spend limit wali key use karo.
