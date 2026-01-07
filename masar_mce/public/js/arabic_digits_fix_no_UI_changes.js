(function () {
  if (window.__arabic_digits_fix_loaded) return;
  window.__arabic_digits_fix_loaded = true;

  const map = {
    "٠":"0","١":"1","٢":"2","٣":"3","٤":"4","٥":"5","٦":"6","٧":"7","٨":"8","٩":"9",
    "۰":"0","۱":"1","۲":"2","۳":"3","۴":"4","۵":"5","۶":"6","۷":"7","۸":"8","۹":"9",
    "٫":".", "٬":",", "،":","
  };

  function normalize(v) {
    if (v === null || v === undefined) return v;
    if (typeof v === "number") return v;

    let s;
    try { s = String(v); } catch (e) { return v; }

    // only touch when we detect Arabic digits/separators
    if (!/[٠-٩۰-۹٫٬،]/.test(s)) return v;

    s = s.replace(/[٠-٩۰-۹٫٬،]/g, ch => map[ch] ?? ch);
    s = s.replace(/,/g, ""); // remove thousand separators
    return s;
  }

  function patchOnce(obj, key, wrap) {
    if (!obj) return;
    const orig = obj[key];
    if (typeof orig !== "function") return;
    if (orig.__arabic_patched__) return;

    const wrapped = wrap(orig);
    wrapped.__arabic_patched__ = true;
    obj[key] = wrapped;
  }

  function patchControls() {
    if (!window.frappe || !frappe.ui || !frappe.ui.form) return;

    const names = ["ControlFloat", "ControlInt", "ControlCurrency", "ControlPercent"];
    names.forEach((n) => {
      const proto = frappe.ui.form[n] && frappe.ui.form[n].prototype;
      if (!proto || proto.__arabic_digits_parse_patched__) return;

      const origParse = proto.parse;
      if (typeof origParse !== "function") return;

      proto.parse = function (v) {
        return origParse.call(this, normalize(v));
      };

      proto.__arabic_digits_parse_patched__ = true;
    });
  }

  function patchParsersFallback() {
    // fallback: patch flt/cint in case some code uses them directly
    patchOnce(window, "flt", (orig) => (v, d) => orig(normalize(v), d));
    patchOnce(window, "cint", (orig) => (v, def) => orig(normalize(v), def));

    if (window.frappe && frappe.utils) {
      patchOnce(frappe.utils, "flt", (orig) => (v, d) => orig(normalize(v), d));
      patchOnce(frappe.utils, "cint", (orig) => (v, def) => orig(normalize(v), def));
    }
  }

  function applyAll() {
    try { patchControls(); } catch (e) {}
    try { patchParsersFallback(); } catch (e) {}
  }

  applyAll();

  if (window.frappe && typeof frappe.ready === "function") {
    frappe.ready(() => applyAll());
  }
})();
