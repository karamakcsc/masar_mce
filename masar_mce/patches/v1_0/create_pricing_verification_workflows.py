import frappe

# One "Send to Manager" verification workflow per dual-entry doctype.
# Both doctypes share the same state/action names, defined here once.
WORKFLOWS = [
	{
		"workflow_name": "Supplier Agreement Pricing Verification",
		"document_type": "Blanket Order",
		"first_entry_role": "Purchase User",
		"manager_role": "Purchase Manager",
	},
	{
		"workflow_name": "Pricing Sheet Pricing Verification",
		"document_type": "Pricing Sheet",
		"first_entry_role": "Purchase User",
		"manager_role": "Purchase Manager",
	},
]


def execute():
	ensure_workflow_state("Draft")
	ensure_workflow_state("Pending Manager Review")
	ensure_workflow_state("Verified")
	ensure_workflow_action("Send to Manager")
	ensure_workflow_action("Submit")
	ensure_workflow_action("Feedback")

	for config in WORKFLOWS:
		create_or_update_workflow(config)


def ensure_workflow_state(state):
	if not frappe.db.exists("Workflow State", state):
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(
			ignore_permissions=True
		)


def ensure_workflow_action(action):
	if not frappe.db.exists("Workflow Action Master", action):
		frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
			ignore_permissions=True
		)


def get_states(first_entry_role, manager_role):
	return [
		{"state": "Draft", "doc_status": "0", "allow_edit": first_entry_role},
		{"state": "Pending Manager Review", "doc_status": "0", "allow_edit": manager_role},
		{"state": "Verified", "doc_status": "1", "allow_edit": manager_role},
	]


def get_transitions(first_entry_role, manager_role):
	return [
		{
			"state": "Draft",
			"action": "Send to Manager",
			"next_state": "Pending Manager Review",
			"allowed": first_entry_role,
			"allow_self_approval": 1,
		},
		{
			"state": "Pending Manager Review",
			"action": "Feedback",
			"next_state": "Draft",
			"allowed": manager_role,
			"allow_self_approval": 1,
		},
		{
			"state": "Pending Manager Review",
			"action": "Submit",
			"next_state": "Verified",
			"allowed": manager_role,
			"allow_self_approval": 1,
		},
	]


def create_or_update_workflow(config):
	first_entry_role = config["first_entry_role"]
	manager_role = config["manager_role"]

	if not frappe.db.exists("Workflow", config["workflow_name"]):
		workflow = frappe.get_doc(
			{
				"doctype": "Workflow",
				"workflow_name": config["workflow_name"],
				"document_type": config["document_type"],
				"workflow_state_field": "workflow_state",
				"is_active": 1,
				"send_email_alert": 0,
				"states": get_states(first_entry_role, manager_role),
				"transitions": get_transitions(first_entry_role, manager_role),
			}
		)
		workflow.insert(ignore_permissions=True)
		return

	# Workflow already exists (e.g. created before the "Feedback" transition was
	# added here) - add any transitions/states it is still missing.
	workflow = frappe.get_doc("Workflow", config["workflow_name"])
	existing_states = {s.state for s in workflow.states}
	for state in get_states(first_entry_role, manager_role):
		if state["state"] not in existing_states:
			workflow.append("states", state)

	existing_transitions = {(t.state, t.action) for t in workflow.transitions}
	for transition in get_transitions(first_entry_role, manager_role):
		key = (transition["state"], transition["action"])
		if key not in existing_transitions:
			workflow.append("transitions", transition)

	workflow.save(ignore_permissions=True)
