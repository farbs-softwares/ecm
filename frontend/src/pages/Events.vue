<template>
	<div v-if="events.data">
		<header
	class="sticky top-0 z-10 flex flex-col border-b bg-white px-3 py-2.5 sm:px-5"
>
	<div class="flex justify-between items-center mb-2">
		<div>
			<Breadcrumbs
				class="h-7"
				:items="[{ label: __('All Events'), route: { name: 'Events' } }]"
			/>
		</div>
		<div class="flex space-x-2">
			<FormControl
				type="text"
				placeholder="Search Event"
				v-model="searchQuery"
				@input="events.reload()"
			>
				<template #prefix>
					<Search class="w-4 stroke-1.5 text-gray-600" name="search" />
				</template>
			</FormControl>
			<router-link
				:to="{
					name: 'CreateEvent',
					params: {
						eventName: 'new',
					},
				}"
			>
				<Button v-if="user.data?.is_moderator" variant="solid">
					<template #prefix>
						<Plus class="h-4 w-4" />
					</template>
					{{ __('New Event') }}
				</Button>
			</router-link>
		</div>
	</div>
	<CategoryFilter theme="gray" :categories="filter_categories" @update:categories="handleCategoryUpdate"></CategoryFilter>
	<div class="flex justify-between items-center">
		<div class="flex space-x-2"></div>
	<div class="flex items-center"><MultiSelect 
	  v-model="filter_countries" 
	  doctype = "Country"
	  :label="__('Country')"
	/></div>
	<div class="flex flex-wrap gap-4"><Button  variant="solid" @click="logCategories()">
					<template #prefix>
						<Plus class="h-4 w-4" />
					</template>
					{{ __('Apply filter') }}
				</Button></div>
			</div>
	
</header>

		
		<div class="">
			<Tabs
				v-model="tabIndex"
				tablistClass="overflow-x-visible flex-wrap !gap-3 md:flex-nowrap"
				:tabs="makeTabs"
			>
				<template #tab="{ tab, selected }">
					<div>
						<button
							class="group -mb-px flex items-center gap-2 overflow-hidden border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
							:class="{ 'text-gray-900': selected }"
						>
							<component v-if="tab.icon" :is="tab.icon" class="h-5" />
							{{ __(tab.label) }}
							<Badge theme="gray">
								{{ tab.count }}
							</Badge>
						</button>
					</div>
				</template>
				<template #default="{ tab }">
					<div
						v-if="tab.events /*&& tab.events.value.length*/"
						class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 my-5 mx-5"
					>
						<router-link
							v-for="eventv in tab.events.value"
							:to="
								{          
											name: 'EventDetail',
											params: { eventName: eventv.name },
									  }
							"
						>
							<EventCard :eventv="eventv" />
						</router-link>
					</div>
					<div
						v-else
						class="grid flex-1 place-items-center text-xl font-medium text-gray-500"
					>
						<div class="flex flex-col items-center justify-center mt-4">
							<div>
								{{ __('No {0} Events found').format(tab.label.toLowerCase()) }}
							</div>
						</div>
					</div>
				</template>
			</Tabs>
		</div>
	</div>
</template>

<script setup>
import {
	Breadcrumbs,
	Tabs,
	Badge,
	Button,
	FormControl,
	createResource,
} from 'frappe-ui'
import EventCard from '@/components/EventCard.vue'
import { Plus, Search } from 'lucide-vue-next'
import { ref, computed, inject } from 'vue'
import { updateDocumentTitle } from '@/utils'
import CategoryFilter from '../components/CategoryFilter.vue'
import MultiSelect from '../components/Controls/MultiSelect.vue'


const user = inject('$user')
const searchQuery = ref('')
const filter_categories = ref([])
const filter_countries = ref([])

const events = createResource({
	url: 'ecm.events_connect_management.utils.get_events',
	cache: ['events', user.data?.email],
	auto: true,
})
const tabIndex = ref(0)
let tabs

const makeTabs = computed(() => {
	tabs = []
	addToTabs('Featured', getEvents('featured'))
	addToTabs('New', getEvents('new'))
	addToTabs('Upcoming', getEvents('upcoming'))

	if (user.data) {
		addToTabs('Enrolled', getEvents('enrolled'))

		if (
			user.data.is_moderator ||
			user.data.is_instructor ||
			events.data?.created?.length
		) {
			addToTabs('Created', getEvents('created'))
		}

		if (user.data.is_moderator) {
			addToTabs('Under Review', getEvents('under_review'))
		}
	}
	return tabs
})

const addToTabs = (label, events) => {
	tabs.push({
		label,
		events: computed(() => events),
		count: computed(() => events?.length),
	})
}
    // Handle the updated categories
    function handleCategoryUpdate(updatedCategories) {
		filter_categories.value = updatedCategories;
    }
/* const getCourses = (type) => {
	if (searchQuery.value) {
		return events.data[type].filter((course) =>
			course.title.toLowerCase().includes(searchQuery.value.toLowerCase())
		)
	}
	return events.data[type]
} */
    // For debugging purposes
    function logCategories() {
		events.reload()
    }

const getEvents = (type) => {
    return events.data[type].filter((eventv) => {
        // Filter by search query if it exists
        const matchesSearchQuery = !searchQuery.value || eventv.title.toLowerCase().includes(searchQuery.value.toLowerCase());

        // Get the list of selected categories
        const selectedCategories = filter_categories.value.filter(category => category.checked).map(category => category.category);

        // Filter by category if there are selected categories
        const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(eventv.category) 
		&& (filter_countries.value.length === 0 || filter_countries.value.includes(eventv.country));
		console.log("filter",filter_countries.value)
        // Only include events that match both filters
        return matchesSearchQuery && matchesCategory;
    });
}
const pageMeta = computed(() => {
	return {
		title: 'Events',
		description: 'All Events divided by categories',
	}
})

updateDocumentTitle(pageMeta)
</script>
