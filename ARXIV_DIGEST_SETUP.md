# Leif's Weekly arXiv digest: setup

The digest is integrated into your existing personal website checkout at
`/Users/leifl/PKU_Research/misc/leiflui.github.io`. It adds a page at
`https://leiflui.github.io/arxiv-digest/`, with its navigation link between Teaching and Blog Posts.
Publishing uses your website's existing `master` branch.

## What you get

- Your chosen 13 topics, including common spelling and acronym variants.
- New papers and updated papers in separate sections.
- Distinct collaborator and notable-author badges, with optional author-only inclusion.
- A weekly archive, links to arXiv and PDFs, and a JSON download of every match.
- A Tuesday 08:17 Hong Kong schedule using arXiv's public API. No paid API keys are required.

This version matches titles and abstracts. It does not claim to read full papers, assess
scientific quality, or reproduce Vojtěch's full critical-review process. You can download
an issue's JSON and ask ChatGPT to review selected papers using your existing subscription.

## Step 1: select your existing website in GitHub Desktop

1. Open GitHub Desktop.
2. Under **Current Repository**, select **leiflui.github.io**.
3. Confirm the repository folder is `/Users/leifl/PKU_Research/misc/leiflui.github.io`.
4. Confirm **Current Branch** is **master**.
5. Open **History** to review the commit that adds the weekly digest.

This folder already points to `leiflui/leiflui.github.io`; do not create another GitHub repository.

## Step 2: push the website changes

1. Click **Push origin** in GitHub Desktop.
2. Wait for the push to finish. If there are no outgoing commits, the changes may already be pushed.
3. Continue with the Pages settings below to enable automatic weekly publishing.

No API secrets need to be added. The workflow uses GitHub's built-in token to archive issues
and deploy your website. Pushing `master` builds the page; manual and scheduled runs also collect papers.

## Step 3: select the GitHub Pages publishing source

1. Open `https://github.com/leiflui/leiflui.github.io/settings/pages`.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Keep your existing custom domain if you have one.

This is a publishing-source change for your complete existing Jekyll website. The supplied
workflow builds the whole site, including the new page. It deploys directly after weekly
collection, because a commit made with GitHub's built-in token does not trigger another Pages build.

## Step 4: make the first real issue

1. Open `https://github.com/leiflui/leiflui.github.io/actions`.
2. Select **Weekly arXiv digest and website**.
3. Click **Run workflow**, choose `master`, then click the green **Run workflow** button.
4. Wait for both the build and deploy jobs to finish successfully.
5. Visit `https://leiflui.github.io/arxiv-digest/`.

The schedule then runs each Tuesday at 08:17 Hong Kong time, subject to GitHub delays.
Each issue covers the previous seven days ending Tuesday 00:00 Hong Kong time. Manual
reruns in the same week replace that issue, rather than creating duplicate archive entries.

## Change topics, exclusions and author flags

Edit `_data/arxiv_preferences.json` in GitHub Desktop or GitHub's file editor.

- `topics`: named groups of keyword aliases. Matching is case-insensitive and normalises dashes.
  A matching topic in the title scores two points; an abstract-only match scores one.
- `categories`: source categories. The initial scope is gr-qc, astro-ph.HE, astro-ph.GA,
  astro-ph.CO and hep-th, chosen to cover the selected gravity, lensing and simulation topics.
- `exclude_keywords`: phrases that always exclude a paper, even if an author is flagged.
- `author_flags.collaborators`: names to show with a green collaborator badge.
- `author_flags.notable_authors`: names to show with a gold notable-author badge.
- `author_aliases`: alternate spellings for a flagged person, matched under the original badge name.
- `include_flagged_authors`: `true` includes papers by a flagged author within the selected
  categories even if none of the topic keywords match. Set `false` to flag topic matches only.
- `max_papers`: number of papers displayed, initially 20. Every match stays in the JSON download.

Your 11 collaborators and 20 notable authors are already configured. To add more names,
edit those lists. For example:

```json
"author_flags": {
  "collaborators": ["First Collaborator", "Second Collaborator"],
  "notable_authors": ["First Notable Author"]
}
```

Use the name as arXiv displays it. Matching ignores accents, punctuation, case and optional
middle initials, so "Scott A. Hughes" matches "Scott Hughes". First initials are not expanded
to full names. Add alternate spellings in `author_aliases`; each person still receives one badge.
Your confirmed spellings are configured as follows:

```json
"author_aliases": {
  "Nicholas Yunes": ["Nicolás Yunes"],
  "João S. Santos": ["João Sieiro dos Santos"]
}
```

The demo uses clearly fictional example names.
Topics and author flags live in a public website repository and are visible to visitors.

After editing preferences, commit and push. Run the workflow manually to regenerate the current
issue immediately, or wait for Tuesday. Each issue keeps its matching results and topic labels; preference edits affect the next generated issue.

## Local checks and preview

Python 3.12+ is sufficient; no Python packages or API accounts are needed.

```sh
python3 -m unittest discover -s tests -p test_arxiv_digest.py -v
python3 scripts/arxiv_digest.py --demo
python3 scripts/arxiv_digest.py --preview
```

The offline demonstration is `local/arxiv-demo/index.html`; all its records are fictional and
paper links are disabled. The live preview is `local/arxiv-preview/index.html`. Both directories
are ignored by Git and excluded from the published website. Run without `--preview` to generate
real website files locally. `--week-ending YYYY-MM-DD` can select a completed Tuesday explicitly.

For a complete local Jekyll build, use the website's normal Ruby/Bundler setup described in its
original README. The standalone preview checks the digest layout without rebuilding the full site.

## Limits and failures

- arXiv requests are serial, at least three seconds apart, with bounded retries.
- The generator follows result pages until it reaches the beginning of the issue's window.
  It fails at 5,000 scanned records instead of silently publishing a truncated week.
- A failed or invalid API response does not replace existing reports. Zero matches from a valid,
  fully traversed window is a successful issue and is labelled as such.
- Cross-lists merge by arXiv ID. Updated versions may appear again in a later issue's update section.
- Indexing delays can affect weekly boundaries. This is not a guarantee that every relevant paper
  was found; a paper without a selected topic or author match is omitted.
- If branch protection prevents the bot from archiving, the collection job fails and leaves the
  existing site intact. Adjust that rule for your repository or use a review-based publishing flow.
- The schedule runs only on `master`. Do not manually deploy the review branch.
- GitHub Pages hosting and standard Actions runners for public repositories are covered by GitHub's
  free offering, subject to platform limits. No paid search or model calls are made by this workflow.

## Sources

- arXiv API: https://info.arxiv.org/help/api/user-manual.html
- arXiv rate limits and reuse rules: https://info.arxiv.org/help/api/tou.html
- GitHub Pages custom workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Inspiration: https://github.com/VojtechW/vojtechs-arxiv-digest
