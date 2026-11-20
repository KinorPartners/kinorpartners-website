# Trivia leaderboard

A small Cloudflare Worker that keeps the online Top 10 for the kids' football
trivia game at `/pages/football-trivia-2026/`. It runs on Cloudflare's free plan.

It stores only a nickname, a score, how many answers were right, the level and
the time. No email, age or IP address is kept. IP addresses are hashed with the
date and used only to rate-limit, and those hashes are deleted after a day.

## Turning it on

1. In Cloudflare, create an API token from the **Edit Cloudflare Workers** template.
2. In this repo's settings, under Secrets and variables > Actions, add:
   - `CLOUDFLARE_API_TOKEN` (the token)
   - `CLOUDFLARE_ACCOUNT_ID` (optional, if the token can see more than one account)
3. Run the **Deploy trivia leaderboard** workflow (or push a change under `leaderboard/`).
   The deploy log prints the Worker's `https://...workers.dev` address.
4. Put that address in `var API = "";` in
   `src/pages/football-trivia-2026/index.html` and merge. The game then shows
   the 🌎 Everyone board and the "Post my score" switch.

Until step 4, the game works exactly the same with scores saved on the device only.

## Optional secrets (set with `wrangler secret put`)

- `ADMIN_KEY`: lets you remove one entry with
  `DELETE /scores?level=easy&t=<time>` and header `X-Admin-Key`.
- `SALT`: any random text, used when hashing IPs for rate limiting.

## Rules the server enforces

- Nickname 2 to 14 letters, numbers, spaces, `_` or `-`, no long number runs,
  and a word filter (including look-alike spellings).
- A round token must be fetched when a round starts and used once, at least
  15 seconds later and within an hour.
- The score must be possible for that level and number of right answers.
- 60 rounds and 20 score posts per hour per player.

Run `node leaderboard/test.mjs` to check the scoring and name rules.
