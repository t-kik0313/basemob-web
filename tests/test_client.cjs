/* Browser renderer tests, using the same vendored engine and actual views. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const nunjucks = require(path.join(root, "static/vendor/nunjucks-3.2.4.min.js"));
const create = require(path.join(root, "static/app/renderer.js"))(nunjucks).createRenderer;
const renderer = create(JSON.parse(fs.readFileSync(path.join(root, "static/app/views.json"), "utf8")));
renderer.compileAll();

const meta = {
    team_slug: "demo",
    routes: {
        static: "/static/<path:filename>", players: "/players", teamstats: "/teamstats",
        annual_stats_detail: "/annual_stats_detail", schedule: "/schedule", events: "/events",
        register_player: "/register_player", qualitative_abilities: "/admin/qualitative_abilities",
        regulation_settings: "/admin/regulation", player_detail_R1: "/player_detail_R1/<int:player_id>",
        player_history: "/player_history/<int:player_id>",
    },
};
const base = { team_name: "テストチーム", score_entry_url: "https://example.com/score", request: { args: {} } };
const malicious = '<script>alert("test")</script>';
const players = renderer.render({ view: "players.njk", meta, data: {
    ...base, players: [{ player_id: 1, name: malicious, no: "1", image_path: "test image.png", pos1: "遊" }],
} });
assert(players.includes("&lt;script&gt;"));
assert(!players.includes(malicious));
assert(players.includes("/t/demo/player_detail_R1/1"));
assert(players.includes("/static/test%20image.png"));

const history = renderer.render({ view: "player_history.njk", meta, data: {
    ...base, player: { id: 1, name: "選手A" }, history_stats: [], total_stats: {},
} });
assert(history.includes("過去の成績データはありません。"));

const annual = renderer.render({ view: "annual_stats_detail.njk", meta, data: {
    ...base, regulation_pa: 2,
    stats: [{ id: 1, name: "選手A", avg: 2 / 3, obp: .75, qualified: true }], team_total: {},
} });
assert(annual.includes(".667"));
assert(!annual.includes(".6,6,7"));

const abilities = renderer.render({ view: "pawapuro.njk", meta, data: {
    ...base, players_data: [{ player_id: 1, name: malicious }],
} });
assert(abilities.includes("\\u003cscript\\u003e"));
assert(!abilities.includes(malicious));

if (process.argv[2] === "--fixtures") {
    const fixtures = JSON.parse(fs.readFileSync(0, "utf8"));
    for (const payload of fixtures) assert(renderer.render(payload).includes("<!DOCTYPE html>"));
    console.log("PASS: " + fixtures.length + " screen payloads rendered");
}
console.log("PASS: all client templates compile; escaping, URLs, empty states and numeric formatting");
