import re
import string
import frappe
import json
import razorpay
import requests
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_result
from frappe.desk.doctype.notification_log.notification_log import (
	make_notification_logs,
	enqueue_create_notification,
	get_title,
)
from frappe.desk.search import get_user_groups
from frappe.desk.notifications import extract_mentions
from frappe.utils import (
	add_months,
	cint,
	cstr,
	flt,
	fmt_money,
	format_date,
	get_datetime,
	getdate,
	validate_phone_number,
	get_fullname,
	pretty_date,
	get_time_str,
	nowtime,
	format_datetime,
)
from frappe.utils.dateutils import get_period
from ecm.events_connect_management.md import find_macros, markdown_to_html

RE_SLUG_NOTALLOWED = re.compile("[^a-z0-9]+")


def slugify(title, used_slugs=None):
	"""Converts title to a slug.

	If a list of used slugs is specified, it will make sure the generated slug
	is not one of them.

	    >>> slugify("Hello World!")
	    'hello-world'
	    >>> slugify("Hello World!", ['hello-world'])
	    'hello-world-2'
	    >>> slugify("Hello World!", ['hello-world', 'hello-world-2'])
	    'hello-world-3'
	"""
	if not used_slugs:
		used_slugs = []

	slug = RE_SLUG_NOTALLOWED.sub("-", title.lower()).strip("-")
	used_slugs = set(used_slugs)

	if slug not in used_slugs:
		return slug

	count = 2
	while True:
		new_slug = f"{slug}-{count}"
		if new_slug not in used_slugs:
			return new_slug
		count = count + 1


def generate_slug(title, doctype):
	result = frappe.get_all(doctype, fields=["name"])
	slugs = {row["name"] for row in result}
	return slugify(title, used_slugs=slugs)


def get_membership(event, member=None, batch=None):
	if not member:
		member = frappe.session.user

	filters = {"member": member, "event": event}
	if batch:
		filters["batch_old"] = batch

	is_member = frappe.db.exists("EventsConnect Enrollment", filters)
	if is_member:
		membership = frappe.db.get_value(
			"EventsConnect Enrollment",
			filters,
			["name", "batch_old", "current_lesson", "member_type", "progress", "member"],
			as_dict=True,
		)

		if membership and membership.batch_old:
			membership.batch_title = frappe.db.get_value(
				"EventsConnect Batch Old", membership.batch_old, "title"
			)
		return membership

	return False


def get_chapters(event):
	"""Returns all chapters of this event."""
	if not event:
		return []
	chapters = frappe.get_all(
		"Chapter Reference", {"parent": event}, ["idx", "chapter"], order_by="idx"
	)
	for chapter in chapters:
		chapter_details = frappe.db.get_value(
			"Event Chapter",
			{"name": chapter.chapter},
			["name", "title", "description"],
			as_dict=True,
		)
		chapter.update(chapter_details)
	return chapters


def get_lessons(event, chapter=None, get_details=True, progress=False):
	"""If chapter is passed, returns lessons of only that chapter.
	Else returns lessons of all chapters of the event"""
	lessons = []
	lesson_count = 0
	if chapter:
		if get_details:
			return get_lesson_details(chapter, progress=progress)
		else:
			return frappe.db.count("Lesson Reference", {"parent": chapter.name})

	for chapter in get_chapters(event):
		if get_details:
			lessons += get_lesson_details(chapter, progress=progress)
		else:
			lesson_count += frappe.db.count("Lesson Reference", {"parent": chapter.name})

	return lessons if get_details else lesson_count


def get_lesson_details(chapter, progress=False):
	lessons = []
	lesson_list = frappe.get_all(
		"Lesson Reference", {"parent": chapter.name}, ["lesson", "idx"], order_by="idx"
	)
	for row in lesson_list:
		lesson_details = frappe.db.get_value(
			"Event Lesson",
			row.lesson,
			[
				"name",
				"title",
				"include_in_preview",
				"body",
				"creation",
				"youtube",
				"quiz_id",
				"question",
				"file_type",
				"instructor_notes",
				"event",
			],
			as_dict=True,
		)
		lesson_details.number = f"{chapter.idx}.{row.idx}"
		lesson_details.icon = get_lesson_icon(lesson_details.body)

		if progress:
			lesson_details.is_complete = get_progress(lesson_details.event, lesson_details.name)

		lessons.append(lesson_details)
	return lessons


def get_lesson_icon(content):
	icon = None
	macros = find_macros(content)

	for macro in macros:
		if macro[0] == "YouTubeVideo" or macro[0] == "Video":
			icon = "icon-youtube"
		elif macro[0] == "Quiz":
			icon = "icon-quiz"

	if not icon:
		icon = "icon-list"

	return icon


@frappe.whitelist(allow_guest=True)
def get_tags(event):
	tags = frappe.db.get_value("EventsConnect Event", event, "tags")
	return tags.split(",") if tags else []


def get_instructors(event):
	instructor_details = []
	instructors = frappe.get_all(
		"Event Instructor", {"parent": event}, order_by="idx", pluck="instructor"
	)

	for instructor in instructors:
		instructor_details.append(
			frappe.db.get_value(
				"User",
				instructor,
				["name", "username", "full_name", "user_image", "first_name"],
				as_dict=True,
			)
		)
	return instructor_details


def get_students(event, batch=None):
	"""Returns (email, full_name, username) of all the students of this batch as a list of dict."""
	filters = {"event": event, "member_type": "Student"}

	if batch:
		filters["batch_old"] = batch

	return frappe.get_all("EventsConnect Enrollment", filters, ["member"])


def get_average_rating(event):
	ratings = [review.rating for review in get_reviews(event)]
	if not len(ratings):
		return None
	return sum(ratings) / len(ratings)


@frappe.whitelist(allow_guest=True)
def get_reviews(event):
	reviews = frappe.get_all(
		"ECM Event Review",
		{"event": event},
		["review", "rating", "owner", "creation"],
		order_by="creation desc",
	)

	out_of_ratings = frappe.db.get_all(
		"DocField", {"parent": "ECM Event Review", "fieldtype": "Rating"}, ["options"]
	)
	out_of_ratings = (len(out_of_ratings) and out_of_ratings[0].options) or 5
	for review in reviews:
		review.rating = review.rating * out_of_ratings
		review.owner_details = frappe.db.get_value(
			"User", review.owner, ["name", "username", "full_name", "user_image"], as_dict=True
		)
		review.creation = pretty_date(review.creation)

	return reviews


def get_sorted_reviews(event):
	rating_count = rating_percent = frappe._dict()
	keys = ["5.0", "4.0", "3.0", "2.0", "1.0"]
	for key in keys:
		rating_count[key] = 0

	reviews = get_reviews(event)
	for review in reviews:
		rating_count[cstr(review.rating)] += 1

	for key in keys:
		rating_percent[key] = rating_count[key] / len(reviews) * 100

	return rating_percent


def is_certified(event):
	certificate = frappe.get_all(
		"EventsConnect Certificate", {"member": frappe.session.user, "event": event}
	)
	if len(certificate):
		return certificate[0].name
	return


def get_lesson_index(lesson_name):
	"""Returns the {chapter_index}.{lesson_index} for the lesson."""
	lesson = frappe.db.get_value(
		"Lesson Reference", {"lesson": lesson_name}, ["idx", "parent"], as_dict=True
	)
	if not lesson:
		return "1-1"

	chapter = frappe.db.get_value(
		"Chapter Reference", {"chapter": lesson.parent}, ["idx"], as_dict=True
	)
	if not chapter:
		return "1-1"

	return f"{chapter.idx}-{lesson.idx}"


def get_lesson_url(event, lesson_number):
	if not lesson_number:
		return
	return f"/events/{event}/learn/{lesson_number}"


def get_batch(event, batch_name):
	return frappe.get_all("EventsConnect Batch Old", {"name": batch_name, "event": event})


def get_slugified_chapter_title(chapter):
	return slugify(chapter)


def get_progress(event, lesson, member=None):
	if not member:
		member = frappe.session.user

	return frappe.db.exists(
		"EventsConnect Event Progress",
		{"event": event, "member": member, "lesson": lesson},
		["status"],
	)


def render_html(lesson):
	youtube = lesson.youtube
	quiz_id = lesson.quiz_id
	body = lesson.body

	if youtube and "/" in youtube:
		youtube = youtube.split("/")[-1]

	quiz_id = "{{ Quiz('" + quiz_id + "') }}" if quiz_id else ""
	youtube = "{{ YouTubeVideo('" + youtube + "') }}" if youtube else ""
	text = youtube + body + quiz_id

	if lesson.question:
		assignment = "{{ Assignment('" + lesson.question + "-" + lesson.file_type + "') }}"
		text = text + assignment

	return markdown_to_html(text)


def is_mentor(event, email):
	"""Checks if given user is a mentor for this event."""
	if not email:
		return False
	return frappe.db.count(
		"EventsConnect Event Mentor Mapping", {"event": event, "mentor": email}
	)


def is_cohort_staff(event, user_email):
	"""Returns True if the user is either a mentor or a staff for one or more active cohorts of this event."""
	staff = {"doctype": "Cohort Staff", "event": event, "email": user_email}
	mentor = {"doctype": "Cohort Mentor", "event": event, "email": user_email}
	return frappe.db.exists(staff) or frappe.db.exists(mentor)


def get_mentors(event):
	"""Returns the list of all mentors for this event."""
	event_mentors = []
	mentors = frappe.get_all("EventsConnect Event Mentor Mapping", {"event": event}, ["mentor"])
	for mentor in mentors:
		member = frappe.db.get_value(
			"User", mentor.mentor, ["name", "username", "full_name", "user_image"]
		)
		member.batch_count = frappe.db.count(
			"EventsConnect Enrollment", {"member": member.name, "member_type": "Mentor"}
		)
		event_mentors.append(member)
	return event_mentors


def is_eligible_to_review(event):
	"""Checks if user is eligible to review the event"""
	if frappe.db.count(
		"EventsConnect Event Review", {"event": event, "owner": frappe.session.user}
	):
		return False
	return True


def get_event_progress(event, member=None):
	"""Returns the event progress of the session user"""
	lesson_count = get_lessons(event, get_details=False)
	if not lesson_count:
		return 0
	completed_lessons = frappe.db.count(
		"EventsConnect Event Progress",
		{"event": event, "member": member or frappe.session.user, "status": "Complete"},
	)
	precision = cint(frappe.db.get_default("float_precision")) or 3
	return flt(((completed_lessons / lesson_count) * 100), precision)


def get_initial_members(event):
	members = frappe.get_all("EventsConnect Enrollment", {"event": event}, ["member"], limit=3)

	member_details = []
	for member in members:
		member_details.append(
			frappe.db.get_value(
				"User", member.member, ["name", "username", "full_name", "user_image"], as_dict=True
			)
		)

	return member_details


def is_instructor(event):
	return (
		len(list(filter(lambda x: x.name == frappe.session.user, get_instructors(event))))
		> 0
	)


def convert_number_to_character(number):
	return string.ascii_uppercase[number]


def get_signup_optin_checks():

	mapper = frappe._dict(
		{
			"terms_of_use": {"page_name": "terms_page", "title": _("Terms of Use")},
			"privacy_policy": {"page_name": "privacy_policy_page", "title": _("Privacy Policy")},
			"cookie_policy": {"page_name": "cookie_policy_page", "title": _("Cookie Policy")},
		}
	)
	checks = ["terms_of_use", "privacy_policy", "cookie_policy"]
	links = []

	for check in checks:
		if frappe.db.get_single_value("EventsConnect Settings", check):
			page = frappe.db.get_single_value("EventsConnect Settings", mapper[check].get("page_name"))
			route = frappe.db.get_value("Web Page", page, "route")
			links.append("<a href='/" + route + "'>" + mapper[check].get("title") + "</a>")

	return (", ").join(links)


def get_popular_events():
	events = frappe.get_all("EventsConnect Event", {"published": 1, "upcoming": 0})
	event_membership = []

	for event in events:
		event_membership.append(
			{
				"event": event.name,
				"members": cint(frappe.db.count("EventsConnect Enrollment", {"event": event.name})),
			}
		)

	event_membership = sorted(
		event_membership, key=lambda x: x.get("members"), reverse=True
	)
	return event_membership[:3]


def get_evaluation_details(event, member=None):
	info = frappe.db.get_value(
		"EventsConnect Event",
		event,
		["grant_certificate_after", "max_attempts", "duration"],
		as_dict=True,
	)
	request = frappe.db.get_value(
		"EventsConnect Certificate Request",
		{
			"event": event,
			"member": member or frappe.session.user,
			"date": [">=", getdate()],
		},
		["date", "start_time", "end_time"],
		as_dict=True,
	)

	no_of_attempts = frappe.db.count(
		"EventsConnect Certificate Evaluation",
		{
			"event": event,
			"member": member or frappe.session.user,
			"status": ["!=", "Pass"],
			"creation": [">=", add_months(getdate(), -abs(cint(info.duration)))],
		},
	)

	return frappe._dict(
		{
			"eligible": info.grant_certificate_after == "Evaluation"
			and not request
			and no_of_attempts < info.max_attempts,
			"request": request,
			"no_of_attempts": no_of_attempts,
		}
	)


def format_amount(amount, currency):
	amount_reduced = amount / 1000
	if amount_reduced < 1:
		return fmt_money(amount, 0, currency)
	precision = 0 if amount % 1000 == 0 else 1
	return _("{0}k").format(fmt_money(amount_reduced, precision, currency))


def format_number(number):
	number_reduced = number / 1000
	if number_reduced < 1:
		return number
	return f"{frappe.utils.flt(number_reduced, 1)}k"


def first_lesson_exists(event):
	first_chapter = frappe.db.get_value(
		"Chapter Reference", {"parent": event, "idx": 1}, "name"
	)
	if not first_chapter:
		return False

	first_lesson = frappe.db.get_value(
		"Lesson Reference", {"parent": first_chapter, "idx": 1}, "name"
	)
	if not first_lesson:
		return False

	return True


def redirect_to_events_list():
	frappe.local.flags.redirect_location = "/eventsconnect/events"
	raise frappe.Redirect


def has_event_instructor_role(member=None):
	return frappe.db.get_value(
		"Has Role",
		{"parent": member or frappe.session.user, "role": "Event Creator"},
		"name",
	)


def can_create_events(event, member=None):
	if not member:
		member = frappe.session.user

	instructors = frappe.get_all(
		"Event Instructor",
		{
			"parent": event,
		},
		pluck="instructor",
	)

	if frappe.session.user == "Guest":
		return False

	if has_event_moderator_role(member):
		return True

	if has_event_instructor_role(member) and member in instructors:
		return True

	portal_event_creation = frappe.db.get_single_value(
		"EventsConnect Settings", "portal_event_creation"
	)

	if portal_event_creation == "Anyone" and member in instructors:
		return True

	if not event and has_event_instructor_role(member):
		return True

	return False


def has_event_moderator_role(member=None):
	return frappe.db.get_value(
		"Has Role",
		{"parent": member or frappe.session.user, "role": "Moderator"},
		"name",
	)


def has_event_evaluator_role(member=None):
	return frappe.db.get_value(
		"Has Role",
		{"parent": member or frappe.session.user, "role": "Batch Evaluator"},
		"name",
	)


def has_student_role(member=None):
	return frappe.db.get_value(
		"Has Role",
		{"parent": member or frappe.session.user, "role": "EventsConnect Student"},
		"name",
	)


def get_events_under_review():
	return frappe.get_all(
		"ECM Events",
		{"status": "Under Review"},
		[
			"name",
			"upcoming",
			"title",
			"short_introduction",
			"image",
			"paid_event",
			"event_price",
			"currency",
			"status",
			"published",
		],
	)


def get_certificates(member=None):
	return frappe.get_all(
		"EventsConnect Certificate",
		{"member": member or frappe.session.user},
		["event", "member", "issue_date", "expiry_date", "name"],
	)


def validate_image(path):
	if path and "/private" in path:
		file = frappe.get_doc("File", {"file_url": path})
		file.is_private = 0
		file.save()
		return file.file_url
	return path


def handle_notifications(doc, method):
	topic = frappe.db.get_value(
		"Discussion Topic",
		doc.topic,
		["reference_doctype", "reference_docname", "owner", "title"],
		as_dict=1,
	)
	if topic.reference_doctype not in ["Event Lesson", "EventsConnect Batch"]:
		return
	create_notification_log(doc, topic)
	notify_mentions_on_portal(doc, topic)
	notify_mentions_via_email(doc, topic)


def create_notification_log(doc, topic):
	users = []
	if topic.reference_doctype == "Event Lesson":
		event = frappe.db.get_value("Event Lesson", topic.reference_docname, "event")
		event_title = frappe.db.get_value("EventsConnect Event", event, "title")
		instructors = frappe.db.get_all(
			"Event Instructor", {"parent": event}, pluck="instructor"
		)

		if doc.owner != topic.owner:
			users.append(topic.owner)

		users += instructors
		subject = _("New reply on the topic {0} in event {1}").format(
			topic.title, event_title
		)
		link = get_lesson_url(event, get_lesson_index(topic.reference_docname))

	else:
		batch_title = frappe.db.get_value("EventsConnect Batch", topic.reference_docname, "title")
		subject = _("New comment in batch {0}").format(batch_title)
		link = f"/batches/{topic.reference_docname}"
		moderators = frappe.get_all("Has Role", {"role": "Moderator"}, pluck="parent")
		users += moderators

	notification = frappe._dict(
		{
			"subject": subject,
			"email_content": doc.reply,
			"document_type": topic.reference_doctype,
			"document_name": topic.reference_docname,
			"for_user": topic.owner,
			"from_user": doc.owner,
			"type": "Alert",
			"link": link,
		}
	)

	make_notification_logs(notification, users)


def notify_mentions_on_portal(doc, topic):
	mentions = extract_mentions(doc.reply)
	if not mentions:
		return

	from_user_name = get_fullname(doc.owner)

	if topic.reference_doctype == "Event Lesson":
		event = frappe.db.get_value("Event Lesson", topic.reference_docname, "event")
		subject = _("{0} mentioned you in a comment in {1}").format(
			from_user_name, topic.title
		)
		link = get_lesson_url(event, get_lesson_index(topic.reference_docname))
	else:
		batch_title = frappe.db.get_value("EventsConnect Batch", topic.reference_docname, "title")
		subject = _("{0} mentioned you in a comment in {1}").format(
			from_user_name, batch_title
		)
		link = f"/batches/{topic.reference_docname}"

	for user in mentions:
		notification = frappe._dict(
			{
				"subject": subject,
				"email_content": doc.reply,
				"document_type": topic.reference_doctype,
				"document_name": topic.reference_docname,
				"for_user": user,
				"from_user": doc.owner,
				"type": "Alert",
				"link": link,
			}
		)
		make_notification_logs(notification, user)


def notify_mentions_via_email(doc, topic):
	outgoing_email_account = frappe.get_cached_value(
		"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
	)
	if not outgoing_email_account or not frappe.conf.get("mail_login"):
		return

	mentions = extract_mentions(doc.reply)
	if not mentions:
		return

	sender_fullname = get_fullname(doc.owner)
	recipients = [
		frappe.db.get_value(
			"User",
			{"enabled": 1, "name": name},
			"email",
		)
		for name in mentions
	]
	subject = _("{0} mentioned you in a comment").format(sender_fullname)
	template = "mention_template"

	if topic.reference_doctype == "EventsConnect Batch":
		link = f"/batches/{topic.reference_docname}#discussions"
	if topic.reference_doctype == "Event Lesson":
		event = frappe.db.get_value("Event Lesson", topic.reference_docname, "event")
		lesson_index = get_lesson_index(topic.reference_docname)
		link = get_lesson_url(event, lesson_index)

	args = {
		"sender": sender_fullname,
		"content": doc.reply,
		"link": link,
	}

	for recipient in recipients:
		frappe.sendmail(
			recipients=recipient,
			subject=subject,
			template=template,
			args=args,
			header=[subject, "green"],
			retry=3,
		)


def get_lesson_count(event):
	lesson_count = 0
	chapters = frappe.get_all("Chapter Reference", {"parent": event}, ["chapter"])
	for chapter in chapters:
		lesson_count += frappe.db.count("Lesson Reference", {"parent": chapter.chapter})

	return lesson_count


def get_restriction_details():
	user = frappe.db.get_value(
		"User", frappe.session.user, ["profile_complete", "username"], as_dict=True
	)
	return {
		"restrict": not user.profile_complete,
		"username": user.username,
		"prefix": frappe.get_hooks("profile_url_prefix")[0] or "/users/",
	}


def get_all_memberships(member):
	return frappe.get_all(
		"EventsConnect Enrollment",
		{"member": member},
		["name", "event", "batch_old", "current_lesson", "member_type", "progress"],
	)


def get_filtered_membership(event, memberships):
	current_membership = list(filter(lambda x: x.event == event, memberships))
	return current_membership[0] if len(current_membership) else None


def show_start_learing_cta(event, membership):

	if event.disable_self_learning or event.upcoming:
		return False
	if is_instructor(event.name):
		return False
	if event.status != "Approved":
		return False
	if not has_lessons(event):
		return False
	if not membership:
		return True


def has_lessons(event):
	lesson_exists = False
	chapter_exists = frappe.db.get_value(
		"Chapter Reference", {"parent": event.name}, ["name", "chapter"], as_dict=True
	)

	if chapter_exists:
		lesson_exists = frappe.db.exists(
			"Lesson Reference", {"parent": chapter_exists.chapter}
		)

	return lesson_exists


@frappe.whitelist(allow_guest=True)
def get_chart_data(
	chart_name,
	timespan="Select Date Range",
	timegrain="Daily",
	from_date=None,
	to_date=None,
):
	if not from_date:
		from_date = add_months(getdate(), -1)
	if not to_date:
		to_date = getdate()
	chart = frappe.get_doc("Dashboard Chart", chart_name)
	filters = [([chart.document_type, "docstatus", "<", 2, False])]
	doctype = chart.document_type
	datefield = chart.based_on
	value_field = chart.value_based_on or "1"
	from_date = get_datetime(from_date).strftime("%Y-%m-%d")
	to_date = get_datetime(to_date)

	filters.append([doctype, datefield, ">=", from_date, False])
	filters.append([doctype, datefield, "<=", to_date, False])

	data = frappe.db.get_all(
		doctype,
		fields=[f"{datefield} as _unit", f"SUM({value_field})", "COUNT(*)"],
		filters=filters,
		group_by="_unit",
		order_by="_unit asc",
		as_list=True,
	)

	result = get_result(data, timegrain, from_date, to_date, chart.chart_type)

	return {
		"labels": [
			format_date(get_period(r[0], timegrain), parse_day_first=True)
			if timegrain in ("Daily", "Weekly")
			else get_period(r[0], timegrain)
			for r in result
		],
		"datasets": [{"name": chart.name, "data": [r[1] for r in result]}],
	}


@frappe.whitelist(allow_guest=True)
def get_event_completion_data():
	all_membership = frappe.db.count("EventsConnect Enrollment")
	completed = frappe.db.count("EventsConnect Enrollment", {"progress": ["like", "%100%"]})

	return {
		"labels": ["Completed", "In Progress"],
		"datasets": [
			{
				"name": "Event Completion",
				"data": [completed, all_membership - completed],
			}
		],
	}


def get_telemetry_boot_info():
	POSTHOG_PROJECT_FIELD = "posthog_project_id"
	POSTHOG_HOST_FIELD = "posthog_host"

	if not frappe.conf.get(POSTHOG_HOST_FIELD) or not frappe.conf.get(
		POSTHOG_PROJECT_FIELD
	):
		return {}

	return {
		"posthog_host": frappe.conf.get(POSTHOG_HOST_FIELD),
		"posthog_project_id": frappe.conf.get(POSTHOG_PROJECT_FIELD),
		"enable_telemetry": 1,
	}


def is_onboarding_complete():
	event_created = frappe.db.a_row_exists("EventsConnect Event")
	chapter_created = frappe.db.a_row_exists("Event Chapter")
	lesson_created = frappe.db.a_row_exists("Event Lesson")

	if event_created and chapter_created and lesson_created:
		frappe.db.set_single_value("EventsConnect Settings", "is_onboarding_complete", 1)

	return {
		"is_onboarded": frappe.db.get_single_value("EventsConnect Settings", "is_onboarding_complete"),
		"event_created": event_created,
		"chapter_created": chapter_created,
		"lesson_created": lesson_created,
		"first_event": frappe.get_all("EventsConnect Event", limit=1, order_by=None, pluck="name")[0]
		if event_created
		else None,
	}


def has_submitted_assessment(assessment, type, member=None):
	if not member:
		member = frappe.session.user

	doctype = (
		"EventsConnect Assignment Submission" if type == "EventsConnect Assignment" else "EventsConnect Quiz Submission"
	)
	docfield = "assignment" if type == "EventsConnect Assignment" else "quiz"

	filters = {}
	filters[docfield] = assessment
	filters["member"] = member
	return frappe.db.exists(doctype, filters)


def has_graded_assessment(submission):
	status = frappe.db.get_value("EventsConnect Assignment Submission", submission, "status")
	return False if status == "Not Graded" else True


def get_evaluator(event, batch=None):
	evaluator = None

	if batch:
		evaluator = frappe.db.get_value(
			"Batch Event",
			{"parent": batch, "event": event},
			"evaluator",
		)

	if not evaluator:
		evaluator = frappe.db.get_value("EventsConnect Event", event, "evaluator")

	return evaluator


@frappe.whitelist()
def get_upcoming_evals(student, events):
	upcoming_evals = frappe.get_all(
		"EventsConnect Certificate Request",
		{
			"member": student,
			"event": ["in", events],
			"date": [">=", frappe.utils.nowdate()],
		},
		["date", "start_time", "event", "evaluator", "google_meet_link"],
		order_by="date",
	)

	for evals in upcoming_evals:
		evals.event_title = frappe.db.get_value("EventsConnect Event", evals.event, "title")
		evals.evaluator_name = frappe.db.get_value("User", evals.evaluator, "full_name")
	return upcoming_evals


@frappe.whitelist()
def get_payment_options(doctype, docname, phone, country):
	if not frappe.db.exists(doctype, docname):
		frappe.throw(_("Invalid document provided."))

	validate_phone_number(phone, True)
	details = get_details(doctype, docname)

	details.amount, details.currency = check_multicurrency(
		details.amount, details.currency, country, details.amount_usd
	)
	if details.currency == "INR":
		details.amount, details.gst_applied = apply_gst(details.amount, country)

	client = get_client()
	order = create_order(client, details.amount, details.currency)

	options = {
		"key_id": frappe.db.get_single_value("EventsConnect Settings", "razorpay_key"),
		"name": frappe.db.get_single_value("Website Settings", "app_name"),
		"description": _("Payment for {0} event").format(details["title"]),
		"order_id": order["id"],
		"amount": cint(order["amount"]) * 100,
		"currency": order["currency"],
		"prefill": {
			"name": frappe.db.get_value("User", frappe.session.user, "full_name"),
			"email": frappe.session.user,
			"contact": phone,
		},
	}
	return options


def check_multicurrency(amount, currency, country=None, amount_usd=None):
	settings = frappe.get_single("EventsConnect Settings")
	show_usd_equivalent = settings.show_usd_equivalent

	# Countries for which currency should not be converted
	exception_country = settings.exception_country
	exception_country = [country.country for country in exception_country]

	# Get users country
	if not country:
		country = frappe.db.get_value("Address", {"email_id": frappe.session.user}, "country")

	if not country:
		country = frappe.db.get_value("User", frappe.session.user, "country")

	if not country:
		country = get_country_code()

	# If the country is the one for which conversion is not needed then return as is
	if not country or (exception_country and country in exception_country):
		return amount, currency

	# If conversion is disabled from settings or the currency is already USD then return as is
	if not show_usd_equivalent or currency == "USD":
		return amount, currency

	# If Explicit USD price is given then return that without conversion
	if amount_usd and country and country not in exception_country:
		return amount_usd, "USD"

	# Conversion logic starts here. Exchange rate is fetched and amount is converted.
	exchange_rate = get_current_exchange_rate(currency, "USD")
	amount = amount * exchange_rate
	currency = "USD"

	# Check if the amount should be rounded and then apply rounding
	apply_rounding = settings.apply_rounding
	if apply_rounding and amount % 100 != 0:
		amount = amount + 100 - amount % 100

	return amount, currency


def apply_gst(amount, country=None):
	gst_applied = 0
	apply_gst = frappe.db.get_single_value("EventsConnect Settings", "apply_gst")

	if not country:
		country = frappe.db.get_value("User", frappe.session.user, "country")

	if apply_gst and country == "India":
		gst_applied = amount * 0.18
		amount += gst_applied

	return amount, gst_applied


def get_details(doctype, docname):
	if doctype == "EventsConnect Event":
		details = frappe.db.get_value(
			"EventsConnect Event",
			docname,
			["name", "title", "paid_event", "currency", "event_price as amount", "amount_usd"],
			as_dict=True,
		)
		if not details.paid_event:
			frappe.throw(_("This event is free."))
	else:
		details = frappe.db.get_value(
			"EventsConnect Batch",
			docname,
			["name", "title", "paid_batch", "currency", "amount", "amount_usd"],
			as_dict=True,
		)
		if not details.paid_batch:
			frappe.throw(_("To join this batch, please contact the Administrator."))

	return details


def save_address(address):
	filters = {"email_id": frappe.session.user}
	exists = frappe.db.exists("Address", filters)
	if exists:
		address_doc = frappe.get_last_doc("Address", filters=filters)
	else:
		address_doc = frappe.new_doc("Address")

	address_doc.update(address)
	address_doc.update(
		{
			"address_title": frappe.db.get_value("User", frappe.session.user, "full_name"),
			"address_type": "Billing",
			"is_primary_address": 1,
			"email_id": frappe.session.user,
		}
	)
	address_doc.save(ignore_permissions=True)
	return address_doc.name


def get_client():
	settings = frappe.get_single("EventsConnect Settings")
	razorpay_key = settings.razorpay_key
	razorpay_secret = settings.get_password("razorpay_secret", raise_exception=True)

	if not razorpay_key and not razorpay_secret:
		frappe.throw(
			_(
				"There is a problem with the payment gateway. Please contact the Administrator to proceed."
			)
		)

	return razorpay.Client(auth=(razorpay_key, razorpay_secret))


def create_order(client, amount, currency):
	try:
		return client.order.create(
			{
				"amount": cint(amount) * 100,
				"currency": currency,
			}
		)
	except Exception as e:
		frappe.throw(
			_(
				"Error during payment: {0} Please contact the Administrator. Amount {1} Currency {2} Formatted {3}"
			).format(e, amount, currency, cint(amount))
		)


@frappe.whitelist()
def verify_payment(response, doctype, docname, address, order_id):
	client = get_client()
	client.utility.verify_payment_signature(
		{
			"razorpay_order_id": order_id,
			"razorpay_payment_id": response["razorpay_payment_id"],
			"razorpay_signature": response["razorpay_signature"],
		}
	)

	payment = record_payment(address, response, client, doctype, docname)
	if doctype == "EventsConnect Event":
		return create_membership(docname, payment)
	else:
		return add_student_to_batch(docname, payment)


def record_payment(address, response, client, doctype, docname):
	address = frappe._dict(address)
	address_name = save_address(address)

	payment_details = get_payment_details(doctype, docname, address)
	payment_doc = frappe.new_doc("EventsConnect Payment")
	payment_doc.update(
		{
			"member": frappe.session.user,
			"billing_name": address.billing_name,
			"address": address_name,
			"payment_received": 1,
			"order_id": response["razorpay_order_id"],
			"payment_id": response["razorpay_payment_id"],
			"amount": payment_details["amount"],
			"currency": payment_details["currency"],
			"amount_with_gst": payment_details["amount_with_gst"],
			"gstin": address.gstin,
			"pan": address.pan,
			"source": address.source,
			"payment_for_document_type": doctype,
			"payment_for_document": docname,
		}
	)
	payment_doc.save(ignore_permissions=True)
	return payment_doc


def get_payment_details(doctype, docname, address):
	amount_field = "event_price" if doctype == "EventsConnect Event" else "amount"
	amount = frappe.db.get_value(doctype, docname, amount_field)
	currency = frappe.db.get_value(doctype, docname, "currency")
	amount_usd = frappe.db.get_value(doctype, docname, "amount_usd")
	amount_with_gst = 0

	amount, currency = check_multicurrency(amount, currency, None, amount_usd)
	if currency == "INR" and address.country == "India":
		amount_with_gst, gst_applied = apply_gst(amount, address.country)

	return {
		"amount": amount,
		"currency": currency,
		"amount_with_gst": amount_with_gst,
	}


def create_membership(event, payment):
	membership = frappe.new_doc("EventsConnect Enrollment")
	membership.update(
		{"member": frappe.session.user, "event": event, "payment": payment.name}
	)
	membership.save(ignore_permissions=True)
	return f"/eventsconnect/events/{event}/learn/1-1"


def add_student_to_batch(batchname, payment):
	student = frappe.new_doc("Batch Student")
	current_count = frappe.db.count("Batch Student", {"parent": batchname})
	student.update(
		{
			"student": frappe.session.user,
			"payment": payment.name,
			"source": payment.source,
			"parent": batchname,
			"parenttype": "EventsConnect Batch",
			"parentfield": "students",
			"idx": current_count + 1,
		}
	)
	student.save(ignore_permissions=True)
	return f"/batches/{batchname}"


def get_current_exchange_rate(source, target="USD"):
	url = f"https://api.frankfurter.app/latest?from={source}&to={target}"

	response = requests.request("GET", url)
	details = response.json()
	return details["rates"][target]


@frappe.whitelist()
def change_currency(amount, currency, country=None):
	amount = cint(amount)
	amount, currency = check_multicurrency(amount, currency, country)
	return fmt_money(amount, 0, currency)


@frappe.whitelist(allow_guest=True)
def get_events(search_query=""):
	"""Returns the list of events."""
	events = []
	event_list = frappe.get_all(
		"ECM Events", {"title": ["like", f"%{search_query}%"]}, pluck="name"
	)
	for event in event_list:
		events.append(get_event_details(event))

	events = get_categorized_events(events)
	return events


@frappe.whitelist(allow_guest=True)
def get_event_details(event):
	event_details = frappe.db.get_value(
		"ECM Events",
		event,
		[
			  "name",
			  "title",
				"start_time",
				"finish_time",
				"cover_image",
				"category",
				"location",
				"location_map",
				"about_event",
				"full_description",
				"number_of_participate",
				"group",
				"control_level",
				"suggested_cost",
				"is_price_negotiable",
				"start_date",
				"finish_date",
				"status",
				"owner",
				"country",
				"province",
				"city"
		],
		as_dict=1,
	)
	
	return event_details


@frappe.whitelist(allow_guest=True)
def get_event_group_options():
    doctype = 'ECM Events'
    fields = 'group'
    options = {}
    

    field = frappe.get_meta(doctype).get_field(fields)
    if field.fieldtype == 'Select':
        options[fields] = field.options.split('\n')
    
    return options
@frappe.whitelist(allow_guest=True)
def get_event_pricenegotiate_options():
    doctype = 'ECM Events'
    fields = 'is_price_negotiable'
    options = {}
    

    field = frappe.get_meta(doctype).get_field(fields)
    if field.fieldtype == 'Select':
        options[fields] = field.options.split('\n')
    
    return options

@frappe.whitelist(allow_guest=True)
def get_event_control_level_options():
    doctype = 'ECM Events'
    fields = 'control_level'
    options = {}
    

    field = frappe.get_meta(doctype).get_field(fields)
    if field.fieldtype == 'Select':
        options[fields] = field.options.split('\n')
    
    return options

def get_categorized_events(events):
	featured, upcoming, new, enrolled, created, under_review = [], [], [], [], [], []

	for event in events:
		if event.status == "Under Review":
			under_review.append(event)
		elif event.status == "Upcoming" :
			upcoming.append(event)
		elif event.status == "Featured":
			featured.append(event)

		if (
			event.published
			and not event.upcoming
			and event.published_on > add_months(getdate(), -3)
		):
			new.append(event)

		if event.membership and event.published:
			enrolled.append(event)
		elif event.is_instructor:
			created.append(event)

		categories = [featured, enrolled, created]
		for category in categories:
			category.sort(key=lambda x: x.enrollment_count, reverse=True)

		featured.sort(key=lambda x: x.featured, reverse=True)

	return {
		"featured": featured,
		"new": new,
		"upcoming": upcoming,
		"enrolled": enrolled,
		"created": created,
		"under_review": under_review,
	}


@frappe.whitelist(allow_guest=True)
def get_event_task(event):

	tasks = frappe.get_all("Event Tasks", {"parent": event},["title","description"]
	)

	return tasks


@frappe.whitelist(allow_guest=True)
def get_lesson(event, chapter, lesson):
	chapter_name = frappe.db.get_value(
		"Chapter Reference", {"parent": event, "idx": chapter}, "chapter"
	)
	lesson_name = frappe.db.get_value(
		"Lesson Reference", {"parent": chapter_name, "idx": lesson}, "lesson"
	)
	lesson_details = frappe.db.get_value(
		"Event Lesson", lesson_name, ["include_in_preview", "title"], as_dict=1
	)
	membership = get_membership(event)
	event_title = frappe.db.get_value("EventsConnect Event", event, "title")
	if (
		not lesson_details.include_in_preview
		and not membership
		and not has_event_moderator_role()
		and not is_instructor(event)
	):
		return {"no_preview": 1, "title": lesson_details.title, "event_title": event_title}

	lesson_details = frappe.db.get_value(
		"Event Lesson",
		lesson_name,
		[
			"name",
			"title",
			"include_in_preview",
			"body",
			"creation",
			"youtube",
			"quiz_id",
			"question",
			"file_type",
			"instructor_notes",
			"event",
			"content",
			"instructor_content",
		],
		as_dict=True,
	)

	if frappe.session.user == "Guest":
		progress = 0
	else:
		progress = get_progress(event, lesson_details.name)

	lesson_details.rendered_content = render_html(lesson_details)
	neighbours = get_neighbour_lesson(event, chapter, lesson)
	lesson_details.next = neighbours["next"]
	lesson_details.progress = progress
	lesson_details.prev = neighbours["prev"]
	lesson_details.membership = membership
	lesson_details.instructors = get_instructors(event)
	lesson_details.event_title = event_title
	return lesson_details


def get_neighbour_lesson(event, chapter, lesson):
	numbers = []
	current = f"{chapter}.{lesson}"
	chapters = frappe.get_all("Chapter Reference", {"parent": event}, ["idx", "chapter"])
	for chapter in chapters:
		lessons = frappe.get_all("Lesson Reference", {"parent": chapter.chapter}, pluck="idx")
		for lesson in lessons:
			numbers.append(f"{chapter.idx}.{lesson}")

	tuples_list = [tuple(int(x) for x in s.split(".")) for s in numbers]
	sorted_tuples = sorted(tuples_list)
	sorted_numbers = [".".join(str(num) for num in t) for t in sorted_tuples]
	index = sorted_numbers.index(current)

	return {
		"prev": sorted_numbers[index - 1] if index - 1 >= 0 else None,
		"next": sorted_numbers[index + 1] if index + 1 < len(sorted_numbers) else None,
	}


@frappe.whitelist(allow_guest=True)
def get_batches():
	batches = []
	filters = {}
	if frappe.session.user == "Guest":
		filters.update({"start_date": [">=", getdate()], "published": 1})
	batch_list = frappe.get_all("EventsConnect Batch", filters)

	for batch in batch_list:
		batches.append(get_batch_details(batch.name))

	batches = categorize_batches(batches)
	return batches


@frappe.whitelist(allow_guest=True)
def get_batch_details(batch):
	batch_details = frappe.db.get_value(
		"EventsConnect Batch",
		batch,
		[
			"name",
			"title",
			"description",
			"batch_details",
			"batch_details_raw",
			"start_date",
			"end_date",
			"start_time",
			"end_time",
			"seat_count",
			"published",
			"amount",
			"amount_usd",
			"currency",
			"paid_batch",
			"evaluation_end_date",
			"allow_self_enrollment",
			"timezone",
		],
		as_dict=True,
	)

	batch_details.instructors = get_instructors(batch)

	batch_details.events = frappe.get_all(
		"Batch Event", filters={"parent": batch}, fields=["event", "title"]
	)
	batch_details.students = frappe.get_all(
		"Batch Student", {"parent": batch}, pluck="student"
	)
	if batch_details.paid_batch and batch_details.start_date >= getdate():
		batch_details.amount, batch_details.currency = check_multicurrency(
			batch_details.amount, batch_details.currency, None, batch_details.amount_usd
		)
		batch_details.price = fmt_money(batch_details.amount, 0, batch_details.currency)

	if batch_details.seat_count:
		batch_details.seats_left = batch_details.seat_count - len(batch_details.students)

	return batch_details


def categorize_batches(batches):
	upcoming, archived, private, enrolled = [], [], [], []

	for batch in batches:
		if not batch.published:
			private.append(batch)
		elif getdate(batch.start_date) < getdate():
			archived.append(batch)
		elif (
			getdate(batch.start_date) == getdate() and get_time_str(batch.start_time) < nowtime()
		):
			archived.append(batch)
		else:
			upcoming.append(batch)

		if frappe.session.user != "Guest":
			if frappe.db.exists(
				"Batch Student", {"student": frappe.session.user, "parent": batch.name}
			):
				enrolled.append(batch)

	categories = [archived, private, enrolled]
	for category in categories:
		category.sort(key=lambda x: x.start_date, reverse=True)

	upcoming.sort(key=lambda x: x.start_date)
	return {
		"upcoming": upcoming,
		"archived": archived,
		"private": private,
		"enrolled": enrolled,
	}


def get_country_code():
	ip = frappe.local.request_ip
	res = requests.get(f"http://ip-api.com/json/{ip}")

	try:
		data = res.json()
		if data.get("status") != "fail":
			return frappe.db.get_value("Country", {"code": data.get("countryCode")}, "name")
	except Exception:
		pass
	return


@frappe.whitelist()
def get_question_details(question):
	fields = ["question", "type", "multiple"]
	for i in range(1, 5):
		fields.append(f"option_{i}")
		fields.append(f"explanation_{i}")
		fields.append(f"is_correct_{i}")

	question_details = frappe.db.get_value("EventsConnect Question", question, fields, as_dict=1)
	return question_details


@frappe.whitelist(allow_guest=True)
def get_batch_events(batch):
	events = []
	event_list = frappe.get_all("Batch Event", {"parent": batch}, ["name", "event"])

	for event in event_list:
		details = get_event_details(event.event)
		details.batch_event = event.name
		events.append(details)

	return events


@frappe.whitelist()
def get_assessments(batch, member=None):
	if not member:
		member = frappe.session.user

	assessments = frappe.get_all(
		"EventsConnect Assessment",
		{"parent": batch},
		["name", "assessment_type", "assessment_name"],
	)

	for assessment in assessments:
		if assessment.assessment_type == "EventsConnect Assignment":
			assessment = get_assignment_details(assessment, member)

		elif assessment.assessment_type == "EventsConnect Quiz":
			assessment = get_quiz_details(assessment, member)

	return assessments


def get_assignment_details(assessment, member):
	assessment.title = frappe.db.get_value(
		"EventsConnect Assignment", assessment.assessment_name, "title"
	)

	existing_submission = frappe.db.exists(
		{
			"doctype": "EventsConnect Assignment Submission",
			"member": member,
			"assignment": assessment.assessment_name,
		}
	)
	assessment.completed = False
	if existing_submission:
		assessment.submission = frappe.db.get_value(
			"EventsConnect Assignment Submission",
			existing_submission,
			["name", "status", "comments"],
			as_dict=True,
		)
		assessment.completed = True
		assessment.status = assessment.submission.status
	else:
		assessment.status = "Not Attempted"
		assessment.color = "red"

	assessment.edit_url = f"/assignments/{assessment.assessment_name}"
	submission_name = existing_submission if existing_submission else "new-submission"
	assessment.url = (
		f"/assignment-submission/{assessment.assessment_name}/{submission_name}"
	)

	return assessment


def get_quiz_details(assessment, member):
	assessment_details = frappe.db.get_value(
		"EventsConnect Quiz", assessment.assessment_name, ["title", "passing_percentage"], as_dict=1
	)
	assessment.title = assessment_details.title

	existing_submission = frappe.get_all(
		"EventsConnect Quiz Submission",
		{
			"member": member,
			"quiz": assessment.assessment_name,
		},
		["name", "score", "percentage"],
		order_by="percentage desc",
	)

	if len(existing_submission):
		assessment.submission = existing_submission[0]
		assessment.completed = True
		assessment.status = assessment.submission.score
	else:
		assessment.status = "Not Attempted"
		assessment.color = "red"
		assessment.completed = False

	assessment.edit_url = f"/quizzes/{assessment.assessment_name}"
	submission_name = (
		existing_submission[0].name if len(existing_submission) else "new-submission"
	)
	assessment.url = f"/quiz-submission/{assessment.assessment_name}/{submission_name}"

	return assessment


@frappe.whitelist()
def get_batch_students(batch):
	students = []

	students_list = frappe.get_all(
		"Batch Student", filters={"parent": batch}, fields=["student", "name"]
	)

	batch_events = frappe.get_all("Batch Event", {"parent": batch}, pluck="event")

	assessments = frappe.get_all(
		"EventsConnect Assessment",
		filters={"parent": batch},
		fields=["name", "assessment_type", "assessment_name"],
	)

	for student in students_list:
		events_completed = 0
		assessments_completed = 0
		detail = frappe.db.get_value(
			"User",
			student.student,
			["full_name", "email", "username", "last_active", "user_image"],
			as_dict=True,
		)
		detail.last_active = format_datetime(detail.last_active, "dd MMM YY")
		detail.name = student.name
		students.append(detail)

		for event in batch_events:
			progress = frappe.db.get_value(
				"EventsConnect Enrollment", {"event": event, "member": student.student}, "progress"
			)

			if progress == 100:
				events_completed += 1

		detail.events_completed = events_completed

		for assessment in assessments:
			if has_submitted_assessment(
				assessment.assessment_name, assessment.assessment_type, student.student
			):
				assessments_completed += 1

		detail.assessments_completed = assessments_completed

	return students


@frappe.whitelist()
def get_discussion_topics(doctype, docname, single_thread):
	if single_thread:
		filters = {
			"reference_doctype": doctype,
			"reference_docname": docname,
		}
		topic = frappe.db.exists("Discussion Topic", filters)
		if topic:
			return frappe.db.get_value("Discussion Topic", topic, ["name"], as_dict=1)
		else:
			return create_discussion_topic(doctype, docname)
	topics = frappe.get_all(
		"Discussion Topic",
		{
			"reference_doctype": doctype,
			"reference_docname": docname,
		},
		["name", "title", "owner", "creation", "modified"],
		order_by="creation desc",
	)

	for topic in topics:
		topic.user = frappe.db.get_value(
			"User", topic.owner, ["full_name", "user_image"], as_dict=True
		)

	return topics


def create_discussion_topic(doctype, docname):
	doc = frappe.new_doc("Discussion Topic")
	doc.update(
		{
			"title": docname,
			"reference_doctype": doctype,
			"reference_docname": docname,
		}
	)
	doc.insert()
	return doc


@frappe.whitelist()
def get_discussion_replies(topic):
	replies = frappe.get_all(
		"Discussion Reply",
		{
			"topic": topic,
		},
		["name", "owner", "creation", "modified", "reply"],
		order_by="creation",
	)

	for reply in replies:
		reply.user = frappe.db.get_value(
			"User", reply.owner, ["full_name", "user_image"], as_dict=True
		)

	return replies


@frappe.whitelist()
def get_order_summary(doctype, docname, country=None):
	if doctype == "EventsConnect Event":
		details = frappe.db.get_value(
			"EventsConnect Event",
			docname,
			["title", "name", "paid_event", "event_price as amount", "currency", "amount_usd"],
			as_dict=True,
		)

		if not details.paid_event:
			raise frappe.throw(_("This event is free."))

	else:
		details = frappe.db.get_value(
			"EventsConnect Batch",
			docname,
			["title", "name", "paid_batch", "amount", "currency", "amount_usd"],
			as_dict=True,
		)

		if not details.paid_batch:
			raise frappe.throw(_("To join this batch, please contact the Administrator."))

	details.amount, details.currency = check_multicurrency(
		details.amount, details.currency, country, details.amount_usd
	)
	details.original_amount_formatted = fmt_money(details.amount, 0, details.currency)

	if details.currency == "INR":
		details.amount, details.gst_applied = apply_gst(details.amount)
		details.gst_amount_formatted = fmt_money(details.gst_applied, 0, details.currency)

	details.total_amount_formatted = fmt_money(details.amount, 0, details.currency)
	return details


@frappe.whitelist()
def get_lesson_creation_details(event, chapter, lesson):
	chapter_name = frappe.db.get_value(
		"Chapter Reference", {"parent": event, "idx": chapter}, "chapter"
	)
	lesson_name = frappe.db.get_value(
		"Lesson Reference", {"parent": chapter_name, "idx": lesson}, "lesson"
	)

	if lesson_name:
		lesson_details = frappe.db.get_value(
			"Event Lesson",
			lesson_name,
			[
				"name",
				"title",
				"include_in_preview",
				"body",
				"content",
				"instructor_notes",
				"instructor_content",
				"youtube",
				"quiz_id",
			],
			as_dict=1,
		)

	return {
		"event_title": frappe.db.get_value("EventsConnect Event", event, "title"),
		"chapter": frappe.db.get_value(
			"Event Chapter", chapter_name, ["title", "name"], as_dict=True
		),
		"lesson": lesson_details if lesson_name else None,
	}


@frappe.whitelist()
def get_roles(name):
	frappe.only_for("Moderator")
	return {
		"moderator": has_event_moderator_role(name),
		"event_creator": has_event_instructor_role(name),
		"batch_evaluator": has_event_evaluator_role(name),
		"eventsconnect_student": has_student_role(name),
	}


def publish_notifications(doc, method):
	frappe.publish_realtime(
		"publish_eventsconnect_notifications", user=doc.for_user, after_commit=True
	)
@frappe.whitelist(allow_guest=True)
def get_categories(category_filter):
	category_filter = json.loads(category_filter)
	categoryList = []
	categories = frappe.get_all("ECM Category", fields=["category"])
	for category in categories:
		new_category_filter = {
            'category': category.get('category'),
            'checked': True
        }
		categoryList.append(new_category_filter)

	return categoryList