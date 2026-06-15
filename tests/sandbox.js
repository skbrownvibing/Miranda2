/**
 * Test helper – runs app.js inside a Node.js vm sandbox, stripping the init()
 * call so no side-effects fire.  Function-declared identifiers land on the
 * returned context object and are callable from tests.
 */
import { readFileSync } from "fs";
import { createContext, Script } from "vm";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function makeDomStub() {
  const elStub = () => ({
    value: "", checked: false,
    classList: { toggle() {}, add() {}, remove() {} },
    addEventListener() {},
    textContent: "", disabled: false, innerHTML: "",
    style: { display: "" }, select() {}, title: "",
    appendChild() {}, type: "", className: "",
    querySelectorAll: () => [], querySelector: () => null,
    dataset: {},
  });
  return {
    getElementById: elStub,
    addEventListener() {},
    createElement: elStub,
    execCommand() {},
    querySelectorAll: () => [],
    querySelector: () => null,
  };
}

export function createSandbox() {
  const code = readFileSync(resolve(__dirname, "..", "app.js"), "utf8")
    .replace(/\binit\(\);\s*$/, "");

  const sandbox = createContext({
    console, Date, Math, Number, String, Array, Object, Set, Map, RegExp,
    JSON, Error, parseInt, parseFloat, isNaN, isFinite, Intl, Promise,
    URL, encodeURIComponent, decodeURIComponent,
    structuredClone: typeof structuredClone === "function"
      ? structuredClone
      : (o) => JSON.parse(JSON.stringify(o)),
    setTimeout: () => 0, clearTimeout() {},
    setInterval: () => 0, clearInterval() {},
    fetch: async () => ({ ok: false, text: async () => "", json: async () => ({}) }),
    document: makeDomStub(),
    window: {},
    localStorage: { getItem: () => null, setItem() {} },
    location: { origin: "http://localhost" },
    navigator: { clipboard: { writeText: async () => {} } },
    indexedDB: {
      open() {
        return { onupgradeneeded: null, onsuccess: null, onerror: null,
          result: { objectStoreNames: { contains: () => false },
            createObjectStore() {},
            transaction() { return { objectStore() { return { get() { return { onsuccess: null, onerror: null, result: undefined }; } }; } }; }
          }
        };
      },
    },
  });

  new Script(code, { filename: "app.js" }).runInContext(sandbox);
  return sandbox;
}
