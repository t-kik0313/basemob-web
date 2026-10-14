// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
async function submitAnswers() {
        const key = personKey();
        if (!key) throw new Error(manualMode ? "名前を入力してください。" : "名前を選んでください。");
        const answers = {};
        visible().forEach(day => {
            const current = effective(key, day.iso);
            if (current.status === "pending" && !current.by) throw new Error("未定の場合は、回答期日を設定してください。");
            answers[day.iso] = current.status === "pending" ? { status: "pending", by: current.by } : { status: current.status };
        });
        const body = { action: "answer", answers };
        if (key.startsWith("n:")) body.name = manualName.trim().slice(0, 40);
        else body.person_id = key;
        await postPoll(body);
        delete answerDraft[key];
    }

function syncLineupFromForm(iso, game) {
        const card = gameCard(iso);
        if (!card) return;
        game.lineup.forEach((row, index) => {
            const pos = card.querySelector(`[data-pos="${index}"]`);
            if (pos) row.p = pos.value;
            const manual = card.querySelector(`[data-manual="${index}"]`);
            const name = card.querySelector(`[data-name="${index}"]`);
            if (manual && !manual.hidden) row.n = manual.value;
            else if (name && name.value !== MANUAL) row.n = name.value;
        });
    }

function refreshAddressList(iso, query) {
        if (!document.getElementById(`address-list-${iso}`)) return;
        paintAddressList(iso, query, "");
        const needle = String(query || "").trim();
        addressToken += 1;
        const token = addressToken;
        clearTimeout(addressTimer);
        if (needle.length < 2 || stadiumHits(query).length) return;
        addressTimer = setTimeout(async () => {
            try {
                const res = await fetch("https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + encodeURIComponent(needle));
                if (!res.ok || token !== addressToken) return;
                const data = await res.json();
                if (token !== addressToken || !Array.isArray(data)) return;
                const titles = [];
                data.forEach(item => {
                    const title = item && item.properties && item.properties.title;
                    if (title && !titles.includes(title)) titles.push(title);
                });
                const extra = titles.map(title => `<option value="${esc(title)}" label="${esc(needle)}"></option>`).join("");
                if (token === addressToken) paintAddressList(iso, query, extra);
            } catch (err) {
                /* 地図の候補が取れないときは登録済みの会場だけ出す */
            }
        }, 400);
    }

function paintFace(card, index, name) {
        const img = card.querySelector(`[data-face="${index}"]`);
        const blank = card.querySelector(`[data-face-blank="${index}"]`);
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

function paintOrder(card, game) {
        game.lineup.forEach((row, index) => {
            const color = positionColors[row.p] || "#c5ced6";
            const namePill = card.querySelector(`[data-name-pill="${index}"]`);
            const posPill = card.querySelector(`[data-pos-pill="${index}"]`);
            if (namePill) namePill.style.background = color;
            if (posPill) posPill.style.background = color;
            if (index === 9) {
                const num = card.querySelector('[data-num="9"]');
                if (num) num.textContent = tenthLabel(game);
            }
            paintFace(card, index, row.n.trim());
        });
    }

function updateSupport(card, iso, game) {
        const box = card.querySelector(".support-box");
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
        const card = gameCard(iso);
        const game = drafts[iso];
        if (!card || !game) return;
        refreshAddressList(iso, game.stadium);
        ["opponent", "eventName", "stadium", "address", "uniform", "bat", "timeGather", "timePB", "bench"].forEach(key => {
            const el = card.querySelector(`[data-field="${key}"]`);
            if (!el) return;
            if (el.tagName === "SELECT") {
                const wanted = game[key] === "使用可能バット情報なし" ? "情報なし" : game[key];
                const index = [...el.options].findIndex(option => option.value === wanted);
                if (index >= 0) el.selectedIndex = index;
            }
            const write = () => {
                game[key] = el.value;
                if (key === "stadium") {
                    refreshAddressList(iso, el.value);
                    if (STADIUMS[el.value]) {
                        game.address = STADIUMS[el.value];
                        const address = card.querySelector('[data-field="address"]');
                        if (address) address.value = game.address;
                    }
                    const pill = card.querySelector(".pill.move");
                    if (pill) pill.textContent = el.value.trim() ? el.value.trim() : "試合会場未定";
                }
                if (key === "timePB") paintWhen(iso, game);
            };
            el.addEventListener("input", write);
            el.addEventListener("change", () => {
                if (key === "timeGather" || key === "timePB") {
                    el.value = snapTime(el.value);
                    game[key] = el.value;
                    if (key === "timePB") paintWhen(iso, game);
                } else {
                    write();
                }
            });
        });
        game.lineup.forEach((_, index) => {
            const name = card.querySelector(`[data-name="${index}"]`);
            const manual = card.querySelector(`[data-manual="${index}"]`);
            const pos = card.querySelector(`[data-pos="${index}"]`);
            if (name) name.addEventListener("change", () => {
                if (name.value === MANUAL) {
                    name.hidden = true;
                    manual.hidden = false;
                    if (rosterNames.includes(game.lineup[index].n)) game.lineup[index].n = "";
                    manual.value = game.lineup[index].n;
                    manual.focus();
                } else {
                    manual.hidden = true;
                    name.hidden = false;
                    manual.value = "";
                    game.lineup[index].n = name.value;
                }
                paintFace(card, index, game.lineup[index].n.trim());
                updateSupport(card, iso, game);
            });
            if (manual) {
                manual.addEventListener("input", () => {
                    game.lineup[index].n = manual.value;
                    paintFace(card, index, manual.value.trim());
                    updateSupport(card, iso, game);
                });
                manual.addEventListener("blur", () => {
                    if (manual.value.trim()) return;
                    manual.hidden = true;
                    name.hidden = false;
                    name.value = "";
                    game.lineup[index].n = "";
                    paintFace(card, index, "");
                    updateSupport(card, iso, game);
                });
            }
            if (pos) pos.addEventListener("change", () => {
                game.lineup[index].p = pos.value;
                paintOrder(card, game);
                updateSupport(card, iso, game);
            });
        });
        const edit = card.querySelector("[data-edit-game]");
        if (edit) edit.addEventListener("click", () => {
            if (iso < TODAY && !openPast[iso]) openPast[iso] = true;
            if (editingGame !== iso) {
                editingGame = iso;
                render();
                return;
            }
            run(async () => {
                syncLineupFromForm(iso, game);
                await postPoll({ action: "game", iso, game });
                drafts[iso] = cloneGame(state.games[iso]);
                editingGame = "";
                setToast("反映しました。");
            });
        });
        const cancel = card.querySelector("[data-cancel-game]");
        if (cancel) cancel.addEventListener("click", () => {
            if (busy) return;
            delete drafts[iso];
            editingGame = "";
            render();
        });
        const removeGame = card.querySelector("[data-delete-game]");
        if (removeGame) removeGame.addEventListener("click", () => {
            if (busy) return;
            pendingGameDelete = iso;
            render();
        });
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
                const next = button.dataset.view;
                if (view === "answer" && next !== "answer" && answerDirty(personKey())) {
                    pendingLeave = next;
                    render();
                    return;
                }
                view = next;
                pendingLeave = null;
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
        const toggleAdd = document.getElementById("toggle-add");
        if (toggleAdd) toggleAdd.addEventListener("click", () => {
            showAdd = !showAdd;
            if (showAdd) showPeople = false;
            if (!showAdd) pendingSetup = null;
            render();
        });
        const toggleDelete = document.getElementById("toggle-delete");
        if (toggleDelete) toggleDelete.addEventListener("click", () => {
            deleteMode = !deleteMode;
            if (deleteMode) showPeople = false;
            if (!deleteMode) pendingRemove = null;
            render();
        });
        const togglePeople = document.getElementById("toggle-people");
        if (togglePeople) togglePeople.addEventListener("click", () => {
            showPeople = !showPeople;
            if (showPeople) {
                showAdd = false;
                deleteMode = false;
                pendingSetup = null;
                pendingRemove = null;
            }
            render();
        });
        const personAdd = document.getElementById("person-add-btn");
        const personName = document.getElementById("person-add");
        if (personAdd && personName) personAdd.addEventListener("click", () => run(async () => {
            const name = personName.value.trim();
            if (!name) throw new Error("名前を入力してください。");
            if (roster.some(person => plainName(person.name) === plainName(name))) throw new Error("その名前はもう入っています。");
            await postPoll({ action: "people", people: peoplePayload().concat([{ name }]) });
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
            await postPoll({ action: "people", people: peoplePayload().filter(person => person.id !== id) });
            pendingPerson = "";
            setToast("回答対象者から外しました。");
        }));
        const pastToggle = document.getElementById("toggle-past");
        if (pastToggle) pastToggle.addEventListener("click", () => {
            showPast = !showPast;
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
        app.querySelectorAll("[data-past]").forEach(button => {
            button.addEventListener("click", () => {
                const iso = button.dataset.past;
                if (openPast[iso]) {
                    delete openPast[iso];
                    if (activeGame === iso) activeGame = "";
                    if (editingGame === iso) editingGame = "";
                } else {
                    Object.keys(openPast).forEach(key => { delete openPast[key]; });
                    openPast[iso] = true;
                    activeGame = iso;
                }
                render();
            });
        });
        app.querySelectorAll("[data-open]").forEach(row => {
            row.addEventListener("click", event => {
                if (event.target.closest("[data-go], [data-remove], [data-setup]")) return;
                openId = openId === row.dataset.open ? "" : row.dataset.open;
                render();
            });
        });
        function beginGame(iso, slot, verb) {
            const day = visible().find(item => item.iso === iso);
            run(async () => {
                const game = cloneGame(drafts[iso] || state.games[iso] || blankGame(slot));
                game.slot = slot;
                await postPoll({ action: "game", iso, game });
                drafts[iso] = cloneGame(state.games[iso]);
                activeGame = iso;
                scrollTo = iso;
                view = "game";
                pendingSetup = null;
                const when = slot === "pm" ? "午後" : "午前";
                setToast(day ? `${day.md}（${day.dow}）の${when}で${verb}。` : `${verb}。`);
            });
        }
        app.querySelectorAll("[data-go]").forEach(button => {
            button.addEventListener("click", event => {
                event.stopPropagation();
                beginGame(button.dataset.go, button.dataset.slot, "進めました");
            });
        });
        app.querySelectorAll("[data-setup]").forEach(button => {
            button.addEventListener("click", event => {
                event.stopPropagation();
                if (busy) return;
                pendingSetup = button.dataset.setup;
                render();
            });
        });
        app.querySelectorAll("[data-setup-slot]").forEach(button => {
            button.addEventListener("click", () => {
                const iso = pendingSetup;
                pendingSetup = null;
                beginGame(iso, button.dataset.setupSlot, "設定しました");
            });
        });
        const setupCancel = document.getElementById("setup-cancel");
        if (setupCancel) setupCancel.addEventListener("click", () => {
            pendingSetup = null;
            render();
        });
        const gameDeleteOk = document.getElementById("game-delete-ok");
        const gameDeleteCancel = document.getElementById("game-delete-cancel");
        if (gameDeleteCancel) gameDeleteCancel.addEventListener("click", () => {
            pendingGameDelete = null;
            render();
        });
        if (gameDeleteOk) gameDeleteOk.addEventListener("click", () => {
            const iso = pendingGameDelete;
            const day = findGameDay(iso);
            run(async () => {
                await postPoll({ action: "clear-game", iso });
                delete drafts[iso];
                if (activeGame === iso) activeGame = "";
                pendingGameDelete = null;
                view = gameDays().length || pastGameDays().length ? "game" : "board";
                setToast(day ? `${day.md}の試合カードを削除しました。` : "試合カードを削除しました。");
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
        app.querySelectorAll(".alert-back").forEach(alertBack => {
            alertBack.addEventListener("click", event => {
                if (event.target !== alertBack) return;
                pendingRemove = null;
                pendingSetup = null;
                pendingGameDelete = null;
                pendingLeave = null;
                render();
            });
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
                setToast(day ? `${day.md}を削除しました。` : "削除しました。");
            });
        });
        const person = document.getElementById("person");
        if (person) person.addEventListener("change", () => {
            if (person.value === MANUAL) {
                manualMode = true;
                manualName = "";
                personId = "";
                focusManual = true;
                rememberPerson("");
                render();
                return;
            }
            manualMode = false;
            manualName = "";
            personId = person.value;
            rememberAnswering();
            render();
        });
        const manual = document.getElementById("person-manual");
        if (manual) {
            const paintWho = () => {
                const named = Boolean(personKey());
                app.querySelectorAll("[data-set]").forEach(button => { button.disabled = !named; });
                const send = document.getElementById("send");
                if (send) send.disabled = !named;
                const label = app.querySelector(".who-label");
                if (label) label.textContent = named ? "この名前で回答します" : "名前を入力してください";
                const box = app.querySelector(".who");
                if (box) {
                    box.classList.toggle("picked", named);
                    box.classList.toggle("need", !named);
                }
            };
            manual.addEventListener("input", () => {
                const before = personKey();
                const caret = manual.selectionStart;
                manualName = manual.value;
                const after = personKey();
                if (before && after && before !== after && answerDraft[before]) {
                    answerDraft[after] = Object.assign({}, answerDraft[before], answerDraft[after] || {});
                    delete answerDraft[before];
                }
                rememberAnswering();
                if (before === after) {
                    paintWho();
                    return;
                }
                manualCaret = caret;
                render();
            });
            manual.addEventListener("blur", () => {
                if (manual.value.trim()) return;
                manualMode = false;
                manualName = "";
                rememberPerson("");
                render();
            });
        }
        if (focusManual || manualCaret != null) {
            focusManual = false;
            const field = document.getElementById("person-manual");
            const caret = manualCaret;
            manualCaret = null;
            if (field) {
                field.focus();
                if (caret != null) field.setSelectionRange(caret, caret);
            }
        }
        app.querySelectorAll("[data-set]").forEach(button => {
            button.addEventListener("click", () => {
                const who = personKey();
                if (!who) return;
                const iso = button.dataset.set;
                const status = button.dataset.status;
                const item = ensureDraft(who, iso);
                item.status = item.status === status ? "" : status;
                if (item.status === "pending" && !item.by) item.by = shiftDays(TODAY, 14);
                render();
            });
        });
        app.querySelectorAll("[data-by]").forEach(input => {
            input.addEventListener("change", () => {
                const who = personKey();
                if (!who) return;
                const item = ensureDraft(who, input.dataset.by);
                item.status = "pending";
                if (input.value) item.by = input.value;
                render();
            });
        });
        const leaveOk = document.getElementById("leave-ok");
        const leaveCancel = document.getElementById("leave-cancel");
        if (leaveCancel) {
            leaveCancel.focus();
            leaveCancel.addEventListener("click", () => {
                pendingLeave = null;
                render();
            });
        }
        if (leaveOk) leaveOk.addEventListener("click", () => {
            const next = pendingLeave;
            run(async () => {
                await submitAnswers();
                pendingLeave = null;
                view = next;
                setToast("回答を反映しました。");
            });
        });
        const send = document.getElementById("send");
        if (send) send.addEventListener("click", () => run(async () => {
            await submitAnswers();
            if (boot.loggedIn) view = "board";
            const key = personKey();
            const player = roster.find(item => String(item.player_id) === key);
            const sentName = player ? player.name : manualName.trim();
            setToast(boot.loggedIn ? "回答を反映しました。" : `${sentName}の回答を送りました。`);
        }));
        if (view === "game" && boot.loggedIn) app.querySelectorAll("[data-game]").forEach(card => bindGame(card.dataset.game));
    }
