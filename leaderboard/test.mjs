// Plain-Node checks for the leaderboard rules (no Cloudflare runtime needed).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const src = readFileSync(new URL("./worker.js", import.meta.url), "utf8")
  .replace(/import \{ DurableObject \} from "cloudflare:workers";/, "class DurableObject {}");
const mod = await import("data:text/javascript;base64," + Buffer.from(src).toString("base64"));
const { maxScore, cleanName } = mod;

// Max scores line up with the game's scoring (base x1.5 speed, streak x1.5 from 3, x2 from 5).
assert.equal(maxScore("easy", 0), 0);
assert.equal(maxScore("easy", 1), 150);
assert.equal(maxScore("easy", 10), 150 * (2 + 1.5 * 2 + 2 * 6));
assert.equal(maxScore("hard", 10), 450 * 17);

for (const ok of ["BlitzKing", "QB 12", "Super_Fan", "Class Clown", "Mia-23", "Dieter", "Michelle", "Shelly", "Classy"]) assert.equal(cleanName(ok), ok, ok);
for (const bad of ["a", "ThisNameIsWayTooLong", "b1tch", "sh1t", "kid@mail.com", "5551234567", "Ass", "<script>", "Fvck", "Big Butt", "h3ll"]) {
  assert.equal(cleanName(bad), null, bad);
}
console.log("leaderboard rules OK");
