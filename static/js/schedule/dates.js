// schedule_board.js の構成部品。単体では読み込まず scripts/build_schedule_js.py で結合する。
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

function dayFromIso(iso) {
        const date = parseDate(iso);
        const holidayName = holidays.get(iso) || "";
        const dow = date.getDay();
        return {
            iso,
            md: `${date.getMonth() + 1}/${date.getDate()}`,
            dow: DOW[dow],
            kind: holidayName ? "hol" : (dow === 6 ? "sat" : dow === 0 ? "sun" : "plain"),
            extra: holidayName
        };
    }

function gameDays() {
        return visible().filter(day => state.games[day.iso]);
    }

function pastGameDays() {
        return Object.keys(state.games).filter(iso => iso < TODAY && state.games[iso]).sort().map(dayFromIso);
    }

function findGameDay(iso) {
        return gameDays().find(item => item.iso === iso) || pastGameDays().find(item => item.iso === iso);
    }

function currentGameId() {
        const days = gameDays();
        if (activeGame && days.some(day => day.iso === activeGame)) return activeGame;
        const upcoming = days.find(day => day.iso >= TODAY);
        return (upcoming || days[0] || {}).iso || "";
    }
