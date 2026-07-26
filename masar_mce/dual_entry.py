import frappe
from frappe import _
from frappe.utils import flt, cstr

# Doctypes that implement dual data-entry verification for pricing fields.
# child_table_field: fieldname of the Table field holding the priced rows.
# pricing_fields: fieldnames (on the child row) that must be entered twice.
# trigger_state: workflow_state that, once entered, backs up and resets the
#                pricing_fields so a second user can re-enter them from scratch.
DUAL_ENTRY_CONFIG = {
	"Blanket Order": {
		"child_table_field": "items",
		"pricing_fields": [
			"rate",
			"custom_markup_percentage",
			"custom_selling_price",
			"custom_suggest_accounting_price",
		],
		"trigger_state": "Pending Manager Review",
	},
	"Pricing Sheet": {
		"child_table_field": "items",
		"pricing_fields": [
			"new_purchase_price",
			"local_mp",
			"local_sp",
			"free_mp",
			"free_sp",
		],
		"trigger_state": "Pending Manager Review",
	},
}

DIFFERENCE_TOLERANCE = 1e-3

# Marks a child row as having already been sent to the manager once. Set once
# and never cleared, so a later Feedback -> Draft -> Send to Manager cycle
# does not wipe the manager's input fields to 0 again (only the Original
# Entry backup is refreshed on every cycle, not the zero-reset).
CAPTURED_FIELD = "dual_entry_captured"


def get_config(doctype):
	config = DUAL_ENTRY_CONFIG.get(doctype)
	if not config:
		frappe.throw(_("Dual entry pricing verification is not configured for {0}").format(doctype))
	return config


def original_fieldname(fieldname):
	return f"original_{fieldname}"


def difference_fieldname(fieldname):
	return f"difference_{fieldname}"


def is_entering_state(doc, state):
	"""True only on the save that just transitioned doc.workflow_state into `state`."""
	if cstr(doc.get("workflow_state")) != state:
		return False
	before_save = doc.get_doc_before_save()
	if not before_save:
		return False
	return cstr(before_save.get("workflow_state")) != state


def send_pricing_to_manager(doc, config=None):
	"""Every time the entry user sends the row to the manager, whatever they
	currently have entered is captured as the Original Entry - so a value the
	entry user corrects after a Feedback loop is compared against the
	corrected number, not a stale one from an earlier cycle.

	The manager's input fields are only reset to 0 the FIRST time a row is
	sent, giving the manager a blank field for a truly independent first
	entry. On later cycles the fields are left as they are so the manager
	isn't forced to blindly retype on every review round."""
	config = config or get_config(doc.doctype)
	for row in doc.get(config["child_table_field"]):
		first_time = not row.get(CAPTURED_FIELD)
		for fieldname in config["pricing_fields"]:
			row.set(original_fieldname(fieldname), flt(row.get(fieldname)))
			if first_time:
				row.set(fieldname, 0)
				row.set(difference_fieldname(fieldname), 0)
		if first_time:
			row.set(CAPTURED_FIELD, 1)
		else:
			_refresh_row_differences(row, config)


def _refresh_row_differences(row, config):
	for fieldname in config["pricing_fields"]:
		original_value = flt(row.get(original_fieldname(fieldname)))
		current_value = flt(row.get(fieldname))
		row.set(difference_fieldname(fieldname), abs(current_value - original_value))


def update_pricing_differences(doc, config=None):
	"""Recompute Difference = abs(manager value - original value) for every pricing field."""
	config = config or get_config(doc.doctype)
	for row in doc.get(config["child_table_field"]):
		_refresh_row_differences(row, config)


def apply_dual_entry_workflow(doc, config=None):
	"""Call from validate(): on the 'Send to Manager' transition, back up and reset.
	On every other save, just keep the Difference fields in sync."""
	config = config or get_config(doc.doctype)
	if is_entering_state(doc, config["trigger_state"]):
		send_pricing_to_manager(doc, config)
	else:
		update_pricing_differences(doc, config)


def validate_pricing_matches(doc, config=None):
	"""Call from before_submit(): block submission unless every pricing field the
	manager entered matches the first user's Original Entry exactly."""
	config = config or get_config(doc.doctype)
	child_meta = frappe.get_meta(doc.meta.get_field(config["child_table_field"]).options)
	mismatches = []

	for row in doc.get(config["child_table_field"]):
		for fieldname in config["pricing_fields"]:
			original_value = flt(row.get(original_fieldname(fieldname)))
			manager_value = flt(row.get(fieldname))
			if abs(manager_value - original_value) > DIFFERENCE_TOLERANCE:
				label = child_meta.get_label(fieldname)
				mismatches.append(
					_("Row #{0}: {1} (Original Entry: {2}, Manager Entry: {3})").format(
						row.idx, label, original_value, manager_value
					)
				)

	if mismatches:
		frappe.throw(
			_(
				"Pricing values entered by the Manager do not match the Original Entry "
				"for the following fields. Please correct and re-enter matching values "
				"before submitting:<br>{0}"
			).format("<br>".join(mismatches)),
			title=_("Pricing Verification Failed"),
		)
