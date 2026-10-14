// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
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
