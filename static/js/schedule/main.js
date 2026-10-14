// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
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
