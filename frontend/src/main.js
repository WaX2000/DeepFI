import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 导入根组件
import App from './App.vue'

// 创建Vue应用实例
const app = createApp(App)

// 全局注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用Element Plus插件
app.use(ElementPlus)

// 将应用挂载到HTML中的 #app 元素上
app.mount('#app')
