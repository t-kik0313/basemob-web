// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
function answerOf(iso, playerKey) {
        return (state.answers[iso] || {})[playerKey] || null;
    }

function plainName(value) {
        return String(value || "").replace(/[\s\u3000]/g, "");
    }

function guests() {
        const found = new Map();
        Object.values(state.answers).forEach(bucket => {
            Object.entries(bucket || {}).forEach(([key, record]) => {
                if (key.startsWith("n:") && record && record.name) found.set(key, record.name);
            });
        });
        return Array.from(found, ([player_id, name]) => ({ player_id, name }));
    }

function answerers() {
        return roster.concat(guests());
    }

function counts(iso) {
        let all = 0;
        let am = 0;
        let pm = 0;
        answerers().forEach(player => {
            const status = (answerOf(iso, String(player.player_id)) || {}).status;
            if (status === "all") all += 1;
            else if (status === "am") am += 1;
            else if (status === "pm") pm += 1;
        });
        return { am: all + am, pm: all + pm };
    }

function people(iso, status) {
        return answerers().filter(player => (answerOf(iso, String(player.player_id)) || {}).status === status);
    }

function unanswered(iso) {
        return roster.filter(player => !(answerOf(iso, String(player.player_id)) || {}).status);
    }

function effective(playerKey, iso) {
        const draft = answerDraft[playerKey] && answerDraft[playerKey][iso];
        if (draft) return draft;
        const saved = answerOf(iso, playerKey);
        if (saved) return { status: saved.status, by: saved.by || shiftDays(TODAY, 14) };
        return { status: "", by: shiftDays(TODAY, 14) };
    }

function ensureDraft(playerKey, iso) {
        answerDraft[playerKey] = answerDraft[playerKey] || {};
        if (!answerDraft[playerKey][iso]) {
            const current = effective(playerKey, iso);
            answerDraft[playerKey][iso] = { status: current.status, by: current.by };
        }
        return answerDraft[playerKey][iso];
    }

function sameAnswer(draft, saved) {
        const left = draft || { status: "", by: "" };
        const right = saved || { status: "", by: "" };
        if ((left.status || "") !== (right.status || "")) return false;
        if (left.status === "pending" && (left.by || "") !== (right.by || "")) return false;
        return true;
    }

function answerDirty(playerKey) {
        const draft = answerDraft[playerKey];
        if (!draft) return false;
        return Object.keys(draft).some(iso => !sameAnswer(draft[iso], answerOf(iso, playerKey)));
    }

function personKey() {
        if (!manualMode) return personId;
        const display = manualName.trim().slice(0, 40);
        const plain = plainName(display).slice(0, 40);
        if (!plain) return "";
        const hit = roster.find(player => plainName(player.name) === plainName(display));
        return hit ? String(hit.player_id) : `n:${plain}`;
    }

function rememberAnswering() {
        const key = personKey();
        if (manualMode && key.startsWith("n:")) rememberPerson(`manual:${manualName.trim().slice(0, 40)}`);
        else rememberPerson(key);
    }

function blankGame(slot) {
        return {
            slot: slot || "pm",
            opponent: "",
            eventName: "練習試合",
            stadium: "",
            address: "",
            uniform: "黒",
            bat: "情報なし",
            timeGather: "",
            timePB: "",
            bench: "",
            lineup: Array.from({ length: 10 }, () => ({ n: "", p: "" }))
        };
    }

function cloneGame(game) {
        const copy = blankGame(game && game.slot);
        if (!game) return copy;
        ["slot", "opponent", "eventName", "stadium", "address", "uniform", "bat", "timeGather", "timePB", "bench"].forEach(key => {
            if (game[key] != null) copy[key] = game[key];
        });
        copy.lineup = Array.from({ length: 10 }, (_, index) => {
            const row = (game.lineup || [])[index] || {};
            return { n: row.n || "", p: row.p || "" };
        });
        return copy;
    }

function gameCard(iso) {
        return document.querySelector(`[data-game="${iso}"]`);
    }

function tenthLabel(game) {
        const hasDh = game.lineup.slice(0, 9).some(row => row.p === "DH");
        const tenth = game.lineup[9] || {};
        return hasDh && tenth.p === "投" ? "P" : "10";
    }

function draftFor(iso) {
        if (!drafts[iso]) drafts[iso] = cloneGame(state.games[iso] || blankGame("pm"));
        return drafts[iso];
    }

function supportNames(iso, game) {
        const starters = new Set(game.lineup.map(row => row.n.trim()).filter(Boolean));
        return answerers().filter(player => {
            const status = (answerOf(iso, String(player.player_id)) || {}).status;
            const inSlot = game.slot === "pm" ? (status === "all" || status === "pm") : (status === "all" || status === "am");
            return inSlot && !starters.has(player.name);
        }).map(player => player.name);
    }

function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }

function conditionSrc(name) {
        const text = (boot.conditions || {})[name] || "普通";
        return (boot.icons || {})[text] || (boot.icons || {})["普通"] || "";
    }

function storedPerson() {
        try { return sessionStorage.getItem("schedule-person") || ""; }
        catch (error) { return ""; }
    }

function rememberPerson(id) {
        try { sessionStorage.setItem("schedule-person", id); }
        catch (error) { /* 保存できなくても回答自体は送れる */ }
    }

function setToast(message, bad) {
        toast = message || "";
        toastBad = Boolean(bad);
    }

function applyPoll(data) {
        state.removed = data.removed || [];
        state.added = data.added || [];
        state.answers = data.answers || {};
        if (Object.prototype.hasOwnProperty.call(data, "games")) state.games = data.games || {};
        setPeople(data.people, data.peopleCustom);
    }

function setPeople(people, custom) {
        if (!Array.isArray(people)) return;
        roster.splice(0, roster.length, ...people.map(person => ({ player_id: person.id, name: person.name })));
        state.peopleCustom = Boolean(custom);
        if (!manualMode && personId && !roster.some(player => String(player.player_id) === String(personId))) {
            personId = "";
            rememberPerson("");
        }
    }

function peoplePayload() {
        return roster.map(person => ({ id: String(person.player_id), name: person.name }));
    }

async function run(task) {
        if (busy) return;
        busy = true;
        try {
            await task();
        } catch (error) {
            setToast(error.message || "保存に失敗しました。", true);
        } finally {
            busy = false;
            render();
        }
    }
