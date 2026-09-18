// utils/share.js - 增强版
 
/**
 * 在页面中动态设置分享内容的方式：
 * 
 * 方式一：在页面 onLoad 中设置
 * this._shareConfig = {
 *     title: '动态标题',
 *     path: '/pages/index/index',
 *     imageUrl: '/static/share.png'
 * }
 * 
 * 方式二：通过页面 data 返回
 * data() {
 *     return {
 *         _shareConfig: {
 *             title: '标题',
 *             path: '/pages/index/index'
 *         }
 *     }
 * }
 */
 
export default {
    // 发送给朋友
    onShareAppMessage() {
        // 获取当前页面实例
        const pages = getCurrentPages()
        const currentPage = pages[pages.length - 1]
        
        // 优先级：页面直接定义 > 页面 _shareConfig > 全局默认
        if (currentPage?.onShareAppMessage && currentPage.onShareAppMessage !== this.onShareAppMessage) {
            // 如果页面自己定义了 onShareAppMessage，直接调用
            return currentPage.onShareAppMessage.call(currentPage)
        }
        
        // 从页面数据中获取自定义配置
        const shareConfig = currentPage?.data?._shareConfig || {}
        const route = currentPage?.route || 'pages/index/index'
        
        return {
            title: shareConfig.title || '默认分享标题',
            path: shareConfig.path || `/${route}`,
            imageUrl: shareConfig.imageUrl || '/static/share.png',
            // 自定义参数
            ...(shareConfig.extra || {})
        }
    },
    
    // 分享到朋友圈
    onShareTimeline() {
        const pages = getCurrentPages()
        const currentPage = pages[pages.length - 1]
        
        // 如果页面自己定义了 onShareTimeline，优先使用
        if (currentPage?.onShareTimeline && currentPage.onShareTimeline !== this.onShareTimeline) {
            return currentPage.onShareTimeline.call(currentPage)
        }
        
        const shareConfig = currentPage?.data?._shareConfig || {}
        
        return {
            title: shareConfig.title || '默认分享标题',
            query: shareConfig.query || 'from=timeline',
            imageUrl: shareConfig.imageUrl || '/static/share.png'
        }
    }
}