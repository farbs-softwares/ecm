<template>
	<div class="">
		<div class="grid md:grid-cols-[70%,30%] h-full">
			<div>
				<header
					class="sticky top-0 z-10 flex flex-col md:flex-row md:items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
				>
					<Breadcrumbs class="h-7" :items="breadcrumbs" />
					<div class="flex items-center mt-3 md:mt-0">
						<Button variant="solid" @click="submitEvent()" class="ml-2">
							<span>
								{{ __('Save') }}
							</span>
						</Button>
					</div>
				</header>
				<div class="mt-5 mb-10">
					<div class="container mb-5">
						<div class="text-lg font-semibold mb-4">
							{{ __('Details') }}
						</div>
						<FormControl
							v-model="event.title"
							:label="__('Title')"
							class="mb-4"
						/>
						<FormControl
							v-model="event.about_event"
							:label="__(' About Event')"
							class="mb-4"
						/>
						<div class="mb-4">
							<div class="mb-1.5 text-sm text-gray-700">
								{{ __('Event Description') }}
							</div>
							<TextEditor
								:content="event.full_description"
								@change="(val) => (event.full_description = val)"
								:editable="true"
								:fixedMenu="true"
								editorClass="prose-sm max-w-none border-b border-x bg-gray-100 rounded-b-md py-1 px-2 min-h-[7rem]"
							/>
						</div>
						<div class="mb-1.5 text-sm text-gray-700">
								{{ __('Event Cover image') }}
							</div>
						<FileUploader
							v-if="!event.event_image"
							:fileTypes="['image/*']"
							:validateFile="validateFile"
							@success="(file) => saveImage(file)"
						>
							<template
								v-slot="{ file, progress, uploading, openFileSelector }"
							>
								<div class="mb-4">
									<Button @click="openFileSelector" :loading="uploading">
										{{
											uploading ? `Uploading ${progress}%` : 'Upload an image'
										}}
									</Button>
								</div>
							</template>
						</FileUploader>
						<div v-else class="mb-4">
							<div class="text-xs text-gray-600 mb-1">
								{{ __('Event Cover image') }}
							</div>
							<div class="flex items-center">
								<div class="border rounded-md p-2 mr-2">
									<FileText class="h-5 w-5 stroke-1.5 text-gray-700" />
								</div>
								<div class="flex flex-col">
									<span>
										{{ event.event_image.file_name }}
									</span>
									<span class="text-sm text-gray-500 mt-1">
										{{ getFileSize(event.event_image.file_size) }}
									</span>
								</div>
								<X
									@click="removeImage()"
									class="bg-gray-200 rounded-md cursor-pointer stroke-1.5 w-5 h-5 p-1 ml-4"
								/>
							</div>
						</div>
					
						<div class="mb-4">
								<div class="text-lg font-semibold mb-4">
									{{ __('Date and Time & Location') }}
								</div>
							<div class="grid grid-cols-2 gap-10">
								
								<FormControl
								v-model="event.start_date"
								:label="__('Start Date')"
								type="date"
								class="mb-4"
								/>
								<FormControl
								v-model="event.start_time"
								:label="__('Start Time')"
								type="time"
								class="mb-4"
								/>
								<FormControl
									v-model="event.finish_date"
									:label="__('End Date')"
									type="date"
									class="mb-4"
								/>
								
								<FormControl
									v-model="event.finish_time"
									:label="__('End Time')"
									type="time"
									class="mb-4"
								/>
								
								<FormControl
									v-model="event.location"
									:label="__(' Event Location')"
									class="mb-4"
								/>
							</div>
						</div>
						<div class="mb-4">
								<div class="text-lg font-semibold mb-4">
									{{ __('Price') }}
								</div>
							<div class="grid grid-cols-2 gap-10">

								<FormControl
									v-model="event.suggested_cost"
									:label="__(' Cost')"
									class="mb-4"
								/>
								<FormControl
									v-model="event.is_price_negotiable"
									:label="__(' Is price negotiable')"
									type="select"
									:options="eventGetSelectPriceOptions.data.is_price_negotiable"
									class="mb-4"
								/>
							</div>
						</div>
						<div class="mb-4">
								<div class="text-lg font-semibold mb-4">
									{{ __('More details') }}
								</div>
							<div class="grid grid-cols-2 gap-10">

								<FormControl
									v-model="event.number_of_participate"
									:label="__(' Number of Participate')"
									class="mb-4"
								/>
								<FormControl
									v-model="event.group"
									:label="__('Group?')"
									type="select"
									:options="eventGetSelectGroupOptions.data.group"
									class="mb-4"
								/>
								<FormControl
									v-model="event.control_level"
									:label="__('Control Level')"
									type="select"
									:options="eventGetSelectControlLevelOptions.data.control_level"
									class="mb-4"
								/>
							</div>
						</div>
						<div class="mb-4">
								<div class="text-lg font-semibold mb-4">
									{{ __('Settings') }}
								</div>
							<div class="grid grid-cols-2 gap-10">
								<div class="flex items-center">
									<Link
									doctype="ECM Status"
									v-model="event.status"
									:label="__('Status')"
									/>
								</div>
								<div class="flex items-center">
									<Link
									doctype="ECM Category"
									v-model="event.category"
									:label="__('Category')"
									/>
								</div>
							</div>
						</div>
					</div>
					
					
				</div>
			</div>
			<div class="border-l pt-5">
				<EventOutline
					v-if="eventResource.data"
					:eventName="eventResource.data.name"
					:title="event.title"
					:allowEdit="true"
				/>
			</div>
		</div>
	</div>
</template>
<script setup>
import {
	Breadcrumbs,
	TextEditor,
	Button,
	createResource,
	FormControl,
	FileUploader,
} from 'frappe-ui'
import {
	inject,
	onMounted,
	onBeforeUnmount,
	computed,
	ref,
	reactive,
	watch,
} from 'vue'
import {
	convertToTitleCase,
	showToast,
	getFileSize,
	updateDocumentTitle,
} from '../utils'
import Link from '@/components/Controls/Link.vue'
import { FileText, X } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import EventOutline from '@/components/EventOutline.vue'


const user = inject('$user')
const newTag = ref('')
const router = useRouter()
const instructors = ref([])


const props = defineProps({
	eventName: {
		type: String,
	},
})

const event = reactive({
	title: '',
	about_event: '',
	full_description: '',
	start_time: '',
	finish_time: '',
	start_date: '',
	finish_date: '',
	event_image: '',
	category: '',
	number_of_participate:'',
	location: '',
	status:'',
	number_of_participate:0,
	group:false,
	control_level:'',
	suggested_cost:0,
	is_price_negotiable:false,
	published: false,

})

onMounted(() => {
	if (
		props.eventName == 'new' &&
		!user.data?.is_moderator &&
		!user.data?.is_instructor
	) {
		router.push({ name: 'Event' })
	}

	if (props.eventName !== 'new') {
		eventResource.reload()
	}

	window.addEventListener('keydown', keyboardShortcut)
})

const keyboardShortcut = (e) => {
	if (
		e.key === 's' &&
		(e.ctrlKey || e.metaKey) &&
		!e.target.classList.contains('ProseMirror')
	) {
		submitEvent()
		e.preventDefault()
	}
}

onBeforeUnmount(() => {
	window.removeEventListener('keydown', keyboardShortcut)
})

const eventCreationResource = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'ECM Events',
				cover_image: event.event_image?.file_url || '',
				...values,
			},
		}
	},
})

//


const courseEditResource = createResource({
	url: 'frappe.client.set_value',
	auto: false,
	makeParams(values) {
		return {
			doctype: 'ECM Events',
			name: values.event,
			fieldname: {
				cover_image: event.event_image?.file_url || '',
				/* instructors: instructors.value.map((instructor) => ({
					instructor: instructor,
				})), */
				...event,
			},
		}
	},
})

const eventResource = createResource({
	url: 'frappe.client.get',
	makeParams(values) {
		return {
			doctype: 'ECM Events',
			name: props.eventName,
		}
	},
	auto: false,
	onSuccess(data) {
		Object.keys(data).forEach((key) => {
			if (key == 'instructors') {
				instructors.value = []
				data.instructors.forEach((instructor) => {
					instructors.value.push(instructor.instructor)
				})
			} else if (Object.hasOwn(event, key)) event[key] = data[key]
		})
/* 		let checkboxes = [
			'published',
			'upcoming',
			'disable_self_learning',
			'paid_course',
			'featured',
		]
		for (let idx in checkboxes) {
			let key = checkboxes[idx]
			event[key] = event[key] ? true : false
		} */

		if (data.cover_image) imageResource.reload({ image: data.cover_image })
		check_permission()
	},
})

const imageResource = createResource({
	url: 'ecm.events_connect_management.api.get_file_info',
	makeParams(values) {
		return {
			file_url: values.image,
		}
	},
	auto: false,
	onSuccess(data) {
		event.event_image = data
	},
})

const submitEvent = () => {
	
	if (eventResource.data) {
		courseEditResource.submit(
			{
				event: eventResource.data.name,
			},
			{
				onSuccess() {
					showToast('Success', 'Event updated successfully', 'check')
				},
				onError(err) {
					showToast('Error', err.messages?.[0] || err, 'x')
				},
			}
		)
	} else {
		eventCreationResource.submit(event, {
			onSuccess(data) {
				showToast('Success', 'Event created successfully', 'check')
				router.push({
					name: 'CreateEvent',
					params: { eventName: data.name },
				})
			},
			onError(err) {
				showToast('Error', err.messages?.[0] || err, 'x')
			},
		})
	}
}

const validateMandatoryFields = () => {
	const mandatory_fields = [
		'title',
		'about_event',
	]
	for (const field of mandatory_fields) {
		if (!event[field]) {
			let fieldLabel = convertToTitleCase(field.split('_').join(' '))
			return `${fieldLabel} is mandatory`
		}
	}
	/* if (event.paid_course && (!event.course_price || !event.currency)) {
		return 'Course price and currency are mandatory for paid courses'
	} */
}

watch(
	() => props.eventName !== 'new',
	(newVal) => {
		if (newVal) {
			eventResource.reload()
		}
	}
)

const validateFile = (file) => {
	let extension = file.name.split('.').pop().toLowerCase()
	if (!['jpg', 'jpeg', 'png', 'webp'].includes(extension)) {
		return 'Only image file is allowed.'
	}
}

/* const updateTags = () => {
	if (newTag.value) {
		event.tags = event.tags ? `${event.tags}, ${newTag.value}` : newTag.value
		newTag.value = ''
	}
} */

/* const removeTag = (tag) => {
	event.tags = event.tags
		?.split(', ')
		.filter((t) => t !== tag)
		.join(', ')
	newTag.value = ''
} */

const saveImage = (file) => {
	event.event_image = file
}

const removeImage = () => {
	event.event_image = null
}

const check_permission = () => {
	let user_is_instructor = false
	if (user.data?.is_moderator) return

	instructors.value.forEach((instructor) => {
		if (!user_is_instructor && instructor == user.data?.name) {
			user_is_instructor = true
		}
	})

	if (!user_is_instructor) {
		router.push({ name: 'Events' })
	}
}

const breadcrumbs = computed(() => {
	let crumbs = [
		{
			label: 'Events',
			route: { name: 'Events' },
		},
	]
	if (eventResource.data) {
		crumbs.push({
			label: event.title,
			route: { name: 'EventDetail', params: { eventName: props.eventName } },
		})
	}
	crumbs.push({
		label: props.eventName == 'new' ? 'New Events' : 'Edit Events',
		route: { name: 'CreateEvent', params: { eventName: props.eventName } },
	})
	return crumbs
})

const pageMeta = computed(() => {
	return {
		title: 'Create an Event',
		description: 'Create or edit an event.',
	}
})
const eventGetSelectGroupOptions = createResource({
	url: 'ecm.events_connect_management.utils.get_event_group_options',
	
	auto: true,

})
const eventGetSelectPriceOptions = createResource({
	url: 'ecm.events_connect_management.utils.get_event_pricenegotiate_options',
	
	auto: true,

})
const eventGetSelectControlLevelOptions = createResource({
	url: 'ecm.events_connect_management.utils.get_event_control_level_options',
	
	auto: true,

})

updateDocumentTitle(pageMeta)

</script>
