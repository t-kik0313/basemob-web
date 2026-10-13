(function () {
    const boot = window.SCHEDULE_BOOT || {};
    const roster = boot.roster || [];
    const rosterNames = roster.map(player => player.name);
    const READY = 7;
    const MARK = 9;
    const DOW = "日月火水木金土";
    const MANUAL = "__manual__";
    const POSITIONS = ["投", "捕", "一", "二", "三", "遊", "左", "中", "右", "DH"];
    const positionColors = {
        "投": "#ff7eae", "捕": "#5ec8f5",
        "一": "#ffe14a", "二": "#ffe14a", "三": "#ffe14a", "遊": "#ffe14a",
        "左": "#7ed957", "中": "#7ed957", "右": "#7ed957",
        "DH": "#ffb020"
    };
    const STADIUMS = {
        "大田スタジアム": "東京都大田区東海1-2-1",
        "多摩川緑地広場野球場": "東京都大田区本羽田3-29",
        "駒沢オリンピック公園総合運動場野球場": "東京都世田谷区駒沢公園1-1",
        "等々力球場": "神奈川県川崎市中原区等々力1-1",
        "世田谷公園野球場": "東京都世田谷区池尻1-5-27"
    };
    const choiceMeta = [
        ["all", "終日"], ["am", "午前だけ"], ["pm", "午後だけ"], ["pending", "未定"], ["out", "不参加"]
    ];

    const todayDate = new Date();
    todayDate.setHours(0, 0, 0, 0);
    const rangeEnd = new Date(todayDate.getFullYear(), todayDate.getMonth() + 2, 0);
    const TODAY = isoDate(todayDate);
    const RANGE_END = isoDate(rangeEnd);
    const monthTitle = `${todayDate.getMonth() + 1}月・${rangeEnd.getMonth() + 1}月の日程調整`;
    const answerTitle = `${todayDate.getMonth() + 1}月・${rangeEnd.getMonth() + 1}月の出欠`;

    const state = { removed: [], added: [], answers: {}, games: {} };
    const answerDraft = {};
    const drafts = {};
    let view = boot.loggedIn ? "board" : "answer";
    let openId = "";
    let activeGame = "";
    let pendingRemove = null;
    let toast = "";
    let toastBad = false;
    let busy = false;
    let scrollTo = "";
    let personId = storedPerson();
    if (!roster.some(player => String(player.player_id) === personId)) {
        personId = roster[0] ? String(roster[0].player_id) : "";
    }

    const app = document.getElementById("app");

    function isoDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, "0");
        const d = String(date.getDate()).padStart(2, "0");
        return `${y}-${m}-${d}`;
    }
    function parseDate(value) {
        const [y, m, d] = value.split("-").map(Number);
        return new Date(y, m - 1, d);
    }
    function shiftDays(value, delta) {
        const date = parseDate(value);
        date.setDate(date.getDate() + delta);
        return isoDate(date);
    }
    function nthWeekday(year, monthIndex, weekday, n) {
        const first = new Date(year, monthIndex, 1);
        const offset = (weekday - first.getDay() + 7) % 7;
        return 1 + offset + (n - 1) * 7;
    }
    function equinoxDay(year, spring) {
        const dy = year - 1980;
        const base = spring ? 20.8431 : 23.2488;
        return Math.floor(base + 0.242194 * dy) - Math.floor(dy / 4);
    }
    function holidayMap(year) {
        const map = new Map();
        const add = (month, day, name) => {
            const key = isoDate(new Date(year, month - 1, day));
            if (!map.has(key)) map.set(key, name);
        };
        add(1, 1, "元日");
        add(1, nthWeekday(year, 0, 1, 2), "成人の日");
        add(2, 11, "建国記念の日");
        add(2, 23, "天皇誕生日");
        add(3, equinoxDay(year, true), "春分の日");
        add(4, 29, "昭和の日");
        add(5, 3, "憲法記念日");
        add(5, 4, "みどりの日");
        add(5, 5, "こどもの日");
        add(7, nthWeekday(year, 6, 1, 3), "海の日");
        add(8, 11, "山の日");
        add(9, nthWeekday(year, 8, 1, 3), "敬老の日");
        add(9, equinoxDay(year, false), "秋分の日");
        add(10, nthWeekday(year, 9, 1, 2), "スポーツの日");
        add(11, 3, "文化の日");
        add(11, 23, "勤労感謝の日");
        for (const key of [...map.keys()].sort()) {
            if (parseDate(key).getDay() !== 0) continue;
            const cursor = parseDate(key);
            do { cursor.setDate(cursor.getDate() + 1); } while (map.has(isoDate(cursor)));
            map.set(isoDate(cursor), "振替休日");
        }
        let changed = true;
        while (changed) {
            changed = false;
            const keys = [...map.keys()].sort();
            for (let i = 0; i < keys.length - 1; i++) {
                const gap = (parseDate(keys[i + 1]) - parseDate(keys[i])) / 86400000;
                if (gap !== 2) continue;
                const mid = parseDate(keys[i]);
                mid.setDate(mid.getDate() + 1);
                const midKey = isoDate(mid);
                if (!map.has(midKey) && mid.getDay() !== 0) {
                    map.set(midKey, "国民の休日");
                    changed = true;
                }
            }
        }
        return map;
    }
    const holidays = new Map();
    for (let year = todayDate.getFullYear(); year <= rangeEnd.getFullYear(); year++) {
        for (const [key, name] of holidayMap(year)) holidays.set(key, name);
    }

    function isRoutine(iso) {
        const date = parseDate(iso);
        return Boolean(holidays.get(iso) || date.getDay() === 0 || date.getDay() === 6);
    }
    function visible() {
        const removed = new Set(state.removed);
        const added = new Set(state.added);
        const list = [];
        for (let cursor = new Date(todayDate); cursor <= rangeEnd; cursor.setDate(cursor.getDate() + 1)) {
            const iso = isoDate(cursor);
            if (removed.has(iso)) continue;
            const holidayName = holidays.get(iso) || "";
            const dow = cursor.getDay();
            const routine = Boolean(holidayName) || dow === 0 || dow === 6;
            if (!added.has(iso) && !routine) continue;
            list.push({
                iso,
                md: `${cursor.getMonth() + 1}/${cursor.getDate()}`,
                dow: DOW[dow],
                kind: holidayName ? "hol" : (dow === 6 ? "sat" : dow === 0 ? "sun" : "plain"),
                extra: added.has(iso) && !routine ? "追加" : holidayName
            });
        }
        return list;
    }
    function answerOf(iso, playerKey) {
        return (state.answers[iso] || {})[playerKey] || null;
    }
    function counts(iso) {
        let all = 0;
        let am = 0;
        let pm = 0;
        roster.forEach(player => {
            const status = (answerOf(iso, String(player.player_id)) || {}).status;
            if (status === "all") all += 1;
            else if (status === "am") am += 1;
            else if (status === "pm") pm += 1;
        });
        return { am: all + am, pm: all + pm };
    }
    function people(iso, status) {
        return roster.filter(player => (answerOf(iso, String(player.player_id)) || {}).status === status);
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
    function blankGame(slot) {
        return {
            slot: slot || "pm",
            opponent: "",
            eventName: "公式戦",
            stadium: "",
            address: "",
            uniform: "黒",
            bat: "ウレタン可",
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
        enforceDh(copy);
        return copy;
    }
    function enforceDh(game) {
        if (game.lineup.slice(0, 9).some(row => row.p === "DH")) game.lineup[9].p = "投";
    }
    function draftFor(iso) {
        if (!drafts[iso]) drafts[iso] = cloneGame(state.games[iso] || blankGame("pm"));
        return drafts[iso];
    }
    function supportNames(iso, game) {
        const starters = new Set(game.lineup.map(row => row.n.trim()).filter(Boolean));
        return roster.filter(player => {
            const status = (answerOf(iso, String(player.player_id)) || {}).status;
            const inSlot = game.slot === "pm" ? (status === "all" || status === "pm") : (status === "all" || status === "am");
            return inSlot && !starters.has(player.name);
        }).map(player => player.name);
    }
    function gameDays() {
        return visible().filter(day => state.games[day.iso]);
    }
    function currentGameId() {
        const days = gameDays();
        if (activeGame && days.some(day => day.iso === activeGame)) return activeGame;
        const upcoming = days.find(day => day.iso >= TODAY);
        return (upcoming || days[0] || {}).iso || "";
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
    }
    async function postPoll(body) {
        const response = await fetch(boot.pollApi, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || "保存に失敗しました。");
        applyPoll(data);
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

    function toastHtml() {
        if (!toast) return "";
        return `<div class="toast${toastBad ? " bad" : ""}">${esc(toast)}</div>`;
    }
    function memberHead() {
        const tabs = [["board", "調整ボード"], ["answer", "回答シート"], ["game", "試合カード"]];
        const buttons = tabs.map(([id, label]) => `<button type="button" data-view="${id}" class="${view === id ? "on" : ""}">${label}</button>`).join("");
        const title = view === "game" ? "試合カード" : (view === "answer" ? answerTitle : monthTitle);
        return `<header class="site"><h1>${title}</h1><div class="view-switch">${buttons}</div></header>`;
    }
    function meter(count, slot, hot) {
        const peopleCount = Math.max(roster.length, 1);
        const width = Math.min(100, count / peopleCount * 100);
        const mark = Math.min(100, MARK / peopleCount * 100);
        const label = slot === "pm" ? "午後" : "午前";
        return `<div class="slot${hot ? " up" : ""}"><span class="k">${label}</span><span class="n">${count}</span><span class="meter"><i style="width:${width}%"></i><em style="left:${mark}%"></em></span></div>`;
    }
    function scale() {
        if (!roster.length) return "";
        const ticks = Array.from({ length: roster.length }, () => "<span></span>").join("");
        return `<div class="tick-row"><span></span><span></span><div class="ticks" style="--people:${roster.length}">${ticks}</div></div>`;
    }
    function goButton(day, slot) {
        const label = slot === "pm" ? "この日の午後で進める" : "この日の午前で進める";
        return `<button type="button" class="go" data-go="${day.iso}" data-slot="${slot}">${label}</button>`;
    }
    function nameChips(players) {
        if (!players.length) return '<span class="empty">なし</span>';
        return players.map(player => `<span class="chip">${esc(player.name)}</span>`).join("");
    }
    function pendingChips(iso, players) {
        if (!players.length) return '<span class="empty">なし</span>';
        return players.map(player => {
            const answer = answerOf(iso, String(player.player_id)) || {};
            const late = answer.by && answer.by < TODAY;
            const when = String(answer.by || "").slice(5).replace("-", "/");
            return `<span class="chip${late ? " late" : ""}">${esc(player.name)}（${esc(when)}${late ? "・期限超過" : ""}）</span>`;
        }).join("");
    }
    function dateField(attrs) {
        return `<label class="date-field"><input type="date" ${attrs}><span class="date-ph">年/月/日</span></label>`;
    }
    function addControls(phone) {
        const cls = phone ? "add-phone" : "addbar";
        return `<div class="${cls}">${dateField(`id="add-date" min="${TODAY}" max="${RANGE_END}"`)}<button type="button" id="add-day">この日を足す</button></div>`;
    }

    function renderBoard() {
        if (!roster.length) return '<p class="note">名簿が空です。</p>';
        const rows = visible().map(day => {
            const count = counts(day.iso);
            const amHot = count.am >= READY;
            const pmHot = count.pm >= READY;
            const hot = amHot || pmHot;
            const game = state.games[day.iso];
            const moving = game ? (game.slot === "pm" ? "午後で進行中" : "午前で進行中") : "";
            const pill = moving || (hot ? "手配候補" : "様子見");
            const pillClass = moving ? "pill move" : (hot ? "pill yes" : "pill");
            const opened = openId === day.iso;
            const detail = opened ? `<div class="detail"><div class="groups">
                <div class="group"><h3>終日 ${people(day.iso, "all").length}</h3>${nameChips(people(day.iso, "all"))}</div>
                <div class="group"><h3>午前だけ ${people(day.iso, "am").length}</h3>${nameChips(people(day.iso, "am"))}</div>
                <div class="group"><h3>午後だけ ${people(day.iso, "pm").length}</h3>${nameChips(people(day.iso, "pm"))}</div>
                <div class="group"><h3>未定 ${people(day.iso, "pending").length}</h3>${pendingChips(day.iso, people(day.iso, "pending"))}</div>
                <div class="group"><h3>不参加 ${people(day.iso, "out").length}</h3>${nameChips(people(day.iso, "out"))}</div>
                <div class="group"><h3>未回答 ${unanswered(day.iso).length}</h3>${nameChips(unanswered(day.iso))}</div>
            </div></div>` : "";
            return `<article class="day${hot ? " hot" : ""}">
                <div class="day-row" data-open="${day.iso}">
                    <div class="when"><b>${day.md}</b><span class="dow ${day.kind}">${day.dow}</span>${day.extra ? `<div class="tag">${esc(day.extra)}</div>` : ""}</div>
                    <div>${meter(count.am, "am", amHot)}${meter(count.pm, "pm", pmHot)}${scale()}</div>
                    <div class="side">
                        <span class="${pillClass}">${pill}</span>
                        ${amHot ? goButton(day, "am") : ""}
                        ${pmHot ? goButton(day, "pm") : ""}
                        <button type="button" class="ghost remove" data-remove="${day.iso}">外す</button>
                    </div>
                </div>
                ${detail}
            </article>`;
        }).join("");
        return `<div class="toolbar">
                <div class="linkbox"><code>回答用リンク ${esc(location.pathname)}</code><button type="button" id="copy">コピー</button></div>
                ${addControls(false)}
            </div>
            ${rows || '<p class="note">候補日がありません。日を足してください。</p>'}`;
    }

    function renderAnswer() {
        if (!roster.length) return '<p class="note">名簿が空です。</p>';
        const rows = visible().map(day => {
            const current = effective(personId, day.iso);
            const buttons = choiceMeta.map(([key, label]) => `<button type="button" class="${current.status === key ? "on " + key : ""}" data-set="${day.iso}" data-status="${key}">${label}</button>`).join("");
            const by = current.status === "pending" ? `<div class="by">いつまでに答えるか ${dateField(`data-by="${day.iso}" value="${esc(current.by)}" class="has-value"`)}</div>` : "";
            return `<div class="ans"><div class="top"><b>${day.md}</b><span class="dow ${day.kind}">${day.dow}</span>${day.extra ? `<span class="tag">${esc(day.extra)}</span>` : ""}<button type="button" class="text-remove" data-remove="${day.iso}">外す</button></div><div class="choices">${buttons}</div>${by}</div>`;
        }).join("");
        const options = roster.map(player => `<option value="${esc(player.player_id)}"${String(player.player_id) === personId ? " selected" : ""}>${esc(player.name)}</option>`).join("");
        const heading = boot.loggedIn ? "" : `<h1>${answerTitle}</h1>`;
        return `<div class="phone-wrap"><div class="phone">
            <header>${heading}<p>出られる時間を選んでください。未定のときは、いつまでに答えるかも入れてください。</p></header>
            <div class="who"><select id="person">${options}</select></div>
            ${addControls(true)}
            ${rows}
            <button type="button" class="send" id="send">回答を送る</button>
        </div></div>`;
    }

    function nameField(index, current) {
        const typed = current && !rosterNames.includes(current);
        const options = [`<option value="">選手名</option>`, `<option value="${MANUAL}"${typed ? " selected" : ""}>手入力</option>`]
            .concat(roster.map(player => `<option value="${esc(player.name)}"${!typed && player.name === current ? " selected" : ""}>${esc(player.name)}</option>`));
        return `<select class="pp-select" data-name="${index}">${options.join("")}</select><input class="pp-manual" data-manual="${index}" value="${esc(typed ? current : "")}" placeholder="選手名を入力"${typed ? "" : " hidden"}>`;
    }
    function posField(index, current, locked) {
        const options = [['', '位置']].concat(POSITIONS.map(pos => [pos, pos])).map(([value, label]) => `<option value="${value}"${value === current ? " selected" : ""}>${label}</option>`).join("");
        return `<select class="pp-select" data-pos="${index}"${locked ? " disabled" : ""}>${options}</select>`;
    }
    function faceHtml(index, name) {
        if (name) return `<img class="pp-face" data-face="${index}" src="${esc(conditionSrc(name))}" alt=""><span class="pp-face" data-face-blank="${index}" hidden></span>`;
        return `<img class="pp-face" data-face="${index}" alt="" hidden><span class="pp-face" data-face-blank="${index}"></span>`;
    }
    function supportHtml(names) {
        if (!names.length) return "";
        return `<div class="support"><p class="support-label">サポートメンバー</p><div class="support-list">${names.map(name => `<span class="support-name">${esc(name)}</span>`).join("")}</div></div>`;
    }
    function orderHtml(game) {
        const hasDh = game.lineup.slice(0, 9).some(row => row.p === "DH");
        return game.lineup.map((row, index) => {
            const locked = index === 9 && hasDh;
            const label = index === 9 ? (hasDh ? "P" : "10") : String(index + 1);
            const color = positionColors[row.p] || "#c5ced6";
            return `<div class="pp-row"><span class="pp-num" data-num="${index}">${label}</span><span class="pp-name" data-name-pill="${index}" style="background:${color}">${nameField(index, row.n)}</span>${faceHtml(index, row.n.trim())}<span class="pp-pos" data-pos-pill="${index}" style="background:${color}">${posField(index, row.p, locked)}</span></div>`;
        }).join("");
    }
    function renderGame() {
        const iso = currentGameId();
        if (!iso) return '<p class="note">進める日を選ぶと、ここに試合カードが出ます。</p>';
        const day = visible().find(item => item.iso === iso);
        if (!day) return '<p class="note">進める日を選ぶと、ここに試合カードが出ます。</p>';
        const game = draftFor(iso);
        enforceDh(game);
        const choices = [["公式戦", "公式戦"], ["練習試合", "練習試合"]];
        const uniforms = ["黒", "青"];
        const bats = ["ウレタン可", "金属・木製のみ", "使用可能バット情報なし"];
        const picked = gameDays();
        const picker = picked.length > 1 ? `<select class="game-pick" id="game-pick">${picked.map(item => `<option value="${item.iso}"${item.iso === iso ? " selected" : ""}>${item.md}（${item.dow}）${state.games[item.iso].slot === "pm" ? "午後" : "午前"}</option>`).join("")}</select>` : "";
        const stadiumOptions = Object.keys(STADIUMS).map(name => `<option value="${esc(name)}">`).join("");
        return `<article class="game">
            <div class="game-head">
                <span class="date-pill">${day.md}<span class="dow ${day.kind}">${day.dow}</span><span class="when-slot">${game.slot === "pm" ? "午後" : "午前"}</span></span>
                <span class="pill move" id="ground-pill">${esc(game.stadium.trim() ? game.stadium.trim() : "グラウンド手配中")}</span>
            </div>
            ${picker ? `<div class="game-head">${picker}</div>` : ""}
            <div class="game-body">
                <div>
                    <div class="slot-label">${game.slot === "pm" ? "午後" : "午前"}の試合</div>
                    <div class="grid">
                        <div class="field"><label>対戦相手</label><input id="f-opponent" value="${esc(game.opponent)}" placeholder="決まり次第"></div>
                        <div class="field"><label>試合の種類</label><select id="f-event">${choices.map(([value, label]) => `<option value="${value}"${game.eventName === value ? " selected" : ""}>${label}</option>`).join("")}</select></div>
                        <div class="field"><label>グラウンド</label><input id="f-stadium" list="stadium-list" value="${esc(game.stadium)}" placeholder="手配中"><datalist id="stadium-list">${stadiumOptions}</datalist></div>
                        <div class="field"><label>住所</label><input id="f-address" value="${esc(game.address)}"></div>
                        <div class="field"><label>ユニフォーム</label><select id="f-uniform">${uniforms.map(value => `<option${game.uniform === value ? " selected" : ""}>${value}</option>`).join("")}</select></div>
                        <div class="field"><label>バット条件</label><select id="f-bat">${bats.map(value => `<option${game.bat === value ? " selected" : ""}>${value}</option>`).join("")}</select></div>
                        <div class="field"><label>集合時間</label><input id="f-gather" type="time" step="300" value="${esc(game.timeGather)}"></div>
                        <div class="field"><label>試合開始</label><input id="f-start" type="time" step="300" value="${esc(game.timePB)}"></div>
                        <div class="field wide"><label>備考</label><textarea id="f-bench" rows="2">${esc(game.bench)}</textarea></div>
                    </div>
                </div>
                <div>
                    <p class="order-label">STARTING ORDER</p>
                    <div class="pp-order">${orderHtml(game)}<div id="support-box">${supportHtml(supportNames(iso, game))}</div></div>
                </div>
            </div>
            <button type="button" class="save" id="save-game">保存する</button>
        </article>`;
    }

    function removeAlert() {
        if (!pendingRemove) return "";
        const day = visible().find(item => item.iso === pendingRemove);
        if (!day) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="alert-text"><p id="alert-text">${esc(day.md)}（${esc(day.dow)}）を外しますか？</p><div class="alert-actions"><button type="button" id="alert-ok">外す</button><button type="button" id="alert-cancel">キャンセル</button></div></div></div>`;
    }

    function paintFace(index, name) {
        const img = document.querySelector(`[data-face="${index}"]`);
        const blank = document.querySelector(`[data-face-blank="${index}"]`);
        if (!img || !blank) return;
        if (name) {
            img.hidden = false;
            img.src = conditionSrc(name);
            blank.hidden = true;
        } else {
            img.hidden = true;
            img.removeAttribute("src");
            blank.hidden = false;
        }
    }
    function paintOrder(game) {
        enforceDh(game);
        const hasDh = game.lineup.slice(0, 9).some(row => row.p === "DH");
        game.lineup.forEach((row, index) => {
            const color = positionColors[row.p] || "#c5ced6";
            const namePill = document.querySelector(`[data-name-pill="${index}"]`);
            const posPill = document.querySelector(`[data-pos-pill="${index}"]`);
            if (namePill) namePill.style.background = color;
            if (posPill) posPill.style.background = color;
            if (index === 9) {
                const num = document.querySelector('[data-num="9"]');
                const pos = document.querySelector('[data-pos="9"]');
                if (num) num.textContent = hasDh ? "P" : "10";
                if (pos) {
                    pos.disabled = hasDh;
                    pos.value = row.p;
                }
            }
            paintFace(index, row.n.trim());
        });
    }
    function updateSupport(iso, game) {
        const box = document.getElementById("support-box");
        if (box) box.innerHTML = supportHtml(supportNames(iso, game));
    }
    function snapTime(value) {
        if (!value || !value.includes(":")) return value || "";
        const [hour, minute] = value.split(":");
        const snapped = Math.floor(parseInt(minute, 10) / 5) * 5;
        if (Number.isNaN(snapped)) return value;
        return `${hour}:${String(snapped).padStart(2, "0")}`;
    }
    function bindGame(iso) {
        const game = drafts[iso];
        if (!game) return;
        const fields = {
            "f-opponent": "opponent",
            "f-event": "eventName",
            "f-stadium": "stadium",
            "f-address": "address",
            "f-uniform": "uniform",
            "f-bat": "bat",
            "f-gather": "timeGather",
            "f-start": "timePB",
            "f-bench": "bench"
        };
        Object.entries(fields).forEach(([id, key]) => {
            const el = document.getElementById(id);
            if (!el) return;
            const write = () => {
                game[key] = el.value;
                if (id === "f-stadium") {
                    if (STADIUMS[el.value]) {
                        game.address = STADIUMS[el.value];
                        const address = document.getElementById("f-address");
                        if (address) address.value = game.address;
                    }
                    const pill = document.getElementById("ground-pill");
                    if (pill) pill.textContent = el.value.trim() ? el.value.trim() : "グラウンド手配中";
                }
            };
            el.addEventListener("input", write);
            el.addEventListener("change", () => {
                if (id === "f-gather" || id === "f-start") {
                    el.value = snapTime(el.value);
                    game[key] = el.value;
                } else {
                    write();
                }
            });
        });
        game.lineup.forEach((_, index) => {
            const name = document.querySelector(`[data-name="${index}"]`);
            const manual = document.querySelector(`[data-manual="${index}"]`);
            const pos = document.querySelector(`[data-pos="${index}"]`);
            if (name) name.addEventListener("change", () => {
                if (name.value === MANUAL) {
                    manual.hidden = false;
                    if (rosterNames.includes(game.lineup[index].n)) game.lineup[index].n = "";
                    manual.value = game.lineup[index].n;
                    manual.focus();
                } else {
                    manual.hidden = true;
                    manual.value = "";
                    game.lineup[index].n = name.value;
                }
                paintFace(index, game.lineup[index].n.trim());
                updateSupport(iso, game);
            });
            if (manual) manual.addEventListener("input", () => {
                game.lineup[index].n = manual.value;
                paintFace(index, manual.value.trim());
                updateSupport(iso, game);
            });
            if (pos) pos.addEventListener("change", () => {
                game.lineup[index].p = pos.value;
                paintOrder(game);
                updateSupport(iso, game);
            });
        });
        const pick = document.getElementById("game-pick");
        if (pick) pick.addEventListener("change", () => {
            activeGame = pick.value;
            render();
        });
        const save = document.getElementById("save-game");
        if (save) save.addEventListener("click", () => run(async () => {
            enforceDh(game);
            await postPoll({ action: "game", iso, game });
            drafts[iso] = cloneGame(state.games[iso]);
            setToast("保存しました。");
        }));
    }

    function render() {
        const scroll = window.scrollY;
        let body = "";
        if (!boot.loggedIn || view === "answer") body = renderAnswer();
        else if (view === "game") body = renderGame();
        else body = renderBoard();
        app.innerHTML = (boot.loggedIn ? memberHead() : "") + toastHtml() + body + removeAlert();
        bind();
        window.scrollTo(0, scroll);
        if (scrollTo) {
            const row = document.querySelector(`[data-open="${scrollTo}"]`);
            if (row) row.scrollIntoView({ block: "nearest" });
            scrollTo = "";
        }
    }
    function bind() {
        app.querySelectorAll(".date-field input").forEach(input => {
            const sync = () => input.classList.toggle("has-value", Boolean(input.value));
            sync();
            input.addEventListener("input", sync);
            input.addEventListener("change", sync);
        });
        app.querySelectorAll("[data-view]").forEach(button => {
            button.addEventListener("click", () => {
                if (busy) return;
                view = button.dataset.view;
                setToast("");
                render();
            });
        });
        const copy = document.getElementById("copy");
        if (copy) copy.addEventListener("click", async () => {
            const url = location.origin + location.pathname;
            try {
                await navigator.clipboard.writeText(url);
                setToast("回答用リンクをコピーしました。");
            } catch (error) {
                setToast("コピーできませんでした。", true);
            }
            render();
        });
        const add = document.getElementById("add-day");
        const addDate = document.getElementById("add-date");
        if (add && addDate) {
            addDate.addEventListener("keydown", event => {
                if (event.key === "Enter") add.click();
            });
            add.addEventListener("click", () => run(async () => {
                const value = addDate.value;
                if (!value) {
                    setToast("足す日を選んでください。", true);
                    return;
                }
                if (value < TODAY || value > RANGE_END) {
                    setToast("足せるのは今日から来月末までです。", true);
                    return;
                }
                if (visible().some(day => day.iso === value)) {
                    openId = value;
                    setToast("その日はもう並んでいます。", true);
                    return;
                }
                await postPoll({ action: "add", iso: value, routine: isRoutine(value) });
                openId = value;
                scrollTo = value;
                const date = parseDate(value);
                setToast(`${date.getMonth() + 1}/${date.getDate()}を足しました。`);
            }));
        }
        app.querySelectorAll("[data-open]").forEach(row => {
            row.addEventListener("click", event => {
                if (event.target.closest("[data-go], [data-remove]")) return;
                openId = openId === row.dataset.open ? "" : row.dataset.open;
                render();
            });
        });
        app.querySelectorAll("[data-go]").forEach(button => {
            button.addEventListener("click", event => {
                event.stopPropagation();
                const iso = button.dataset.go;
                const slot = button.dataset.slot;
                const day = visible().find(item => item.iso === iso);
                run(async () => {
                    const game = cloneGame(drafts[iso] || state.games[iso] || blankGame(slot));
                    game.slot = slot;
                    enforceDh(game);
                    await postPoll({ action: "game", iso, game });
                    drafts[iso] = cloneGame(state.games[iso]);
                    activeGame = iso;
                    view = "game";
                    setToast(day ? `${day.md}（${day.dow}）の${slot === "pm" ? "午後" : "午前"}で進めました。` : "進めました。");
                });
            });
        });
        app.querySelectorAll("[data-remove]").forEach(button => {
            button.addEventListener("click", event => {
                event.stopPropagation();
                if (busy) return;
                pendingRemove = button.dataset.remove;
                render();
            });
        });
        const alertOk = document.getElementById("alert-ok");
        const alertCancel = document.getElementById("alert-cancel");
        if (alertCancel) {
            alertCancel.focus();
            alertCancel.addEventListener("click", () => {
                pendingRemove = null;
                render();
            });
        }
        const alertBack = document.querySelector(".alert-back");
        if (alertBack) alertBack.addEventListener("click", event => {
            if (event.target !== alertBack) return;
            pendingRemove = null;
            render();
        });
        if (alertOk) alertOk.addEventListener("click", () => {
            const iso = pendingRemove;
            const day = visible().find(item => item.iso === iso);
            run(async () => {
                await postPoll({ action: "remove", iso });
                if (activeGame === iso) activeGame = "";
                delete drafts[iso];
                Object.keys(answerDraft).forEach(player => {
                    if (answerDraft[player]) delete answerDraft[player][iso];
                });
                if (openId === iso) openId = "";
                pendingRemove = null;
                setToast(day ? `${day.md}を外しました。` : "外しました。");
            });
        });
        const person = document.getElementById("person");
        if (person) person.addEventListener("change", () => {
            personId = person.value;
            rememberPerson(personId);
            render();
        });
        app.querySelectorAll("[data-set]").forEach(button => {
            button.addEventListener("click", () => {
                const iso = button.dataset.set;
                const status = button.dataset.status;
                const item = ensureDraft(personId, iso);
                item.status = item.status === status ? "" : status;
                if (item.status === "pending" && !item.by) item.by = shiftDays(TODAY, 14);
                render();
            });
        });
        app.querySelectorAll("[data-by]").forEach(input => {
            input.addEventListener("change", () => {
                const item = ensureDraft(personId, input.dataset.by);
                item.status = "pending";
                if (input.value) item.by = input.value;
                render();
            });
        });
        const send = document.getElementById("send");
        if (send) send.addEventListener("click", () => run(async () => {
            const answers = {};
            visible().forEach(day => {
                const current = effective(personId, day.iso);
                if (current.status === "pending" && !current.by) throw new Error("未定のときは、いつまでに答えるかを入れてください。");
                answers[day.iso] = current.status === "pending" ? { status: "pending", by: current.by } : { status: current.status };
            });
            await postPoll({ action: "answer", player_id: Number(personId), answers });
            delete answerDraft[personId];
            if (boot.loggedIn) view = "board";
            const player = roster.find(item => String(item.player_id) === personId);
            setToast(boot.loggedIn ? "回答を反映しました。" : `${player ? player.name : ""}の回答を送りました。`);
        }));
        if (view === "game" && boot.loggedIn) bindGame(currentGameId());
    }

    app.textContent = "読み込んでいます。";
    fetch(boot.readApi, { cache: "no-store" })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error((data && data.error) || "読み込めませんでした。");
            applyPoll(data);
            render();
        })
        .catch(error => {
            app.textContent = error.message || "読み込めませんでした。";
        });
})();
