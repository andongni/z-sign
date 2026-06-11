import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'

import App from './App.vue'
import './style.css'

createApp(App).use(ElementPlus, { locale: zhCn }).mount('#app')
