<template>
	<div class="flex justify-between items-center">
		<div class="flex space-x-2 text-xl">
			{{ __('Filter Events') }}
		</div>
		<div class="flex flex-wrap gap-4">
    <div v-for="(category, index) in categories" :key="index" class="flex items-center">
				<Switch
					size="sm"
					:label="category.category"
					:disabled="false"
					v-model="category.checked"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { reactive, ref,watch } from 'vue'
import { Switch,createResource,} from 'frappe-ui'
const props = defineProps({
	categories: {
		type: Array,
		required: true,
	},
})
const state = reactive({
      categories: props.categories.map(category => ({
        ...category,
        checked: category.checked !== undefined ? category.checked : true // Default to true if not defined
      }))
    });

    // Watch for changes in the props to update the internal state
    watch(() => props.categories, (newCategories) => {
      state.categories = newCategories.map(category => ({
        ...category,
        checked: category.checked !== undefined ? category.checked : true
      }));
    });

    // Emit changes to the parent component
    function emitChanges() {
      emit('update:categories', state.categories);
    }
/* const categories = reactive({
	category: '',
	checked: true,
}) */
const categoryResource = createResource({
	url: 'ecm.events_connect_management.utils.get_categories',
	params: {
		category_filter: JSON.stringify(props.categories),
	},
	auto: true,
	onSuccess(data) {
		props.categories.splice(0, props.categories.length, ...data);
	}

})
// Method to filter checked categories
function getCheckedCategories() {
      return categories.filter(category => category.checked);
    }

</script>
