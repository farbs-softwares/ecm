import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import frappeui from 'frappe-ui/vite'
import { webserver_port } from '../../../sites/common_site_config.json'
// https://vitejs.dev/config/
export default defineConfig({
	plugins: [
		frappeui(),
		vue({
			script: {
				defineModel: true,
				propsDestructure: true,
			},
		}),
	],
	server: {
	    port: 8080,
	    proxy: {
	      '^/(app|login|api|assets|files)': {
	        target: `http://127.0.0.1:${webserver_port}`,
	       ws: true,
	        router: function (req) {
	          const site_name = req.headers.host.split(':')[0]
	          return `http://${site_name}:${webserver_port}`
	        },
	      },
	    },
	  },
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src'),
		},
	},
	build: {
		outDir: `../ecm/public/frontend`,
		emptyOutDir: true,
		commonjsOptions: {
			include: [/tailwind.config.js/, /node_modules/],
		},
		sourcemap: true,
		target: 'es2015',
		rollupOptions: {
			output: {
				manualChunks: {
					'frappe-ui': ['frappe-ui'],
				},
			},
		},
	},
	optimizeDeps: {
		include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'],
	},
})
