import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'

export const usersStore = defineStore('lms-users', () => {
	let userResource = createResource({
		url: 'ecm.events_connect_management.api.get_user_info',
		onError(error) {
			if (error && error.exc_type === 'AuthenticationError') {
				router.push('/login')
			}
		},
		auto: true,
	})

	const allUsers = createResource({
		url: 'ecm.events_connect_management.api.get_all_users',
		cache: ['allUsers'],
		auto: true,
	})

	return {
		userResource,
		allUsers,
	}
})
