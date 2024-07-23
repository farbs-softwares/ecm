<template>
	<div v-if="event.data">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>
		<div class="m-5">
			<div class="flex justify-between w-full">
				<div class="md:w-2/3">
		
					<div class="text-3xl font-semibold">
						{{ event.data.title }}
					</div>
					<div class="my-3 leading-6">
						{{ event.data.about_event }}
					</div>
					<div class="flex items-center">
						<!-- <Tooltip
							v-if="event.data.avg_rating"
							:text="__('Average Rating')"
							class="flex items-center"
						>
							<Star class="h-5 w-5 text-gray-100 fill-orange-500" />
							<span class="ml-1">
								{{ course.data.avg_rating }}
							</span>
						</Tooltip> -->
						<!-- <span v-if="course.data.avg_rating" class="mx-3">&middot;</span> -->
						<!-- <Tooltip
							v-if="course.data.enrollment_count"
							:text="__('Enrolled Students')"
							class="flex items-center"
						>
							<Users class="h-4 w-4 text-gray-700" />
							<span class="ml-1">
								{{ course.data.enrollment_count_formatted }}
							</span>
						</Tooltip>
						<span v-if="course.data.enrollment_count" class="mx-3"
							>&middot;</span
						> -->
						<!-- <div class="flex items-center">
							<span
								class="h-6 mr-1"
								:class="{
									'avatar-group overlap': course.data.instructors.length > 1,
								}"
							>
								<UserAvatar
									v-for="instructor in course.data.instructors"
									:user="instructor"
								/>
							</span>
							<CourseInstructors :instructors="course.data.instructors" />
						</div> -->
					</div>
					<div class="flex mt-3 mb-4 w-fit">
					<!-- 	<Badge
							theme="gray"
							size="lg"
							class="mr-2"
							v-for="tag in course.data.tags"
						>
							{{ tag }}
						</Badge> -->
					</div>
					<!-- <CourseCardOverlay :course="course" class="md:hidden mb-4" /> -->
					<div
						v-html="event.data.full_description"
						class="course-description"
					></div>
					<div class="mt-10">
						 <EventOutline :eventName="event.data.name" :showOutline="true" /> 
					</div>
					<!-- <CourseReviews
						:eventName="course.data.title"
						:avg_rating="course.data.avg_rating"
						:membership="course.data.membership"
					/> -->
				</div>
				<div class="hidden md:block">
				 	<EventCardOverlay :event="event" />
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import { createResource, Breadcrumbs, Badge, Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { Users, Star } from 'lucide-vue-next'
import EventCardOverlay from '@/components/EventCardOverlay.vue'
import EventOutline from '@/components/EventOutline.vue'
import CourseReviews from '@/components/CourseReviews.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { updateDocumentTitle } from '@/utils'
import CourseInstructors from '@/components/CourseInstructors.vue'



const props = defineProps({
	eventName: {
		type: String,
		required: true,
	},
})

const event = createResource({
	url: 'ecm.events_connect_management.utils.get_event_details',
	cache: ['event', props.eventName],
	params: {
		event: props.eventName,
	},
	auto: true,
})

const breadcrumbs = computed(() => {
	let items = [{ label: 'All Events', route: { name: 'Events' } }]
	items.push({
		label: event?.data?.title,
		route: { name: 'EventDetail', params: { event: event?.data?.name } },
	})
	return items
})

const pageMeta = computed(() => {
	return {
		title: event?.data?.title,
		description: event?.data?.about_event,
	}
})

updateDocumentTitle(pageMeta)
</script>
<style>
.course-description p {
	margin-bottom: 1rem;
	line-height: 1.7;
}
.course-description li {
	line-height: 1.7;
}

.course-description ol {
	list-style: auto;
	margin: revert;
	padding: revert;
}

.course-description ul {
	list-style: disc;
	margin: revert;
	padding: revert;
}

.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
}
</style>
