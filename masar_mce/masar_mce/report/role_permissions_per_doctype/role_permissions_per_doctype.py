# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_data(filters):
    conditions = " 1=1 "
    if filters.get("doctype"):
        conditions += f" AND dt.name = '{filters.get('doctype')}'"
    if filters.get("role"):
        conditions += f" AND r.name = '{filters.get('role')}'"

    sql = frappe.db.sql(f"""
        SELECT
			r.name AS Role,
			dt.name AS DocType,
			COALESCE(dp.permlevel,0) AS Level,
			COALESCE(dp.if_owner,0) AS IfOwner,
			COALESCE(dp.`select`,0) AS SelectPerm,
			COALESCE(dp.read,0) AS ReadPerm,
			COALESCE(dp.`write`,0) AS WritePerm,
			COALESCE(dp.create,0) AS CreatePerm,
			COALESCE(dp.`delete`,0) AS DeletePerm,
			COALESCE(dp.submit,0) AS SubmitPerm,
			COALESCE(dp.cancel,0) AS CancelPerm,
			COALESCE(dp.amend,0) AS AmendPerm,
			COALESCE(dp.report,0) AS ReportPerm,
			COALESCE(dp.`import`,0) AS ImportPerm,
			COALESCE(dp.`export`,0) AS ExportPerm,
			COALESCE(dp.`print`,0) AS PrintPerm,
			COALESCE(dp.email,0) AS EmailPerm,
			COALESCE(dp.share,0) AS SharePerm
		FROM
			`tabRole` r
		CROSS JOIN
			`tabDocType` dt
		LEFT JOIN
			`tabCustom DocPerm` dp
			ON dp.role = r.name AND dp.parent = dt.name 
		WHERE 
			{conditions}
			AND r.disabled = 0
			AND (
				COALESCE(dp.if_owner,0) = 1 OR
				COALESCE(dp.`select`,0) = 1 OR
				COALESCE(dp.read,0) = 1 OR
				COALESCE(dp.`write`,0) = 1 OR
				COALESCE(dp.create,0) = 1 OR
				COALESCE(dp.`delete`,0) = 1 OR
				COALESCE(dp.submit,0) = 1 OR
				COALESCE(dp.cancel,0) = 1 OR
				COALESCE(dp.amend,0) = 1 OR
				COALESCE(dp.report,0) = 1 OR
				COALESCE(dp.`import`,0) = 1 OR
				COALESCE(dp.`export`,0) = 1 OR
				COALESCE(dp.`print`,0) = 1 OR
				COALESCE(dp.email,0) = 1 OR
				COALESCE(dp.share,0) = 1
			)
		ORDER BY r.name, dt.name;
	""")
    
    return sql

def get_columns():
    return [
        "Role:Link/Role:175",
		"DocType:Link/DocType:200",
		"Level:Data:125",
		"IfOwner:Data:125",
		"SelectPerm:Data:125",
		"ReadPerm:Data:125",
		"WritePerm:Data:125",
		"CreatePerm:Data:125",
		"DeletePerm:Data:125",
		"SubmitPerm:Data:125",
		"CancelPerm:Data:125",
		"AmendPerm:Data:125",
		"ReportPerm:Data:125",
		"ImportPerm:Data:125",
		"ExportPerm:Data:125",
		"PrintPerm:Data:125",
		"EmailPerm:Data:125",
		"SharePerm:Data:125"
	]
