// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
function toastHtml() {
        if (!toast) return "";
        return `<div class="toast${toastBad ? " bad" : ""}">${esc(toast)}</div>`;
    }

function memberHead() {
        const tabs = [
            ["board", "調整ボード", "調整"],
            ["answer", "回答シート", "回答"],
            ["game", "試合カード", "試合"]
        ];
        const buttons = tabs.map(([id, label]) => `<button type="button" data-view="${id}" class="${view === id ? "on" : ""}">${label}</button>`).join("");
        const eventTab = `<a href="${esc(boot.eventsUrl || "events")}">イベント</a>`;
        const title = view === "game" ? "試合カード" : (view === "answer" ? answerTitle : monthTitle);
        return `<header class="site"><h1>${title}</h1><div class="view-switch">${buttons}${eventTab}</div></header>`;
    }

function meter(count, slot, hot) {
        const peopleCount = Math.max(roster.length, 1);
        const width = Math.min(100, count / peopleCount * 100);
        const mark = Math.min(100, MARK / peopleCount * 100);
        const label = slot === "pm" ? "午後（13:00~）" : "午前（~13:00）";
        return `<div class="slot${hot ? " up" : ""}"><span class="k">${label}</span><span class="n">${count}</span><span class="meter"><i style="width:${width}%"></i><em style="left:${mark}%"></em></span></div>`;
    }

function scale() {
        if (!roster.length) return "";
        const ticks = Array.from({ length: roster.length }, () => "<span></span>").join("");
        return `<div class="tick-row"><span></span><span></span><div class="ticks" style="--people:${roster.length}">${ticks}</div></div>`;
    }

function goButton(day, slot) {
        const label = slot === "pm" ? "午後に試合を設定する" : "午前に試合を設定する";
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

function manageButtons() {
        return `<div class="manage"><button type="button" id="toggle-add" class="${showAdd ? "on" : ""}" aria-pressed="${showAdd ? "true" : "false"}">日程追加</button><button type="button" id="toggle-delete" class="${deleteMode ? "on" : ""}" aria-pressed="${deleteMode ? "true" : "false"}">予定削除</button><button type="button" id="toggle-people" class="${showPeople ? "on" : ""}" aria-pressed="${showPeople ? "true" : "false"}">回答対象者</button></div>`;
    }

function peoplePanel() {
        if (!showPeople) return "";
        const chips = roster.map(person => `<button type="button" data-person-remove="${esc(person.player_id)}">${esc(person.name)} ×</button>`).join("");
        const note = state.peopleCustom ? "この一覧が調整ボードと回答シートの回答対象です。" : "回答対象者を選択してください。";
        return `<div class="people-box"><p class="people-note">${note}</p><div class="people-list">${chips || '<span class="empty">まだいません</span>'}</div><div class="addbar"><input id="person-add" placeholder="追加メンバーを入力" aria-label="追加メンバーを入力"><button type="button" id="person-add-btn">追加</button></div></div>`;
    }

function personAlert() {
        if (!pendingPerson) return "";
        const person = roster.find(item => String(item.player_id) === pendingPerson);
        if (!person) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="person-remove-text"><p id="person-remove-text">${esc(person.name)}を回答対象から外しますか？</p><div class="alert-actions"><button type="button" id="person-remove-ok">外す</button><button type="button" id="person-remove-cancel">キャンセル</button></div></div></div>`;
    }

function trashButton(iso) {
        if (!deleteMode) return "";
        return `<button type="button" class="trash" data-remove="${iso}" aria-label="予定削除"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM8 9h2v9H8V9z"/></svg></button>`;
    }

function setupButton(iso) {
        if (!showAdd) return "";
        return `<button type="button" class="set-game" data-setup="${iso}">試合を設定</button>`;
    }

function dayCard(day) {
        const count = counts(day.iso);
        const amHot = count.am >= READY;
        const pmHot = count.pm >= READY;
        const hot = amHot || pmHot;
        const game = state.games[day.iso];
        const moving = game ? (game.slot === "pm" ? "午後で活動予定" : "午前で活動予定") : "";
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
        return `<article class="day${hot ? " hot" : ""}${deleteMode ? " deleting" : ""}${showAdd ? " adding" : ""}">
            ${setupButton(day.iso)}
            ${trashButton(day.iso)}
            <div class="day-row${opened ? " open" : ""}" data-open="${day.iso}">
                <div class="when"><span class="fold" aria-hidden="true"></span><div><b>${day.md}</b><span class="dow ${day.kind}">${day.dow}</span>${day.extra ? `<div class="tag">${esc(day.extra)}</div>` : ""}</div></div>
                <div>${meter(count.am, "am", amHot)}${meter(count.pm, "pm", pmHot)}${scale()}</div>
                <div class="side">
                    <span class="${pillClass}">${pill}</span>
                    ${game ? "" : (amHot ? goButton(day, "am") : "")}
                    ${game ? "" : (pmHot ? goButton(day, "pm") : "")}
                </div>
            </div>
            ${detail}
        </article>`;
    }

function renderBoard() {
        if (!roster.length) return '<p class="note">名簿が空です。</p>';
        const rows = visible().map(day => dayCard(day)).join("");
        return `<div class="toolbar">
                <div class="linkbox"><code>回答用リンク ${esc(location.pathname)}</code><button type="button" id="copy">コピー</button></div>
                ${manageButtons()}
                ${showAdd ? addControls(false) : ""}
                ${peoplePanel()}
            </div>
            ${rows || '<p class="note">候補日がありません。日を足してください。</p>'}`;
    }

function renderAnswer() {
        if (!roster.length) return '<p class="note">名簿が空です。</p>';
        const who = personKey();
        const named = Boolean(who);
        const rows = visible().map(day => {
            const current = effective(who, day.iso);
            const tone = current.status === "all" ? " in" : current.status === "out" ? " out" : "";
            const buttons = choiceMeta.map(([key, label]) => `<button type="button" class="${current.status === key ? "on " + key : ""}" data-set="${day.iso}" data-status="${key}"${named ? "" : " disabled"}>${label}</button>`).join("");
            const by = current.status === "pending" ? `<div class="by">回答期日 ${dateField(`data-by="${day.iso}" value="${esc(current.by)}" class="has-value"`)}</div>` : "";
            return `<div class="ans${tone}"><div class="top"><b>${day.md}</b><span class="dow ${day.kind}">${day.dow}</span>${day.extra ? `<span class="tag">${esc(day.extra)}</span>` : ""}</div><div class="choices">${buttons}</div>${by}</div>`;
        }).join("");
        const options = [`<option value="">名前を選んでください</option>`]
            .concat(roster.map(player => `<option value="${esc(player.player_id)}"${!manualMode && String(player.player_id) === personId ? " selected" : ""}>${esc(player.name)}</option>`))
            .concat([`<option value="${MANUAL}"${manualMode ? " selected" : ""}>手入力</option>`])
            .join("");
        const heading = boot.loggedIn ? "" : `<h1>${answerTitle}</h1>`;
        const whoLabel = named ? "この名前で回答します" : (manualMode ? "名前を入力してください" : "先に自分の名前を選んでください");
        return `<div class="phone-wrap"><div class="phone">
            <header>${heading}<p>予定を回答してください。未定の場合は、回答期日を設定してください。</p></header>
            <div class="who${named ? " picked" : " need"}"><p class="who-label">${whoLabel}</p><select id="person" aria-label="あなたの名前"${manualMode ? " hidden" : ""}>${options}</select><input id="person-manual" class="who-manual" value="${esc(manualName)}" placeholder="名前を入力" aria-label="名前を入力"${manualMode ? "" : " hidden"}></div>
            ${rows}
            <button type="button" class="send" id="send"${named ? "" : " disabled"}>回答を送る</button>
        </div></div>`;
    }

function nameField(index, current, frozen) {
        const typed = current && !rosterNames.includes(current);
        const off = frozen ? " disabled" : "";
        const options = [`<option value="">選手名</option>`]
            .concat(players.map(player => `<option value="${esc(player.name)}"${!typed && player.name === current ? " selected" : ""}>${esc(player.name)}</option>`))
            .concat([`<option value="${MANUAL}"${typed ? " selected" : ""}>手入力</option>`]);
        return `<select class="pp-select" data-name="${index}"${typed ? " hidden" : ""}${off}>${options.join("")}</select><input class="pp-manual" data-manual="${index}" value="${esc(typed ? current : "")}" placeholder="選手名を入力"${typed ? "" : " hidden"}${off}>`;
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

function orderHtml(game, frozen) {
        return game.lineup.map((row, index) => {
            const locked = frozen;
            const label = index === 9 ? tenthLabel(game) : String(index + 1);
            const color = positionColors[row.p] || "#c5ced6";
            return `<div class="pp-row"><span class="pp-num" data-num="${index}">${label}</span><span class="pp-name" data-name-pill="${index}" style="background:${color}">${nameField(index, row.n, frozen)}</span>${faceHtml(index, row.n.trim())}<span class="pp-pos" data-pos-pill="${index}" style="background:${color}">${posField(index, row.p, locked)}</span></div>`;
        }).join("");
    }

function viewValue(text) {
        const shown = String(text || "").trim();
        return `<p class="value${shown ? "" : " empty"}">${esc(shown || "未定")}</p>`;
    }

function timeView(text) {
        const shown = String(text || "").trim();
        if (!shown) return viewValue(text);
        return `<p class="value time">${esc(shown)}</p>`;
    }

function uniformView(value) {
        if (value !== "黒" && value !== "青") return viewValue(value);
        const tone = value === "黒" ? "black" : "blue";
        return `<p class="value"><span class="uni ${tone}">${esc(value)}</span></p>`;
    }

function stadiumHits(query) {
        const needle = String(query || "").replace(/\s+/g, "");
        const entries = Object.entries(STADIUMS);
        if (!needle) return entries;
        return entries.filter(([name]) => {
            const plain = name.replace(/\s+/g, "");
            return plain.includes(needle) || needle.includes(plain);
        });
    }

function addressOptions(query) {
        return stadiumHits(query).map(([name, address]) => `<option value="${esc(address)}" label="${esc(name)}"></option>`).join("");
    }

function paintAddressList(iso, query, extra) {
        const list = document.getElementById(`address-list-${iso}`);
        if (!list) return;
        list.innerHTML = addressOptions(query) + (extra || "");
    }

function whenText(game) {
        const time = String((game && game.timePB) || "").trim();
        const match = time.match(/^(\d{1,2}):(\d{2})/);
        if (match) return `${match[1].padStart(2, "0")}:${match[2]}`;
        return game && game.slot === "pm" ? "午後" : "午前";
    }

function paintWhen(iso, game) {
        const card = gameCard(iso);
        if (!card) return;
        const slot = card.querySelector(".when-slot");
        if (slot) slot.textContent = whenText(game);
    }

function gameSummary(day, game, past, opened) {
        const mark = past ? `<span class="fold-mark" aria-hidden="true">${opened ? "▲" : "▼"}</span>` : "";
        const stadium = game.stadium.trim() ? game.stadium.trim() : "試合会場未定";
        const cue = past ? `<span class="detail-cue">${opened ? "閉じる" : "詳細"}</span>` : "";
        return `<span class="date-pill">${mark}${day.md}<span class="dow ${day.kind}">${day.dow}</span><span class="when-slot">${esc(whenText(game))}</span></span><span class="head-side">${cue}<span class="pill move">${esc(stadium)}</span></span>`;
    }

function pastGameBlock(past) {
        const pastBody = showPast
            ? `<div class="past-list">${past.length ? past.map(day => gameCardHtml(day)).join("") : '<p class="note">過去の試合はまだありません。</p>'}</div>`
            : "";
        return `<div class="past-wrap"><button type="button" id="toggle-past" class="past-open${showPast ? " on" : ""}" aria-expanded="${showPast ? "true" : "false"}">過去日程${past.length ? `（${past.length}）` : ""}</button>${pastBody}</div>`;
    }

function renderGame() {
        const days = gameDays();
        const past = pastGameDays();
        const cards = days.map(day => gameCardHtml(day)).join("");
        const main = days.length
            ? `<div class="game-stack">${cards}</div>`
            : '<p class="note">進める日を選ぶと、ここに試合カードが出ます。</p>';
        return `${main}${pastGameBlock(past)}`;
    }

function gameCardHtml(day) {
            const past = day.iso < TODAY;
            const opened = !past || Boolean(openPast[day.iso]);
            const iso = day.iso;
            const game = draftFor(iso);
            const choices = [["練習試合", "練習試合"], ["公式戦", "公式戦"]];
            const uniforms = ["黒", "青"];
            const bats = ["情報なし", "ウレタン可", "金属・木製のみ"];
            const eventShown = game.eventName === "公式戦" ? "公式戦" : "練習試合";
            const batShown = bats.includes(game.bat) ? game.bat : "情報なし";
            const stadiumOptions = Object.keys(STADIUMS).map(name => `<option value="${esc(name)}">`).join("");
            const head = past ? "button" : "div";
            const headAttr = past ? ` type="button" data-past="${iso}" aria-expanded="${opened ? "true" : "false"}"` : "";
            const editing = editingGame === iso;
            const form = editing ? `<div class="grid">
                        <div class="field"><label>対戦相手</label><input data-field="opponent" value="${esc(game.opponent)}" placeholder="対戦相手を入力"></div>
                        <div class="field"><label>試合の種類</label><select data-field="eventName">${choices.map(([value, label]) => `<option value="${value}"${eventShown === value ? " selected" : ""}>${label}</option>`).join("")}</select></div>
                        <div class="field"><label>試合会場</label><input data-field="stadium" list="stadium-list-${iso}" value="${esc(game.stadium)}" placeholder="試合会場を入力"><datalist id="stadium-list-${iso}">${stadiumOptions}</datalist></div>
                        <div class="field"><label>住所</label><input data-field="address" list="address-list-${iso}" value="${esc(game.address)}" placeholder="会場名から候補が出ます"><datalist id="address-list-${iso}">${addressOptions(game.stadium)}</datalist></div>
                        <div class="field"><label>ユニフォーム</label><select data-field="uniform">${uniforms.map(value => `<option${game.uniform === value ? " selected" : ""}>${value}</option>`).join("")}</select></div>
                        <div class="field"><label>バット使用条件</label><select data-field="bat">${bats.map(value => `<option${batShown === value ? " selected" : ""}>${value}</option>`).join("")}</select></div>
                        <div class="field"><label>集合時間</label><input data-field="timeGather" type="time" step="300" value="${esc(game.timeGather)}"></div>
                        <div class="field"><label>試合開始</label><input data-field="timePB" type="time" step="300" value="${esc(game.timePB)}"></div>
                        <div class="field wide"><label>備考</label><textarea data-field="bench" rows="2">${esc(game.bench)}</textarea></div>
                    </div>` : `<div class="grid view">
                        <div class="field"><label>対戦相手</label>${viewValue(game.opponent)}</div>
                        <div class="field"><label>試合の種類</label>${viewValue(eventShown)}</div>
                        <div class="field"><label>試合会場</label>${viewValue(game.stadium)}</div>
                        <div class="field"><label>住所</label>${viewValue(game.address)}</div>
                        <div class="field"><label>ユニフォーム</label>${uniformView(game.uniform)}</div>
                        <div class="field"><label>バット使用条件</label>${viewValue(batShown)}</div>
                        <div class="field"><label>集合時間</label>${timeView(game.timeGather)}</div>
                        <div class="field"><label>試合開始</label>${timeView(game.timePB)}</div>
                        <div class="field wide"><label>備考</label>${viewValue(game.bench)}</div>
                    </div>`;
            const order = opened ? `<div class="order-block">
                    <p class="order-label">STARTING ORDER</p>
                    <div class="pp-order${editing ? "" : " locked"}">${orderHtml(game, !editing)}<div class="support-box">${supportHtml(supportNames(iso, game))}</div></div>
                </div>` : "";
            return `<article class="game${editing ? " editing" : ""}${past && !opened ? " detail-closed" : ""}" data-game="${iso}">
            <${head} class="game-head${past ? " past-toggle" : ""}"${headAttr}>
                ${gameSummary(day, game, past, opened)}
            </${head}>
            <div class="game-body">
                <div class="game-form">
                    ${form}
                    <div class="game-actions">
                        <button type="button" class="game-edit" data-edit-game>${editing ? "反映する" : "編集する"}</button>
                        ${editing ? `<button type="button" class="game-cancel" data-cancel-game>キャンセル</button>` : `<button type="button" class="game-delete" data-delete-game>削除する</button>`}
                    </div>
                </div>
                ${order}
            </div>
        </article>`;
    }

function gameDeleteAlert() {
        if (!pendingGameDelete) return "";
        const day = findGameDay(pendingGameDelete);
        if (!day) return "";
        const game = drafts[day.iso] || state.games[day.iso];
        const when = whenText(game);
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="game-delete-text"><p id="game-delete-text">${esc(day.md)}（${esc(day.dow)}）${when}の試合カードを削除しますか？</p><div class="alert-actions"><button type="button" id="game-delete-ok">削除</button><button type="button" id="game-delete-cancel">キャンセル</button></div></div></div>`;
    }

function setupAlert() {
        if (!pendingSetup) return "";
        const day = visible().find(item => item.iso === pendingSetup);
        if (!day) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="setup-text"><p id="setup-text">${esc(day.md)}（${esc(day.dow)}）の試合を設定します。時間を選んでください。</p><div class="alert-actions setup"><button type="button" class="setup-slot" data-setup-slot="am">午前（~13:00）</button><button type="button" class="setup-slot" data-setup-slot="pm">午後（13:00~）</button><button type="button" id="setup-cancel">キャンセル</button></div></div></div>`;
    }

function leaveAlert() {
        if (!pendingLeave) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="leave-text"><p id="leave-text">回答を送りますか？</p><div class="alert-actions"><button type="button" id="leave-ok">送る</button><button type="button" id="leave-cancel">キャンセル</button></div></div></div>`;
    }

function removeAlert() {
        if (!pendingRemove) return "";
        const day = visible().find(item => item.iso === pendingRemove);
        if (!day) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="alert-text"><p id="alert-text">${esc(day.md)}（${esc(day.dow)}）を削除しますか？</p><div class="alert-actions"><button type="button" id="alert-ok">削除</button><button type="button" id="alert-cancel">キャンセル</button></div></div></div>`;
    }

function render() {
        const scroll = window.scrollY;
        let body = "";
        if (!boot.loggedIn || view === "answer") body = renderAnswer();
        else if (view === "game") body = renderGame();
        else body = renderBoard();
        app.innerHTML = (boot.loggedIn ? memberHead() : "") + toastHtml() + body + setupAlert() + gameDeleteAlert() + removeAlert() + leaveAlert() + personAlert();
        bind();
        window.scrollTo(0, scroll);
        if (scrollTo) {
            const row = document.querySelector(`[data-open="${scrollTo}"]`) || document.querySelector(`[data-game="${scrollTo}"]`);
            if (row) row.scrollIntoView({ block: "nearest" });
            scrollTo = "";
        }
    }
