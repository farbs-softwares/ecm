<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Create Task'),
			size: 'lg',
			actions: [
				{
					label: chapterDetail ? __('Edit Task') : __('Create Task'),
					variant: 'solid',
					onClick: (close) =>
						chapterDetail ? editChapter(close) : addChapter(close),
				},
			],
		}"
	>
		<template #body-content> 
			<div class="my-3 leading-6">
				 <!-- {{ event.title }} -->
					</div>
			<FormControl label="Title" v-model="task.title" class="mb-4" type="text" />
			<FormControl label="Description" v-model="task.description" class="mb-4" type = "textarea"/>
		</template>
	</Dialog>
</template>
<script setup>
import { Dialog, FormControl, createResource } from 'frappe-ui'
import { defineModel, reactive, watch, inject } from 'vue'
import { createToast, formatTime } from '@/utils/'

const show = defineModel()
const outline = defineModel('outline')

const props = defineProps({
	event: {
		type: String,
		required: true,
	},
	offerDetail: {
		type: Object,
	},
})
const chapter = reactive({
	title: '',
})
const task = reactive({
	description: '',
	title: ''
})
const chapterResource = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'Event Tasks',
				title: task.title,
				description: task.description,
				parent: props.event, 
				parentfield: 'task_link',
				parenttype: 'ECM Events' 
			},
		}
	},
})

const chapterEditResource = createResource({
	url: 'frappe.client.set_value',
	makeParams(values) {
		return {
			doctype: 'Event Tasks',
			name: props.offerDetail?.name,
			fieldnames: ['title', 'description'],
			values: [task.title, task.description],
		}
	},
})



const addChapter = (close) => {
	chapterResource.submit(
		{},
		{
			validate() {
				if (!task.title) {
					return 'Title is required'
				}
			},
			onSuccess: (data) => {
				
				createToast({
				text: 'Your Task Created successfully',
				icon: 'check',
				iconClasses: 'bg-green-600 text-white rounded-md p-px',
			})
				close()
			},
			onError(err) {
				showError(err)
			},
		}
	)
}

const editChapter = (close) => {
	chapterEditResource.submit(
		{},
		{
			validate() {
				if (!chapter.title) {
					return 'Title is required'
				}
			},
			onSuccess() {
				outline.value.reload()
				createToast({
					text: 'Task updated successfully',
					icon: 'check',
					iconClasses: 'bg-green-600 text-white rounded-md p-px',
				})
				close()
			},
			onError(err) {
				showError(err)
			},
		}
	)
}

const showError = (err) => {
	createToast({
		title: 'Error',
		text: err.messages?.[0] || err,
		icon: 'x',
		iconClasses: 'bg-red-600 text-white rounded-md p-px',
		position: 'top-center',
		timeout: 10,
	})
}

watch(
	() => props.chapterDetail,
	(newChapter) => {
		chapter.title = newChapter?.title
	}
)
</script>
