# drbriancollins.github.io

Personal academic and professional site of Brian Collins, PhD, PMP®, published with GitHub Pages at <https://drbriancollins.github.io/>.

## Pages

| URL | Content |
|---|---|
| `/` | About, career, education, teaching |
| `/publications/` | Books, papers and presentations |
| `/grants/` | Funded research projects |
| `/student-supervision/` | Postgraduate supervision |
| `/technical-skills/` | Technical skills |
| `/certificates/` | Certification and training |
| `/other/` | Media coverage and professional service |

## Updating

The HTML is generated from the JSON files in `data/`. Python 3 is required; only the standard library is used.

1. Edit `data/site.json` (profile, grants, supervision, certificates, media) or `data/skills.json`.
2. For publications, update the Word file and re-import it:
   `python tools/import_publications.py "path/to/Collins_CV_Publications.docx"`
3. Rebuild: `python tools/build.py`
4. Commit and push. GitHub Pages republishes within a minute or two.
