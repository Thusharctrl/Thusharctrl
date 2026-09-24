name: Update profile README

on:
  schedule:
    - cron: "0 */12 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-profile:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout profile repository
        uses: actions/checkout@v6

      - name: Generate recent repositories section
        env:
          GH_OWNER: ${{ github.repository_owner }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        shell: bash
        run: |
          set -euo pipefail

          api="https://api.github.com/users/${GH_OWNER}/repos?per_page=100&sort=updated&direction=desc"

          repos="$(curl -fsSL             -H "Accept: application/vnd.github+json"             -H "Authorization: Bearer ${GH_TOKEN}"             -H "X-GitHub-Api-Version: 2022-11-28"             "${api}")"

          body="$(
            echo "${repos}" |
            jq -r --arg owner "${GH_OWNER}" '
              map(select(.fork == false and .name != $owner))
              | .[:6]
              | if length == 0 then
                  "| _No public repositories found yet._ | — | — | — |"
                else
                  .[] |
                  "| [\(.name)](\(.html_url)) | \((.description // "No description") | gsub("\r|\n"; " ")) | \((.language // "—")) | \(.updated_at[0:10]) |"
                end
            '
          )"

          export GENERATED_BODY="${body}"

          python3 - <<'PY'
          from pathlib import Path
          import os

          path = Path("README.md")
          text = path.read_text(encoding="utf-8")

          start = "<!-- PROJECTS:START -->"
          end = "<!-- PROJECTS:END -->"

          if start not in text or end not in text:
              raise SystemExit("README markers were not found.")

          body = os.environ["GENERATED_BODY"]

          start_i = text.index(start) + len(start)
          end_i = text.index(end)

          replacement = (
              "\n| Repository | Description | Language | Updated |\n"
              "|---|---|---|---|\n"
              + body
              + "\n"
          )

          text = text[:start_i] + replacement + text[end_i:]
          path.write_text(text, encoding="utf-8")
          PY

      - name: Commit changes
        shell: bash
        run: |
          set -euo pipefail

          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add README.md

          if git diff --cached --quiet; then
            echo "No README changes."
            exit 0
          fi

          git commit -m "chore: update recent repositories"
          git push
