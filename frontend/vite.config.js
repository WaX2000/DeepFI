import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173, // 前端开发服务器端口
    host: '0.0.0.0', // 允许外部访问
    proxy: { // 配置代理，解决跨域问题（如果你的后端运行在5000端口）
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
