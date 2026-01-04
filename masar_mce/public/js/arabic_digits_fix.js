(function () {
  window.__arabic_digits_fix_loaded = true;

  const ar = "٠١٢٣٤٥٦٧٨٩";   // Arabic-Indic
  const fa = "۰۱۲۳۴۵۶۷۸۹";   // Extended Arabic-Indic
  const en = "0123456789";

  // Return a STRING if input is not null/undefined, otherwise return as-is
  function normalizeDigits(v) {
    if (v === null || v === undefined) return v;
    let s = String(v);

    s = s.replace(/[٠-٩]/g, d => en[ar.indexOf(d)]);
    s = s.replace(/[۰-۹]/g, d => en[fa.indexOf(d)]);

    // separators
    s = s.replace(/٫/g, "."); // Arabic decimal
    s = s.replace(/٬/g, ","); // Arabic thousands
    s = s.replace(/،/g, ","); // Arabic comma variant

    return s;
  }

  function normalizeForParse(v) {
    // IMPORTANT: keep undefined/null as-is (ERPNext calls cint(undefined) often)
    if (v === null || v === undefined) return v;

    // If already a number, don’t touch it
    if (typeof v === "number") return v;

    const s = normalizeDigits(v);
    if (s === null || s === undefined) return s;

    // If no Arabic digits/separators exist, skip (avoid side effects)
    if (!/[٠-٩۰-۹٫٬،]/.test(s)) return s;

    // remove thousand separators
    return s.replace(/,/g, "");
  }

  // Normalize actual input value early (capture phase) so blur validation sees ASCII digits
  let _guard = false;

  function isNumericishField(input) {
    if (!input) return false;
    if (input.tagName === "INPUT" && input.type === "number") return true;

    const ftEl = input.closest("[data-fieldtype]");
    const ft = ftEl?.getAttribute("data-fieldtype");
    return ["Int", "Float", "Currency", "Percent"].includes(ft || "");
  }

  function normalizeInput(target) {
    if (_guard) return;

    const input = target?.closest?.("input, textarea");
    if (!input) return;

    // only touch numeric-like fields
    if (!isNumericishField(input)) return;

    const before = input.value;
    const after = normalizeForParse(before);

    // after could be undefined/null (shouldn't happen for input.value), guard anyway
    if (after === null || after === undefined) return;

    if (before !== after) {
      _guard = true;
      input.value = after;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      _guard = false;
    }
  }

  document.addEventListener("beforeinput", e => normalizeInput(e.target), true);
  document.addEventListener("input", e => normalizeInput(e.target), true);
  document.addEventListener("blur", e => normalizeInput(e.target), true);
  document.addEventListener("change", e => normalizeInput(e.target), true);

  // Patch parsers safely (never crash on undefined)
  function patchParsers() {
    // globals
    if (typeof window.flt === "function") {
      const oflt = window.flt;
      window.flt = (v, d) => oflt(normalizeForParse(v), d);
    }
    if (typeof window.cint === "function") {
      const ocint = window.cint;
      window.cint = (v, def) => ocint(normalizeForParse(v), def);
    }

    // frappe.utils.parse_number (commonly used on blur/validation)
    if (window.frappe && frappe.utils && typeof frappe.utils.parse_number === "function") {
      const oparse = frappe.utils.parse_number;
      frappe.utils.parse_number = (v) => oparse(normalizeForParse(v));
    }

    // Some builds also expose frappe.utils.flt/cint
    if (window.frappe && frappe.utils && typeof frappe.utils.flt === "function") {
      const oflt2 = frappe.utils.flt;
      frappe.utils.flt = (v, d) => oflt2(normalizeForParse(v), d);
    }
    if (window.frappe && frappe.utils && typeof frappe.utils.cint === "function") {
      const ocint2 = frappe.utils.cint;
      frappe.utils.cint = (v, def) => ocint2(normalizeForParse(v), def);
    }
  }

  try { patchParsers(); } catch (e) { /* never break desk */ }

  if (window.frappe && typeof frappe.ready === "function") {
    frappe.ready(() => {
      try { patchParsers(); } catch (e) {}
    });
  }
})();
