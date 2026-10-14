import { fetchJson, formApi, teamLocation } from "./api.js";

let renderer;
let payload;
let saving = false;

function message(text, fatal = false) {
    let box = document.getElementById("client-message");
    if (!box) {
        box = document.createElement("div");
        box.id = "client-message";
        box.setAttribute("role", "alert");
        box.style.cssText = "margin:1rem;padding:1rem;border:1px solid #b71c1c;background:#fff4f4;color:#b71c1c;font-family:sans-serif;";
        document.body.prepend(box);
    }
    box.textContent = text;
    if (fatal) {
        const retry = document.createElement("button");
        retry.type = "button";
        retry.textContent = "再読み込み";
        retry.addEventListener("click", () => window.location.reload());
        box.append(document.createTextNode(" "), retry);
    }
}

async function runScript(source) {
    const script = document.createElement("script");
    for (const attribute of source.attributes) script.setAttribute(attribute.name, attribute.value);
    script.dataset.clientView = "";
    if (source.src) {
        script.async = false;
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = () => reject(new Error("画面のスクリプトを読み込めませんでした。"));
            document.body.append(script);
        });
    } else {
        script.textContent = source.textContent;
        document.body.append(script);
    }
}

async function display(nextPayload) {
    const html = renderer.render(nextPayload);
    const parsed = new DOMParser().parseFromString(html, "text/html");
    const scripts = [...parsed.querySelectorAll("script")];
    for (const script of scripts) script.remove();
    for (const element of document.head.querySelectorAll("[data-client-view]")) element.remove();
    document.title = parsed.title || "BaseMob";
    for (const element of parsed.head.querySelectorAll("style, link")) {
        element.dataset.clientView = "";
        document.head.append(element);
    }
    document.body.className = parsed.body.className;
    document.body.replaceChildren(...parsed.body.childNodes);
    payload = nextPayload;
    for (const script of scripts) await runScript(script);
    // API 読込後に初期化される既存チャート・テーブルへ準備完了を通知する。
    document.dispatchEvent(new Event("DOMContentLoaded"));
    document.body.dataset.clientReady = "true";
}

document.addEventListener("submit", async event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") return;
    event.preventDefault();
    if (saving) return;
    const buttons = [...form.querySelectorAll('button[type="submit"], input[type="submit"]')];
    const previous = buttons.map(button => button.disabled);
    try {
        const url = new URL(form.getAttribute("action") || window.location.href, window.location.href);
        if (url.origin !== window.location.origin) throw new Error("保存先を確認してください。");
        const api = formApi(url, payload.meta);
        const body = new FormData(form);
        if (event.submitter?.name) body.append(event.submitter.name, event.submitter.value);
        saving = true;
        buttons.forEach(button => { button.disabled = true; });
        const result = await fetchJson(api, { method: "POST", body });
        if (result.redirect) {
            const target = new URL(result.redirect, window.location.href);
            if (target.origin !== window.location.origin) throw new Error("移動先を確認してください。");
            window.location.assign(target.href);
        } else if (result.view) {
            await display(result);
        } else {
            message("保存しました。");
        }
    } catch (error) {
        message(error.message || "保存に失敗しました。");
    } finally {
        saving = false;
        buttons.forEach((button, index) => { button.disabled = previous[index]; });
    }
});

async function start() {
    const { prefix, path } = teamLocation();
    const [sources, data] = await Promise.all([
        fetchJson("/static/app/views.json", { cache: "default" }),
        fetchJson(prefix + "/api/screens" + path + window.location.search),
    ]);
    renderer = window.BaseMobViews.createRenderer(sources);
    if (data.redirect) window.location.assign(data.redirect);
    else await display(data);
}

start().catch(error => message(error.message || "画面を読み込めませんでした。", true));
