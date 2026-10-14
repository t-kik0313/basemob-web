/* Trusted application templates are rendered locally; API values are escaped. */
(function (root, factory) {
    if (typeof module === "object" && module.exports) module.exports = factory;
    else root.BaseMobViews = factory(root.nunjucks);
})(typeof window === "undefined" ? globalThis : window, function (nunjucks) {
    "use strict";
    nunjucks.installJinjaCompat();

    function createRenderer(sources) {
        const Loader = nunjucks.Loader.extend({
            getSource(name) {
                if (!Object.prototype.hasOwnProperty.call(sources, name)) return null;
                return { src: sources[name], path: name, noCache: false };
            }
        });
        const environment = new nunjucks.Environment(new Loader(), { autoescape: true });
        environment.addGlobal("namespace", function (values) {
            return Object.assign({}, values || {});
        });
        environment.addGlobal("setAttr", (object, key, value) => {
            object[key] = value;
            return "";
        });
        environment.addGlobal("putDict", (object, key, value) => {
            object[key] = value;
            return "";
        });
        environment.addGlobal("concat", (left, right) => left.concat(right));
        environment.addGlobal("sliceText", (value, start) => String(value).slice(start));
        environment.addFilter("float", value => Number(value) || 0);
        environment.addFilter("int", value => Math.trunc(Number(value) || 0));
        environment.addFilter("string", value => value == null ? "" : String(value));
        environment.addFilter("abs", value => Math.abs(Number(value)));
        environment.addFilter("format", (pattern, ...values) => {
            let index = 0;
            return String(pattern).replace(/%([+0]?)(\d+)?(?:\.(\d+))?([dfs])/g,
                (_, flag, width, precision, kind) => {
                    const value = values[index++];
                    let formatted = kind === "f" ? Number(value).toFixed(Number(precision || 6))
                        : kind === "d" ? String(Math.trunc(Number(value))) : String(value);
                    if (flag === "+" && Number(value) >= 0) formatted = "+" + formatted;
                    return width ? formatted.padStart(Number(width), flag === "0" ? "0" : " ") : formatted;
                });
        });
        environment.addFilter("tojson", value => new nunjucks.runtime.SafeString(
            JSON.stringify(value).replace(/[<>&'\u2028\u2029]/g,
                character => "\\u" + character.charCodeAt(0).toString(16).padStart(4, "0"))
        ));

        function urlFor(meta, endpoint, values = {}) {
            const options = { ...values };
            delete options.__keywords;
            let path = meta.routes[endpoint];
            if (!path) throw new Error("Unknown endpoint: " + endpoint);
            path = path.replace(/<(?:\w+:)?(\w+)>/g, (_, name) => {
                if (!(name in options)) throw new Error("Missing URL parameter: " + name);
                const value = options[name];
                delete options[name];
                return name === "filename" ? String(value).split("/").map(encodeURIComponent).join("/")
                    : encodeURIComponent(value);
            });
            if (endpoint !== "static" && meta.team_slug) path = "/t/" + meta.team_slug + path;
            const query = new URLSearchParams();
            for (const [key, value] of Object.entries(options)) {
                if (!key.startsWith("_") && value != null) query.set(key, value);
            }
            return path + (query.size ? "?" + query.toString() : "");
        }

        return {
            compileAll() {
                for (const name of Object.keys(sources)) environment.getTemplate(name, true);
            },
            render(payload) {
                const context = {
                    ...payload.data,
                    request: payload.data.request || { args: {} },
                    url_for: (endpoint, options) => urlFor(payload.meta, endpoint, options),
                };
                return environment.render(payload.view, context);
            },
            urlFor,
        };
    }
    return { createRenderer };
});
