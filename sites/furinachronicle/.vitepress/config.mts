import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-CN',
  title: 'FurinaChronicle',
  description: 'Windows 与 Android 上的原神个人历史档案使用文档',
  base: '/furinachronicle/',
  outDir: '../../docs/furinachronicle',
  srcExclude: ['README.md'],
  head: [['meta', { name: 'theme-color', content: '#385bb8' }]],
  themeConfig: {
    nav: [
      { text: '使用指南', link: '/guide/install' },
      { text: '法律与隐私', items: [
        { text: '使用协议', link: '/terms/' },
        { text: '隐私政策', link: '/privacy/' },
      ] },
    ],
    sidebar: [
      { text: '使用指南', items: [
        { text: '安装与升级', link: '/guide/install' },
        { text: '游戏历程与挑战', link: '/guide/history' },
        { text: '抽卡记录', link: '/guide/gacha' },
        { text: '备份与迁移', link: '/guide/archive' },
      ] },
      { text: '法律与隐私', items: [
        { text: '使用协议', link: '/terms/' },
        { text: '隐私政策', link: '/privacy/' },
      ] },
    ],
    socialLinks: [{ icon: 'github', link: 'https://github.com/DaKang233/FurinaChronicle' }],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档', buttonAriaLabel: '搜索文档' },
          modal: {
            displayDetails: '显示详细列表',
            resetButtonTitle: '清除搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '无匹配结果',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
          },
        },
      },
    },
    outline: { label: '本页目录' },
    sidebarMenuLabel: '文档目录',
    returnToTopLabel: '返回顶部',
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    docFooter: { prev: '上一页', next: '下一页' },
    footer: { message: '<a href="/">返回大康233文档首页</a>' },
  },
})
