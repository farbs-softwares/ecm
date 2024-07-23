<template>
	<div class="text-base">
		<div
			v-if="title && (outline.data?.length || allowEdit)"
			class="grid grid-cols-[70%,30%] mb-4 px-2"
		>
			<div class="font-semibold text-lg">
				{{ __(title) }}
			</div>
			<Button size="sm" v-if="allowEdit" @click="openTaskModal()">
				{{ __('Add Task') }}
			</Button>
			 <span class="font-medium cursor-pointer" @click="expandAllTasks()">
				{{ expandAll ? __("Collapse all tasks") : __("Expand all tasks") }}
			</span> 
		</div>
		<div
			:class="{
				'shadow rounded-md pt-2 px-2': showOutline && outline.data?.length,
			}"
		>
			<Disclosure
				v-slot="{ open }"
				v-for="(task, index) in outline.data"
				:key="task.name"
				:defaultOpen="openChapterDetail(task.idx)"
			>
				<DisclosureButton ref="" class="flex w-full p-2">
					<ChevronRight
						:class="{
							'rotate-90 transform duration-200': open,
							'duration-200': !open,
							open: index == 1,
						}"
						class="h-4 w-4 text-gray-900 stroke-1 mr-2"
					/>
					<div class="text-base text-left font-medium leading-5">
						{{ task.title }}
					</div>
				</DisclosureButton>
				<DisclosurePanel>
					<Draggable
						:list="task.lessons"
						item-key="name"
						group="items"
						@end="updateOutline"
						:data-task="task.name"
					>
						<template #item="{ element: lesson }">
							<div class="outline-lesson pl-8 py-2 pr-4">
								<router-link
									:to="{
										name: allowEdit ? 'CreateLesson' : 'Lesson',
										params: {
											eventName: eventName,
											/* chapterNumber: lesson.number.split('.')[0],
											lessonNumber: lesson.number.split('.')[1], */
										},
									}"
								>
									<div class="flex items-center text-sm leading-5 group">
										<MonitorPlay
											v-if="lesson.icon === 'icon-youtube'"
											class="h-4 w-4 text-gray-900 stroke-1 mr-2"
										/>
										<HelpCircle
											v-else-if="lesson.icon === 'icon-quiz'"
											class="h-4 w-4 text-gray-900 stroke-1 mr-2"
										/>
										<FileText
											v-else-if="lesson.icon === 'icon-list'"
											class="h-4 w-4 text-gray-900 stroke-1 mr-2"
										/>
										{{ lesson.title }}
										<Trash2
											v-if="allowEdit"
											@click.prevent="trashLesson(lesson.name, task.name)"
											class="h-4 w-4 stroke-1.5 text-gray-700 ml-auto invisible group-hover:visible"
										/>
										<Check
											v-if="lesson.is_complete"
											class="h-4 w-4 text-green-700 ml-2"
										/>
									</div>
								</router-link>
							</div>
						</template>
					</Draggable>
					<div v-if="allowEdit" class="flex mt-2 mb-4 pl-8">
						<!-- <router-link
							:to="{
								name: 'CreateLesson',
								params: {
									eventName: eventName,
									chapterNumber: task.idx,
									lessonNumber: task.lessons.length + 1,
								},
							}"
						> 
							<Button>
								{{ __('Add Lesson') }}
							</Button>
						</router-link>-->
						<Button class="ml-2" @click="openTaskModal(task)">
							{{ __('Edit Task') }}
						</Button>
					</div>
				</DisclosurePanel>
			</Disclosure>
		</div>
	</div>
	<TaskModal
		v-model="showTaskModal"
		v-model:outline="outline"
		:event="eventName"
		:chapterDetail="getCurrentTask()"
	/>
</template>
<script setup>
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import Draggable from 'vuedraggable'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue'
import {
	ChevronRight,
	MonitorPlay,
	HelpCircle,
	FileText,
	Check,
	Trash2,
} from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import TaskModal from '@/components/Modals/TaskModal.vue'
import { showToast } from '@/utils'

const route = useRoute()
const expandAll = ref(true)
const showTaskModal = ref(false)
const currentTask = ref(null)

const props = defineProps({
	eventName: {
		type: String,
		required: true,
	},
	showOutline: {
		type: Boolean,
		default: false,
	},
	title: {
		type: String,
		default: '',
	},
	allowEdit: {
		type: Boolean,
		default: false,
	},
	getProgress: {
		type: Boolean,
		default: false,
	},
})

const outline = createResource({
	url: 'ecm.events_connect_management.utils.get_event_task',
	cache: ['event_outline', props.eventName],
	params: {
		event: props.eventName,
		
	},
	auto: true,
})

const deleteLesson = createResource({
	url: 'ecm.events_connect_management.api.delete_lesson',
	makeParams(values) {
		return {
			lesson: values.lesson,
			task: values.task,
		}
	},
	onSuccess() {
		outline.reload()
		showToast('Success', 'Lesson deleted successfully', 'check')
	},
})

const updateLessonIndex = createResource({
	url: 'ecm.events_connect_management.api.update_lesson_index',
	makeParams(values) {
		return {
			lesson: values.lesson,
			sourceChapter: values.sourceChapter,
			targetChapter: values.targetChapter,
			idx: values.idx,
		}
	},
	onSuccess() {
		showToast('Success', 'Lesson moved successfully', 'check')
	},
})

const trashLesson = (lessonName, chapterName) => {
	deleteLesson.submit({
		lesson: lessonName,
		task: chapterName,
	})
}

const openChapterDetail = (index) => {
	return index == route.params.chapterNumber || index == 1
}

const openTaskModal = (task = null) => {
	currentTask.value = task
	showTaskModal.value = true
}

const getCurrentTask = () => {
	return currentTask.value
}

const updateOutline = (e) => {
	updateLessonIndex.submit({
		lesson: e.item.__draggable_context.element.name,
		sourceChapter: e.from.dataset.task,
		targetChapter: e.to.dataset.task,
		idx: e.newIndex,
	})
}
</script>
<style>
.outline-lesson:has(.router-link-active) {
	background-color: theme('colors.gray.100');
}
</style>
