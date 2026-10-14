export function teamLocation(url = new URL(window.location.href)) {
    const match = url.pathname.match(/^\/t\/([^/]+)(\/.*)?$/);
    return { prefix: match ? "/t/" + match[1] : "", path: match ? match[2] || "/" : url.pathname };
}

export async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin", cache: "no-store", ...options,
        headers: { Accept: "application/json", ...options.headers },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(data?.error || (response.status === 401 ? "ログインが必要です。画面を再読み込みしてください。" : "読み込み・保存に失敗しました。"));
    }
    if (!data) throw new Error("API の応答を読み取れませんでした。");
    return data;
}

function matches(rule, path) {
    const pattern = rule.split(/(<[^>]+>)/).map(part => {
        if (/^<int:/.test(part)) return "[0-9]+";
        if (/^</.test(part)) return "[^/]+";
        return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }).join("");
    return new RegExp("^" + pattern + "$").test(path);
}

export function formApi(url, meta) {
    const { path } = teamLocation(url);
    const prefix = meta.team_slug ? "/t/" + meta.team_slug : "";
    for (const [rule, methods] of Object.entries(meta.screen_routes)) {
        if (methods.includes("POST") && matches(rule, path)) return prefix + "/api/screens" + path + url.search;
    }
    for (const [rule, methods] of Object.entries(meta.action_routes)) {
        if (methods.includes("POST") && matches(rule, path)) return prefix + "/api/actions" + path + url.search;
    }
    throw new Error("この操作の保存 API は実装されていません。");
}
