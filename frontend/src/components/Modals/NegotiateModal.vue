<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Send Offer'),
			size: 'lg',
			actions: [
				{
					label: chapterDetail ? __('Edit Offer') : __('Send Offer'),
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
			<FormControl label="Details" v-model="offer.details" class="mb-4" type="textarea" />
			<FormControl label="Sugessted price" v-model="offer.suggested_price" class="mb-4" />
			<FormControl label="About Me" v-model="offer.about_me" class="mb-4" type = "textarea"/>
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
const offer = reactive({
	details: '',
	suggested_price:0,
	about_me:''
})
const chapterResource = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'Event Offers',
				offer: offer.details,
				about_me: offer.about_me,
				event: props.event,
				suggested_price: offer.suggested_price
			},
		}
	},
})

const chapterEditResource = createResource({
	url: 'frappe.client.set_value',
	makeParams(values) {
		return {
			doctype: 'Event Offers',
			name: props.offerDetail?.name,
			fieldnames: ['offer', 'about_me', 'suggested_price'],
			values: [offer.details, offer.about_me, offer.suggested_price],
		}
	},
})



const addChapter = (close) => {
	chapterResource.submit(
		{},
		{
			validate() {
				if (!offer.details) {
					return 'Details is required'
				}
			},
			onSuccess: (data) => {
				
				createToast({
				text: 'Your Offer sent to event Creater successfully',
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
					text: 'Chapter updated successfully',
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
