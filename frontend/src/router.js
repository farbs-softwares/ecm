import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from './stores/user'
import { sessionStore } from './stores/session'

let defaultRoute = '/events'
const routes = [
	{
		path: '/',
		redirect: {
			name: 'Events',
		},
	},
	{
		path: '/events',
		name: 'Events',
		component: () => import('@/pages/Events.vue'),
	},
	 {
		path: '/events/:eventName',
		name: 'EventDetail',
		component: () => import('@/pages/EventDetail.vue'),
		props: true,
	},
	/*{
		path: '/courses/:eventName/learn/:chapterNumber-:lessonNumber',
		name: 'Lesson',
		component: () => import('@/pages/Lesson.vue'),
		props: true,
	},
	{
		path: '/batches',
		name: 'Batches',
		component: () => import('@/pages/Batches.vue'),
	},
	{
		path: '/batches/details/:batchName',
		name: 'BatchDetail',
		component: () => import('@/pages/BatchDetail.vue'),
		props: true,
	},
	{
		path: '/batches/:batchName',
		name: 'Batch',
		component: () => import('@/pages/Batch.vue'),
		props: true,
	},
	{
		path: '/billing/:type/:name',
		name: 'Billing',
		component: () => import('@/pages/Billing.vue'),
		props: true,
	},
	{
		path: '/statistics',
		name: 'Statistics',
		component: () => import('@/pages/Statistics.vue'),
	}, */
	/* {
		path: '/user/:username',
		name: 'Profile',
		component: () => import('@/pages/Profile.vue'),
		props: true,
		redirect: { name: 'ProfileAbout' },
		children: [
			{
				name: 'ProfileAbout',
				path: '',
				component: () => import('@/pages/ProfileAbout.vue'),
			},
			{
				name: 'ProfileCertificates',
				path: 'certificates',
				component: () => import('@/pages/ProfileCertificates.vue'),
			},
			{
				name: 'ProfileRoles',
				path: 'roles',
				component: () => import('@/pages/ProfileRoles.vue'),
			},
			{
				name: 'ProfileEvaluator',
				path: 'evaluations',
				component: () => import('@/pages/ProfileEvaluator.vue'),
			},
		],
	}, */
	/* {
		path: '/job-openings',
		name: 'Jobs',
		component: () => import('@/pages/Jobs.vue'),
	},
	{
		path: '/job-openings/:job',
		name: 'JobDetail',
		component: () => import('@/pages/JobDetail.vue'),
		props: true,
	}, */
	{
		path: '/events/:eventName/edit',
		name: 'CreateEvent',
		component: () => import('@/pages/CreateEvent.vue'),
		props: true,
	},
	/* {
		path: '/courses/:eventName/learn/:chapterNumber-:lessonNumber/edit',
		name: 'CreateLesson',
		component: () => import('@/pages/CreateLesson.vue'),
		props: true,
	},
	{
		path: '/batches/:batchName/edit',
		name: 'BatchCreation',
		component: () => import('@/pages/BatchCreation.vue'),
		props: true,
	},
	{
		path: '/job-opening/:jobName/edit',
		name: 'JobCreation',
		component: () => import('@/pages/JobCreation.vue'),
		props: true,
	},
	{
		path: '/assignment-submission/:assignmentName/:submissionName',
		name: 'AssignmentSubmission',
		component: () => import('@/pages/AssignmentSubmission.vue'),
		props: true,
	},
	{
		path: '/certified-participants',
		name: 'CertifiedParticipants',
		component: () => import('@/pages/CertifiedParticipants.vue'),
	},
	{
		path: '/notifications',
		name: 'Notifications',
		component: () => import('@/pages/Notifications.vue'),
	},
	{
		path: '/badges/:badgeName/:email',
		name: 'Badge',
		component: () => import('@/pages/Badge.vue'),
		props: true,
	}, */
]

let router = createRouter({
	history: createWebHistory('/ecm'),
	routes,
})

router.beforeEach(async (to, from, next) => {
	const { userResource, allUsers } = usersStore()
	let { isLoggedIn } = sessionStore()

	try {
		if (isLoggedIn) {
			await userResource.promise
		}
		if (
			isLoggedIn &&
			(to.name == 'Lesson' ||
				to.name == 'Batch' ||
				to.name == 'Notifications' ||
				to.name == 'Badge')
		) {
			await allUsers.promise
		}
	} catch (error) {
		isLoggedIn = false
	}
	return next()
})

export default router
