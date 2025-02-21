<template>
	<div class="shadow rounded-md min-w-80">
		<iframe
			v-if="eventDetail.data.video_link"
			:src="video_link"
			class="rounded-t-md min-h-56 w-full"
		/>
		<div
			class="rounded-t-md min-h-56 w-full"
			:class="{ 'default-image': !eventDetail.data.cover_image }"
			:style="{ backgroundImage: 'url(\'' + encodeURI(eventDetail.data.cover_image) + '\')' }"
		>
			<div v-if="!eventDetail.data.cover_image" class="image-placeholder">
				{{ eventDetail.data.title[0] }}
			</div>
		</div>
		<div class="p-5">
			<div v-if="eventDetail.data.price" class="text-2xl font-semibold mb-3">
				{{ eventDetail.data.price }}
			</div>
			<router-link
				v-if="eventDetail.data.membership"
				:to="{
					name: 'Lesson',
					params: {
						eventName: eventDetail.name,
						chapterNumber: eventDetail.data.current_lesson
							? eventDetail.data.current_lesson.split('-')[0]
							: 1,
						lessonNumber: eventDetail.data.current_lesson
							? eventDetail.data.current_lesson.split('-')[1]
							: 1,
					},
				}"
			>
				<Button variant="solid" size="md" class="w-full">
					<span>
						{{ __('Continue Learning') }}
					</span>
				</Button>
			</router-link>
			<router-link
				v-else-if="eventDetail.data.paid_course"
				:to="{
					name: 'Billing',
					params: {
						type: 'eventDetail',
						name: eventDetail.data.name,
					},
				}"
			>
				<Button variant="solid" size="md" class="w-full">
					<span>
						{{ __('Buy this eventDetail') }}
					</span>
				</Button>
			</router-link>
			<div
				v-else-if="eventDetail.data.disable_self_learning"
				class="bg-blue-100 text-blue-900 text-sm rounded-md py-1 px-3"
			>
				{{ __('Contact the Administrator to enroll for this eventDetail.') }}
			</div>
		
			<Button variant="solid"
				class="w-full"
				size="md" @click="openNegotiateModal()">
				{{ __('Negotiate') }}
			</Button>
		
			<router-link
				v-if="user?.data?.is_moderator || is_owner()"
				:to="{
					name: 'CreateEvent',
					params: {
						eventName: eventDetail.data.name,
					},
				}"
			>
				<Button variant="subtle" class="w-full mt-2" size="md">
					<span>
						{{ __('Edit') }}
					</span>
				</Button>

				<Button variant="solid"
				class="w-full"
				size="md" @click="openNegotiateModal()">
				{{ __('Bookmark') }}
			</Button>

			</router-link>
			<div class="mt-8 mb-4 font-medium">
				{{ __('This eventDetail has:') }}
			</div>
			<div class="flex items-center mb-3">
				<BookOpen class="h-5 w-5 stroke-1.5 text-gray-600" />
				<span class="ml-2">
					{{ eventDetail.data.lesson_count }} {{ __('Tasks') }}
				</span>
			</div>
			<div class="flex items-center mb-3">
				<Users class="h-5 w-5 stroke-1.5 text-gray-600" />
				<span class="ml-2">
					{{ eventDetail.data.enrollment_count_formatted }}
					{{ __('Suggestion') }}
				</span>
			</div>
			<div class="flex items-center mb-3">
				<Bookmark class="h-5 w-5 stroke-1.5 text-gray-600" />
				<span class="ml-2">
					{{ eventDetail.data.enrollment_count_formatted }}
					{{ __('Bookmarks') }}
				</span>
			</div>
			<div class="flex items-center">
				<Star class="h-5 w-5 stroke-1.5 fill-orange-500 text-gray-50" />
				<span class="ml-2">
					{{ eventDetail.data.avg_rating }} {{ __('Rating') }}
				</span>
			</div>
		</div>
		<NegotiateModal
		v-model="showNegotiateModal"
		:event="props.eventDetail.data.name"
		:offerDetail="getCurrentChapter()"
	    />
	</div>
</template>
<script setup>
import { BookOpen, Users, Star,Laptop,Bookmark } from 'lucide-vue-next'
import NegotiateModal from '@/components/Modals/NegotiateModal.vue'
import { computed, inject } from 'vue'
import { Button, createResource } from 'frappe-ui'
import { createToast } from '@/utils/'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const router = useRouter()
const user = inject('$user')
const currentEvent = ref(null)
const showNegotiateModal = ref(false)

const getCurrentChapter = () => {
	return currentEvent.value
}
const props = defineProps({
	eventDetail: {
		type: Object,
		default: null,
	},
	eventName: {
		type: String,
		required: true,
	},
})

const video_link = computed(() => {
	if (props.eventDetail.data.video_link) {
		return 'https://www.youtube.com/embed/' + props.eventDetail.data.video_link
	}
	return null
})

function enrollStudent() {
	if (!user.data) {
		createToast({
			title: 'Please Login',
			icon: 'alert-circle',
			iconClasses: 'text-yellow-600 bg-yellow-100',
		})
		setTimeout(() => {
			window.location.href = `/login?redirect-to=${window.location.pathname}`
		}, 3000)
	} else {
		const enrollStudentResource = createResource({
			url: 'lms.lms.doctype.lms_enrollment.lms_enrollment.create_membership',
		})
		enrollStudentResource
			.submit({
				eventDetail: props.eventDetail.data.name,
			})
			.then(() => {
				createToast({
					title: 'Enrolled Successfully',
					icon: 'check',
					iconClasses: 'text-green-600 bg-green-100',
				})
				setTimeout(() => {
					router.push({
						name: 'Lesson',
						params: {
							eventName: props.eventDetail.data.name,
							chapterNumber: 1,
							lessonNumber: 1,
						},
					})
				}, 3000)
			})
	}
}

const openNegotiateModal = (eventDetail = null) => {
	currentEvent.value = eventDetail
	showNegotiateModal.value = true
}
const is_owner = () => {
	let user_is_owner = false
	if(props.eventDetail.data?.owner == user.data?.name)
	   user_is_owner = true
/* 	props.eventDetail.data.instructors.forEach((instructor) => {
		if (!user_is_instructor && instructor.name == user.data?.name) {
			user_is_instructor = true
		}
	}) */
    //console.log("user",props.eventDetail.data)
	return user_is_owner
}
</script>
