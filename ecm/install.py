import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to


def after_install():
	add_pages_to_nav()
	create_batch_source()


def after_sync():
	create_ecm_roles()
	set_default_certificate_print_format()
	add_all_roles_to("Administrator")


def add_pages_to_nav():
	pages = [
		{"label": "Explore", "idx": 1},
		{"label": "Events", "url": "/ecm/events", "parent": "Explore", "idx": 2},
		{"label": "Batches", "url": "/ecm/batches", "parent": "Explore", "idx": 3},
		{"label": "Statistics", "url": "/ecm/statistics", "parent": "Explore", "idx": 4},
		{"label": "Jobs", "url": "/ecm/job-openings", "parent": "Explore", "idx": 5},
	]

	for page in pages:
		filters = frappe._dict()
		if page.get("url"):
			filters["url"] = ["like", "%" + page.get("url") + "%"]
		else:
			filters["label"] = page.get("label")

		if not frappe.db.exists("Top Bar Item", filters):
			frappe.get_doc(
				{
					"doctype": "Top Bar Item",
					"label": page.get("label"),
					"url": page.get("url"),
					"parent_label": page.get("parent"),
					"idx": page.get("idx"),
					"parent": "Website Settings",
					"parenttype": "Website Settings",
					"parentfield": "top_bar_items",
				}
			).save()


def before_uninstall():
	delete_custom_fields()
	delete_ecm_roles()


def create_ecm_roles():
	create_event_creator_role()
	create_moderator_role()
	create_evaluator_role()
	create_ecm_host_role()


def delete_ecm_roles():
	roles = ["Event Creator", "ECM Moderator"]
	for role in roles:
		if frappe.db.exists("Role", role):
			frappe.db.delete("Role", role)


def create_event_creator_role():
	if not frappe.db.exists("Role", "Event Creator"):
		role = frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": "Event Creator",
				"home_page": "",
				"desk_access": 0,
			}
		)
		role.save()


def create_moderator_role():
	if not frappe.db.exists("Role", "ECM Moderator"):
		role = frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": "ECM Moderator",
				"home_page": "",
				"desk_access": 0,
			}
		)
		role.save()


def create_evaluator_role():
	if not frappe.db.exists("Role", "Batch Evaluator"):
		role = frappe.new_doc("Role")
		role.update(
			{
				"role_name": "Batch Evaluator",
				"home_page": "",
				"desk_access": 0,
			}
		)
		role.save()


def create_ecm_host_role():
	if not frappe.db.exists("Role", "ECM Host"):
		role = frappe.new_doc("Role")
		role.update(
			{
				"role_name": "ECM Host",
				"home_page": "",
				"desk_access": 0,
			}
		)
		role.save()


def set_default_certificate_print_format():
	filters = {
		"doc_type": "ECM Certificate",
		"property": "default_print_format",
	}
	if not frappe.db.exists("Property Setter", filters):
		filters.update(
			{
				"doctype_or_field": "DocType",
				"property_type": "Data",
				"value": "Certificate",
			}
		)

		doc = frappe.new_doc("Property Setter")
		doc.update(filters)
		doc.save()


def delete_custom_fields():
	fields = [
		"user_category",
		"headline",
		"college",
		"city",
		"verify_terms",
		"country",
		"preferred_location",
		"preferred_functions",
		"preferred_industries",
		"work_environment_column",
		"time",
		"role",
		"carrer_preference_details",
		"skill",
		"certification_details",
		"internship",
		"branch",
		"github",
		"medium",
		"linkedin",
		"profession",
		"looking_for_job",
		"cover_image" "work_environment",
		"dream_companies",
		"career_preference_column",
		"attire",
		"collaboration",
		"location_preference",
		"company_type",
		"skill_details",
		"certification",
		"education",
		"work_experience",
		"education_details",
		"hide_private",
		"work_experience_details",
		"profile_complete",
	]

	for field in fields:
		frappe.db.delete("Custom Field", {"fieldname": field})


def create_batch_source():
	sources = [
		"Newsletter",
		"LinkedIn",
		"Twitter",
		"Website",
		"Friend/Colleague/Connection",
		"Google Search",
	]

	for source in sources:
		if not frappe.db.exists("ECM Source", source):
			doc = frappe.new_doc("ECM Source")
			doc.source = source
			doc.save()
