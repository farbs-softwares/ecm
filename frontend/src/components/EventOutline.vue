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
				
					<div v-if="allowEdit" class="flex mt-2 mb-4 pl-8">
	
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
		:taskDetail="getCurrentTask()"
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



const openChapterDetail = (index) => {
	return index == route.params.chapterNumber || index == 1
}

const openTaskModal = (task = null) => {
	console.log("task",outline.data.name)
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
