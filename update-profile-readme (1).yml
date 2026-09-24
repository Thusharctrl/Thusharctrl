name: Update profile README

on:
  schedule:
    - cron: "0 */6 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-profile:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout profile repository
        uses: actions/checkout@v6

      - name: Update recent repositories
        env:
          GH_OWNER: ${{ github.repository_owner }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 update_profile.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add README.md

          if git diff --cached --quiet; then
            echo "No README changes."
            exit 0
          fi

          git commit -m "chore: update recent repositories"
          git push
