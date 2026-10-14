// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
const boot = window.SCHEDULE_BOOT || {};

const players = (boot.roster || []).map(player => ({ player_id: player.player_id, name: player.name }));

const roster = players.map(player => ({ player_id: player.player_id, name: player.name }));

const rosterNames = players.map(player => player.name);

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

const state = { removed: [], added: [], answers: {}, games: {}, peopleCustom: false };

const answerDraft = {};

const drafts = {};

const askedView = new URLSearchParams(location.search).get("view");

let view = askedView === "board" || askedView === "answer" || askedView === "game" ? askedView : (boot.loggedIn ? "board" : "answer");

let openId = "";

let activeGame = "";

let pendingRemove = null;

let pendingSetup = null;

let pendingGameDelete = null;

let pendingLeave = null;

const openPast = {};

let editingGame = "";

let addressTimer = 0;

let addressToken = 0;

let showAdd = false;

let showPast = false;

let deleteMode = false;

let showPeople = false;

let pendingPerson = "";

let toast = "";

let toastBad = false;

let busy = false;

let scrollTo = "";

let manualMode = false;

let manualName = "";

let focusManual = false;

let manualCaret = null;

let personId = storedPerson();

if (personId.startsWith("manual:")) {
        manualMode = true;
        manualName = personId.slice("manual:".length);
        personId = "";
    } else if (!roster.some(player => String(player.player_id) === personId)) {
        personId = "";
    }

const app = document.getElementById("app");

const holidays = new Map();

for (let year = todayDate.getFullYear(); year <= rangeEnd.getFullYear(); year++) {
        for (const [key, name] of holidayMap(year)) holidays.set(key, name);
    }
