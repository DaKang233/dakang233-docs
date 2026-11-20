import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-CN',
  title: 'Applied Crafted Energistics',
  description: '应用机巧能源：把机械动力：机巧新生的气体接入应用能源 2 的 ME 网络',
  base: '/appliedcraftedenergistics/',
  outDir: '../../docs/appliedcraftedenergistics',
  srcExclude: ['README.md'],
  head: [['meta', { name: 'theme-color', content: '#2f7f8f' }]],
  themeConfig: {
    nav: [
      { text: '开始', link: '/guide/introduction' },
      { text: '玩法', items: [
        { text: '气体存储元件', link: '/guide/cells' },
        { text: 'ME 气体接口', link: '/guide/interface' },
        { text: '气体 P2P 隧道', link: '/guide/p2p' },
        { text: '元件升级卡', link: '/guide/upgrades' },
        { text: '与 AE2 原生设备互通', link: '/guide/interop' },
      ] },
      { text: '参考', items: [
        { text: '气压与容量换算', link: '/guide/pressure' },
        { text: '配置文件', link: '/guide/config' },
        { text: '常见问题', link: '/guide/faq' },
        { text: '许可与声明', link: '/guide/license' },
        { text: '开发者：管网交互', link: '/guide/developer-interop' },
      ] },
    ],
    sidebar: [
      { text: '开始', items: [
        { text: '这是什么', link: '/guide/introduction' },
        { text: '安装与版本', link: '/guide/install' },
      ] },
      { text: '玩法', items: [
        { text: '气体存储元件', link: '/guide/cells' },
        { text: 'ME 气体接口', link: '/guide/interface' },
        { text: '气体 P2P 隧道', link: '/guide/p2p' },
        { text: '元件升级卡', link: '/guide/upgrades' },
        { text: '与 AE2 原生设备互通', link: '/guide/interop' },
      ] },
      { text: '参考', items: [
        { text: '气压与容量换算', link: '/guide/pressure' },
        { text: '配置文件', link: '/guide/config' },
        { text: '常见问题与已知限制', link: '/guide/faq' },
        { text: '许可与第三方声明', link: '/guide/license' },
        { text: '开发者：管网交互', link: '/guide/developer-interop' },
      ] },
    ],
    socialLinks: [{ icon: 'github', link: 'https://github.com/DaKang233/AppliedCraftedEnergistics' }],
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
