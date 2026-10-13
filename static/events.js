(() => {
    const boot = window.EVENTS_BOOT || {};
    const app = document.getElementById("app");
    const roster = boot.roster || [];
    const DOW = ["日", "月", "火", "水", "木", "金", "土"];
    const MANUAL = "__manual__";
    const choices = [["in", "参加"], ["pending", "未定"], ["out", "不参加"]];
    const todayDate = new Date();
    todayDate.setHours(0, 0, 0, 0);
    const rangeEnd = new Date(todayDate.getFullYear(), todayDate.getMonth() + 7, 0);

    const state = { events: {}, peopleCustom: false };
    const answerDraft = {};
    let showAdd = false;
    let showPeople = false;
    let pendingPerson = "";
    let openKey = "";
    let editKey = "";
    let pendingDelete = "";
    let toast = "";
    let toastBad = false;
    let busy = false;
    let manualMode = false;
    let manualName = "";
    let personId = storedPerson();
    if (personId.startsWith("manual:")) {
        manualMode = true;
        manualName = personId.slice("manual:".length);
        personId = "";
    } else if (!roster.some(player => String(player.player_id) === personId)) {
        personId = "";
    }

    function isoDate(date) {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    }
    const TODAY = isoDate(todayDate);
    const RANGE_END = isoDate(rangeEnd);
    function parseDate(iso) {
        const [year, month, day] = String(iso || "").split("-").map(Number);
        return new Date(year, month - 1, day);
    }
    function shiftDays(iso, days) {
        const date = parseDate(iso);
        date.setDate(date.getDate() + days);
        return isoDate(date);
    }
    function dayLabel(iso) {
        const date = parseDate(iso);
        return `${date.getMonth() + 1}/${date.getDate()}（${DOW[date.getDay()]}）`;
    }
    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }
    function plainName(value) {
        return String(value || "").replace(/[\s\u3000]/g, "");
    }
    function storedPerson() {
        try { return sessionStorage.getItem("schedule-person") || ""; }
        catch (error) { return ""; }
    }
    function rememberPerson(id) {
        try { sessionStorage.setItem("schedule-person", id); }
        catch (error) { /* 保存できなくても回答は送れる */ }
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
    function guests() {
        const found = new Map();
        Object.values(state.events).forEach(event => {
            Object.values(event.answers || {}).forEach(bucket => {
                Object.entries(bucket || {}).forEach(([key, record]) => {
                    if (key.startsWith("n:") && record && record.name) found.set(key, record.name);
                });
            });
        });
        return Array.from(found, ([player_id, name]) => ({ player_id, name }));
    }
    function answerers() {
        return roster.concat(guests());
    }
    function answerOf(event, iso, key) {
        return ((event.answers || {})[iso] || {})[key] || null;
    }
    function effective(eventId, iso) {
        const draft = answerDraft[eventId] && answerDraft[eventId][iso];
        if (draft) return draft;
        const event = state.events[eventId];
        const saved = event ? answerOf(event, iso, personKey()) : null;
        if (saved) return { status: saved.status, by: saved.by || shiftDays(TODAY, 14) };
        return { status: "", by: shiftDays(TODAY, 14) };
    }
    function ensureDraft(eventId, iso) {
        answerDraft[eventId] = answerDraft[eventId] || {};
        if (!answerDraft[eventId][iso]) answerDraft[eventId][iso] = effective(eventId, iso);
        return answerDraft[eventId][iso];
    }
    function peopleFor(event, iso, status) {
        return answerers().filter(player => (answerOf(event, iso, String(player.player_id)) || {}).status === status);
    }
    function unansweredPeople(event, iso) {
        return roster.filter(player => !(answerOf(event, iso, String(player.player_id)) || {}).status);
    }
    function nameChips(players) {
        if (!players.length) return '<span class="empty">なし</span>';
        return players.map(player => `<span class="chip">${esc(player.name)}</span>`).join("");
    }
    function pendingChips(event, iso, players) {
        if (!players.length) return '<span class="empty">なし</span>';
        return players.map(player => {
            const answer = answerOf(event, iso, String(player.player_id)) || {};
            const late = answer.by && answer.by < TODAY;
            const when = String(answer.by || "").slice(5).replace("-", "/");
            return `<span class="chip${late ? " late" : ""}">${esc(player.name)}（${esc(when)}${late ? "・期限超過" : ""}）</span>`;
        }).join("");
    }
    function sortedEvents() {
        return Object.entries(state.events).map(([id, event]) => ({ id, ...event })).sort((a, b) => {
            const left = a.dates[0] || "";
            const right = b.dates[0] || "";
            if (left !== right) return left < right ? -1 : 1;
            return a.name < b.name ? -1 : 1;
        });
    }
    function setToast(message, bad) {
        toast = message || "";
        toastBad = Boolean(bad);
    }
    async function postEvent(body) {
        const response = await fetch(boot.pollApi, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || "保存に失敗しました。");
        state.events = data.events || {};
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
    function snapTime(value) {
        if (!value || !value.includes(":")) return value || "";
        const [hour, minute] = value.split(":");
        const snapped = Math.floor(parseInt(minute, 10) / 5) * 5;
        if (Number.isNaN(snapped)) return value;
        return `${hour}:${String(snapped).padStart(2, "0")}`;
    }

    function namePicker() {
        const who = personKey();
        const named = Boolean(who);
        const options = [`<option value="">名前を選んでください</option>`]
            .concat(roster.map(player => `<option value="${esc(player.player_id)}"${!manualMode && String(player.player_id) === personId ? " selected" : ""}>${esc(player.name)}</option>`))
            .concat([`<option value="${MANUAL}"${manualMode ? " selected" : ""}>手入力</option>`]);
        const whoLabel = named ? "この名前で回答します" : (manualMode ? "名前を入力してください" : "先に自分の名前を選んでください");
        return `<div class="who${named ? " picked" : " need"}"><p class="who-label">${whoLabel}</p><select id="person" aria-label="あなたの名前"${manualMode ? " hidden" : ""}>${options.join("")}</select><input id="person-manual" class="who-manual" value="${esc(manualName)}" placeholder="名前を入力" aria-label="名前を入力"${manualMode ? "" : " hidden"}></div>`;
    }
    function attendCount(event, iso) {
        return peopleFor(event, iso, "in").length;
    }
    function meter(count) {
        const peopleCount = Math.max(roster.length, 1);
        const width = Math.min(100, count / peopleCount * 100);
        return `<div class="slot"><span class="k">参加可能</span><span class="n">${count}</span><span class="meter"><i style="width:${width}%"></i></span></div>`;
    }
    function scale() {
        if (!roster.length) return "";
        const ticks = Array.from({ length: roster.length }, () => "<span></span>").join("");
        const ten = roster.length >= 10 ? `<b class="ten">10</b>` : "";
        return `<div class="tick-row"><span></span><span></span><div class="ticks" style="--people:${roster.length}">${ticks}${ten}</div></div>`;
    }
    function choiceButtons(event, iso) {
        const current = effective(event.id, iso);
        const named = Boolean(personKey());
        const buttons = choices.map(([key, label]) => `<button type="button" class="${current.status === key ? "on " + key : ""}" data-event="${event.id}" data-date="${iso}" data-status="${key}"${named ? "" : " disabled"}>${label}</button>`).join("");
        const by = current.status === "pending" ? `<div class="by">回答期日 <input type="date" data-by="${event.id}" data-date="${iso}" value="${esc(current.by)}"></div>` : "";
        return `<div class="choices row-choices">${buttons}</div>${by}`;
    }
    function answerGroups(event, iso) {
        const joined = peopleFor(event, iso, "in");
        const absent = peopleFor(event, iso, "out");
        const pending = peopleFor(event, iso, "pending");
        const missing = unansweredPeople(event, iso);
        const block = (label, count, chips) => `<div class="group"><h3>${label} ${count}</h3>${chips}</div>`;
        return `<div class="groups">${block("参加", joined.length, nameChips(joined))}${block("不参加", absent.length, nameChips(absent))}${block("未定", pending.length, pendingChips(event, iso, pending))}${block("未回答", missing.length, nameChips(missing))}</div>`;
    }
    function eventRows(events) {
        return events.flatMap(event => event.dates.map(iso => ({ event, iso }))).sort((a, b) => a.iso < b.iso ? -1 : a.iso > b.iso ? 1 : 0);
    }
    function eventRow(event, iso) {
        const date = parseDate(iso);
        const kind = date.getDay() === 0 ? "sun" : date.getDay() === 6 ? "sat" : "plain";
        const count = attendCount(event, iso);
        const confirmed = Boolean(event.confirmed);
        const pill = confirmed ? "確定" : "様子見";
        const pillClass = confirmed ? "pill move" : "pill";
        const key = `${event.id}:${iso}`;
        const editing = editKey === key;
        const confirm = confirmed ? "" : `<button type="button" class="go" data-confirm="${event.id}" data-date="${iso}">確定</button>`;
        const opened = editing || openKey === key;
        const actions = boot.loggedIn && opened && !editing ? `<div class="row-actions">${confirm}<button type="button" class="go" data-edit="${event.id}" data-date="${iso}">編集</button><button type="button" class="go danger" data-delete="${event.id}" data-date="${iso}">削除</button></div>` : "";
        const answers = opened && !editing ? choiceButtons(event, iso) : "";
        const people = opened && !editing ? answerGroups(event, iso) : "";
        return `<article class="day"><div class="day-row${opened ? " open" : ""}" data-open="${event.id}" data-date="${iso}"><div class="when"><span class="fold" aria-hidden="true"></span><div><b>${date.getMonth() + 1}/${date.getDate()}</b><span class="dow ${kind}">${DOW[date.getDay()]}</span><div class="tag">${esc(event.name)}</div></div></div><div>${meter(count)}${scale()}${answers}${people}</div><div class="side"><span class="${pillClass}">${pill}</span>${actions}</div></div>${editing ? editPanel(event, iso) : ""}</article>`;
    }
    function editPanel(event, iso) {
        const min = iso < TODAY ? iso : TODAY;
        const max = iso > RANGE_END ? iso : RANGE_END;
        return `<div class="detail"><div class="addbar"><input type="date" id="edit-date" value="${esc(iso)}" min="${min}" max="${max}"><input id="edit-name" value="${esc(event.name)}" aria-label="内容" placeholder="予定を入力"><button type="button" id="edit-save">反映する</button><button type="button" class="cancel" id="edit-cancel">キャンセル</button></div></div>`;
    }
    function deleteAlert() {
        if (!pendingDelete || !state.events[pendingDelete]) return "";
        const event = state.events[pendingDelete];
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="event-delete-text"><p id="event-delete-text">${esc(event.name)}を削除しますか？</p><div class="alert-actions"><button type="button" id="event-delete-ok">削除</button><button type="button" id="event-delete-cancel">キャンセル</button></div></div></div>`;
    }
    function manageBar() {
        if (!boot.loggedIn) return "";
        const add = showAdd ? `<div class="addbar"><input type="date" id="add-date" min="${TODAY}" max="${RANGE_END}"><input id="add-name" placeholder="予定を入力" aria-label="内容"><button type="button" id="add-day">この日を追加</button></div>` : "";
        return `<div class="toolbar"><div class="manage"><button type="button" id="toggle-add" class="${showAdd ? "on" : ""}">予定追加</button><button type="button" id="toggle-people" class="${showPeople ? "on" : ""}">回答対象者</button></div>${add}${peoplePanel()}</div>`;
    }
    function peoplePanel() {
        if (!showPeople) return "";
        const chips = roster.map(person => `<button type="button" data-person-remove="${esc(person.player_id)}">${esc(person.name)} ×</button>`).join("");
        const note = state.peopleCustom ? "この一覧がイベントの回答対象です。" : "いまは選手名簿を使っています。追加または外すと、イベント専用の一覧として保存されます。";
        return `<div class="people-box"><p class="people-note">${note}</p><div class="people-list">${chips || '<span class="empty">まだいません</span>'}</div><div class="addbar"><input id="person-add" placeholder="マネージャーなど" aria-label="回答対象者を追加"><button type="button" id="person-add-btn">追加</button></div></div>`;
    }
    function personAlert() {
        if (!pendingPerson) return "";
        const person = roster.find(item => String(item.player_id) === pendingPerson);
        if (!person) return "";
        return `<div class="alert-back"><div class="alert-panel" role="alertdialog" aria-labelledby="person-remove-text"><p id="person-remove-text">${esc(person.name)}を回答対象から外しますか？</p><div class="alert-actions"><button type="button" id="person-remove-ok">外す</button><button type="button" id="person-remove-cancel">キャンセル</button></div></div></div>`;
    }
    function render() {
        const scroll = window.scrollY;
        const rows = eventRows(sortedEvents());
        const upcoming = rows.filter(row => row.iso >= TODAY);
        const past = rows.filter(row => row.iso < TODAY);
        const empty = boot.loggedIn ? "日程はまだありません。予定追加から日付と内容を入れてください。" : "日程はまだありません。";
        const cards = upcoming.map(row => eventRow(row.event, row.iso)).join("") || `<p class="note">${empty}</p>`;
        const pastCards = past.length ? `<h2 class="note">終わった予定</h2>${past.map(row => eventRow(row.event, row.iso)).join("")}` : "";
        const schedule = boot.scheduleUrl || "schedule";
        const tabs = [
            ["board", "調整ボード", "調整"],
            ["answer", "回答シート", "回答"],
            ["game", "試合カード", "試合"]
        ].map(([id, label]) => `<a href="${esc(schedule)}?view=${id}">${label}</a>`).join("");
        const head = `<header class="site"><h1>イベント</h1><div class="view-switch">${tabs}<a class="on" aria-current="page" href="${esc(location.pathname)}">イベント</a></div></header><p class="lead">日付をクリックすると、参加可否と回答した人が開きます。もう一度クリックすると日付と人数だけに戻ります。</p>`;
        app.innerHTML = `${head}${toast ? `<div class="toast${toastBad ? " bad" : ""}">${esc(toast)}</div>` : ""}${namePicker()}${manageBar()}${cards}${pastCards}${deleteAlert()}${personAlert()}`;
        bind();
        window.scrollTo(0, scroll);
    }
    function bind() {
        const person = document.getElementById("person");
        const manual = document.getElementById("person-manual");
        if (person) person.addEventListener("change", () => {
            if (person.value === MANUAL) {
                manualMode = true;
                manual.hidden = false;
                person.hidden = true;
                manual.focus();
            } else {
                manualMode = false;
                personId = person.value;
                rememberPerson(personId);
            }
            render();
        });
        if (manual) {
            manual.addEventListener("input", () => { manualName = manual.value; });
            manual.addEventListener("change", () => {
                manualName = manual.value;
                if (!manualName.trim()) {
                    manualMode = false;
                    render();
                    return;
                }
                rememberAnswering();
                render();
            });
        }
        const toggleAdd = document.getElementById("toggle-add");
        if (toggleAdd) toggleAdd.addEventListener("click", () => {
            showAdd = !showAdd;
            if (showAdd) showPeople = false;
            render();
        });
        const togglePeople = document.getElementById("toggle-people");
        if (togglePeople) togglePeople.addEventListener("click", () => {
            showPeople = !showPeople;
            if (showPeople) showAdd = false;
            render();
        });
        const personAdd = document.getElementById("person-add-btn");
        const personName = document.getElementById("person-add");
        if (personAdd && personName) personAdd.addEventListener("click", () => run(async () => {
            const name = personName.value.trim();
            if (!name) throw new Error("名前を入力してください。");
            if (roster.some(person => plainName(person.name) === plainName(name))) throw new Error("その名前はもう入っています。");
            await postEvent({ action: "people", people: peoplePayload().concat([{ name }]) });
            setToast("回答対象者を追加しました。");
        }));
        app.querySelectorAll("[data-person-remove]").forEach(button => {
            button.addEventListener("click", () => {
                pendingPerson = button.dataset.personRemove;
                render();
            });
        });
        const personRemoveCancel = document.getElementById("person-remove-cancel");
        const personRemoveOk = document.getElementById("person-remove-ok");
        if (personRemoveCancel) personRemoveCancel.addEventListener("click", () => {
            pendingPerson = "";
            render();
        });
        if (personRemoveOk) personRemoveOk.addEventListener("click", () => run(async () => {
            const id = pendingPerson;
            await postEvent({ action: "people", people: peoplePayload().filter(person => person.id !== id) });
            pendingPerson = "";
            setToast("回答対象者から外しました。");
        }));
        const addDay = document.getElementById("add-day");
        const addDate = document.getElementById("add-date");
        const addName = document.getElementById("add-name");
        if (addDay && addDate && addName) addDay.addEventListener("click", () => run(async () => {
            const iso = addDate.value;
            const name = addName.value.trim();
            if (!iso) throw new Error("足す日を選んでください。");
            if (!name) throw new Error("内容を入力してください。");
            await postEvent({ action: "create", event: { name, dates: [iso], place: "", address: "", timeStart: "", note: "" } });
            showAdd = false;
            setToast("日程を足しました。");
        }));
        app.querySelectorAll("[data-open]").forEach(row => {
            row.addEventListener("click", event => {
                if (event.target.closest("[data-confirm], [data-edit], [data-delete], [data-status], [data-by], button, input, select, textarea")) return;
                const key = `${row.dataset.open}:${row.dataset.date}`;
                if (editKey === key) return;
                openKey = openKey === key ? "" : key;
                render();
            });
        });
        app.querySelectorAll("[data-confirm]").forEach(button => {
            button.addEventListener("click", () => run(async () => {
                const event = state.events[button.dataset.confirm];
                if (event && event.confirmed) return;
                await postEvent({ action: "confirm", id: button.dataset.confirm });
                setToast("予定を確定しました。");
            }));
        });
        app.querySelectorAll("[data-edit]").forEach(button => {
            button.addEventListener("click", () => {
                const key = `${button.dataset.edit}:${button.dataset.date}`;
                editKey = editKey === key ? "" : key;
                render();
            });
        });
        const editSave = document.getElementById("edit-save");
        const editCancel = document.getElementById("edit-cancel");
        const editDate = document.getElementById("edit-date");
        const editName = document.getElementById("edit-name");
        if (editCancel) editCancel.addEventListener("click", () => {
            editKey = "";
            render();
        });
        if (editSave && editDate && editName && editKey) editSave.addEventListener("click", () => run(async () => {
            const [eventId, iso] = editKey.split(":");
            const event = state.events[eventId];
            const nextIso = editDate.value;
            const name = editName.value.trim();
            if (!event) throw new Error("イベントが見つかりません。");
            if (!nextIso) throw new Error("日付を選んでください。");
            if (!name) throw new Error("内容を入力してください。");
            if (nextIso !== iso && (nextIso < TODAY || nextIso > RANGE_END)) throw new Error("足せるのは今日から6か月先の月末までです。");
            const dates = event.dates.map(day => day === iso ? nextIso : day);
            await postEvent({
                action: "update",
                id: eventId,
                event: {
                    name,
                    dates,
                    place: event.place || "",
                    address: event.address || "",
                    timeStart: event.timeStart || "",
                    note: event.note || ""
                }
            });
            editKey = "";
            setToast("予定を反映しました。");
        }));
        app.querySelectorAll("[data-delete]").forEach(button => {
            button.addEventListener("click", event => {
                event.stopPropagation();
                pendingDelete = button.dataset.delete;
                render();
            });
        });
        async function sendAnswer(eventId, iso, status, by) {
            const key = personKey();
            if (!key) throw new Error(manualMode ? "名前を入力してください。" : "名前を選んでください。");
            const answers = {};
            answers[iso] = status === "pending" ? { status, by: by || shiftDays(TODAY, 14) } : { status };
            const body = { action: "answer", id: eventId, answers };
            if (key.startsWith("n:")) body.name = manualName.trim().slice(0, 40);
            else body.person_id = key;
            rememberAnswering();
            await postEvent(body);
            delete answerDraft[eventId];
            setToast("回答を送りました。");
        }
        app.querySelectorAll("[data-status]").forEach(button => {
            button.addEventListener("click", () => run(async () => {
                const eventId = button.dataset.event;
                const iso = button.dataset.date;
                const current = effective(eventId, iso);
                const next = current.status === button.dataset.status ? "" : button.dataset.status;
                await sendAnswer(eventId, iso, next, current.by);
            }));
        });
        app.querySelectorAll("[data-by]").forEach(input => {
            input.addEventListener("change", () => run(async () => {
                if (!input.value) throw new Error("未定の場合は、回答期日を設定してください。");
                await sendAnswer(input.dataset.by, input.dataset.date, "pending", input.value);
            }));
        });
        const deleteOk = document.getElementById("event-delete-ok");
        const deleteCancel = document.getElementById("event-delete-cancel");
        if (deleteCancel) deleteCancel.addEventListener("click", () => {
            pendingDelete = "";
            render();
        });
        if (deleteOk) deleteOk.addEventListener("click", () => run(async () => {
            const id = pendingDelete;
            await postEvent({ action: "delete", id });
            pendingDelete = "";
            setToast("予定を削除しました。");
        }));
    }

    app.textContent = "読み込んでいます。";
    fetch(boot.readApi, { cache: "no-store" })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error((data && data.error) || "読み込めませんでした。");
            state.events = data.events || {};
            setPeople(data.people, data.peopleCustom);
            render();
        })
        .catch(error => {
            app.textContent = error.message || "読み込めませんでした。";
        });
})();
