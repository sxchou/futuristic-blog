<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dashboardApi } from '@/api'
import { isCancelError } from '@/utils/error'
import type { 
  OverviewStats, 
  TrendData, 
  CategoryStats, 
  TagStats, 
  ArticleViewsRank,
  AccessTrend
} from '@/api/dashboard'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import PieChart from '@/components/charts/PieChart.vue'

const loading = ref(true)
const overview = ref<OverviewStats | null>(null)
const viewsTrend = ref<TrendData[]>([])
const articlesTrend = ref<TrendData[]>([])
const commentTrend = ref<TrendData[]>([])
const categoryStats = ref<CategoryStats[]>([])
const tagStats = ref<TagStats[]>([])
const articleRank = ref<ArticleViewsRank[]>([])
const accessTrend = ref<AccessTrend[]>([])

const trendDays = ref(30)
const rankSortBy = ref<'views' | 'likes' | 'comments'>('views')
const rankLimit = ref(10)

const loadingViewsTrend = ref(false)
const loadingArticlesTrend = ref(false)
const loadingCommentTrend = ref(false)
const loadingCategoryStats = ref(false)
const loadingTagStats = ref(false)
const loadingArticleRank = ref(false)
const loadingAccessTrend = ref(false)

const showChartModal = ref(false)
const modalChart = ref<{
  type: 'line' | 'bar' | 'pie'
  title: string
  data: TrendData[] | CategoryStats[] | TagStats[] | { name: string; value: number }[]
  color?: string
  colors?: string[]
  areaStyle?: boolean
  roseType?: boolean
  refreshFn?: () => Promise<void>
  loading?: boolean
} | null>(null)

const modalLoading = ref(false)

const openChartModal = (chart: typeof modalChart.value) => {
  modalChart.value = chart
  showChartModal.value = true
}

const closeChartModal = () => {
  showChartModal.value = false
  modalChart.value = null
}

const handleModalRefresh = async () => {
  if (!modalChart.value?.refreshFn || !showChartModal.value || modalLoading.value) return
  
  modalLoading.value = true
  try {
    await modalChart.value.refreshFn()
  } catch (error) {
    console.error('Modal refresh failed:', error)
  } finally {
    modalLoading.value = false
  }
}

const accessTrendChartData = computed(() => {
  return accessTrend.value.map(item => ({
    name: item.date,
    value: item.page_views
  }))
})

const fetchAllData = async () => {
  loading.value = true
  loadingViewsTrend.value = true
  loadingArticlesTrend.value = true
  loadingCommentTrend.value = true
  loadingCategoryStats.value = true
  loadingTagStats.value = true
  loadingArticleRank.value = true
  loadingAccessTrend.value = true
  
  try {
    const res = await dashboardApi.getInitData({
      trend_days: trendDays.value,
      access_days: 7,
      tag_limit: 10,
      rank_limit: rankLimit.value,
      rank_sort_by: rankSortBy.value
    })
    
    const data = res.data
    overview.value = data.overview
    viewsTrend.value = data.trends.views_trend
    articlesTrend.value = data.trends.articles_trend
    commentTrend.value = data.trends.comment_trend
    accessTrend.value = data.trends.access_trend
    categoryStats.value = data.category_stats
    tagStats.value = data.tag_stats
    articleRank.value = data.article_rank
  } catch (error: unknown) {
    if (isCancelError(error)) {
      return
    }
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
    loadingViewsTrend.value = false
    loadingArticlesTrend.value = false
    loadingCommentTrend.value = false
    loadingCategoryStats.value = false
    loadingTagStats.value = false
    loadingArticleRank.value = false
    loadingAccessTrend.value = false
  }
}

const handleRefresh = async () => {
  await fetchAllData()
}

const refreshViewsTrend = async () => {
  loadingViewsTrend.value = true
  try {
    const res = await dashboardApi.getViewsTrend(trendDays.value)
    viewsTrend.value = res.data
  } catch (error) {
    console.error('Failed to refresh views trend:', error)
  } finally {
    loadingViewsTrend.value = false
  }
}

const refreshArticlesTrend = async () => {
  loadingArticlesTrend.value = true
  try {
    const res = await dashboardApi.getArticlesTrend(trendDays.value)
    articlesTrend.value = res.data
  } catch (error) {
    console.error('Failed to refresh articles trend:', error)
  } finally {
    loadingArticlesTrend.value = false
  }
}

const refreshCommentTrend = async () => {
  loadingCommentTrend.value = true
  try {
    const res = await dashboardApi.getCommentTrend(trendDays.value)
    commentTrend.value = res.data
  } catch (error) {
    console.error('Failed to refresh comment trend:', error)
  } finally {
    loadingCommentTrend.value = false
  }
}

const refreshCategoryStats = async () => {
  loadingCategoryStats.value = true
  try {
    const res = await dashboardApi.getCategoryStats()
    categoryStats.value = res.data
  } catch (error) {
    console.error('Failed to refresh category stats:', error)
  } finally {
    loadingCategoryStats.value = false
  }
}

const refreshTagStats = async () => {
  loadingTagStats.value = true
  try {
    const res = await dashboardApi.getTagStats(10)
    tagStats.value = res.data
  } catch (error) {
    console.error('Failed to refresh tag stats:', error)
  } finally {
    loadingTagStats.value = false
  }
}

const refreshArticleRank = async () => {
  loadingArticleRank.value = true
  try {
    const res = await dashboardApi.getArticleRank(rankLimit.value, rankSortBy.value)
    articleRank.value = res.data
  } catch (error) {
    console.error('Failed to refresh article rank:', error)
  } finally {
    loadingArticleRank.value = false
  }
}

const refreshAccessTrend = async () => {
  loadingAccessTrend.value = true
  try {
    const res = await dashboardApi.getAccessTrend(7)
    accessTrend.value = res.data
  } catch (error) {
    console.error('Failed to refresh access trend:', error)
  } finally {
    loadingAccessTrend.value = false
  }
}

const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

onMounted(() => {
  fetchAllData()
})
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
          <svg class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
          </svg>
        </div>
        <h1 class="text-sm sm:text-base font-bold text-gray-900 dark:text-white">仪表盘</h1>
      </div>
      <div class="header-actions">
        <form class="inline-flex items-center gap-2" @submit.prevent>
          <select id="select-trendDays" v-model="trendDays" name="trend-days" class="trend-select" @change="fetchAllData">
          <option :value="7">近 7 天</option>
          <option :value="14">近 14 天</option>
          <option :value="30">近 30 天</option>
          <option :value="60">近 60 天</option>
          <option :value="90">近 90 天</option>
        </select>
        </form>
        <button class="refresh-btn" @click="handleRefresh">
          <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>刷新</span>
        </button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon bg-primary/20">
          <svg class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">文章</span>
          <span class="stat-value">{{ overview?.total_articles || 0 }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-secondary/20">
          <svg class="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">浏览</span>
          <span class="stat-value">{{ formatNumber(overview?.total_views || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-accent/20">
          <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">点赞</span>
          <span class="stat-value">{{ formatNumber(overview?.total_likes || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-green-500/20">
          <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">评论</span>
          <span class="stat-value">{{ formatNumber(overview?.total_comments || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-yellow-500/20">
          <svg class="w-4 h-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">用户</span>
          <span class="stat-value">{{ overview?.total_users || 0 }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-pink-500/20">
          <svg class="w-4 h-4 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">今日</span>
          <span class="stat-value">{{ overview?.new_articles_today || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <LineChart title="浏览量趋势" :data="viewsTrend" :height="200" :loading="loadingViewsTrend" color="#00d4ff" :show-export="true" :show-expand="true" @refresh="refreshViewsTrend" @expand="openChartModal({ type: 'line', title: '浏览量趋势', data: viewsTrend, color: '#00d4ff', refreshFn: refreshViewsTrend })" />
      </div>
      <div class="chart-card">
        <LineChart title="文章发布趋势" :data="articlesTrend" :height="200" :loading="loadingArticlesTrend" color="#7c3aed" :show-export="true" :show-expand="true" @refresh="refreshArticlesTrend" @expand="openChartModal({ type: 'line', title: '文章发布趋势', data: articlesTrend, color: '#7c3aed', refreshFn: refreshArticlesTrend })" />
      </div>
      <div class="chart-card">
        <PieChart title="分类分布" :data="categoryStats" :height="200" :loading="loadingCategoryStats" :show-export="true" :show-expand="true" @refresh="refreshCategoryStats" @expand="openChartModal({ type: 'pie', title: '分类分布', data: categoryStats, refreshFn: refreshCategoryStats })" />
      </div>
      <div class="chart-card">
        <PieChart title="热门标签" :data="tagStats" :height="200" :loading="loadingTagStats" :rose-type="true" :show-export="true" :show-expand="true" @refresh="refreshTagStats" @expand="openChartModal({ type: 'pie', title: '热门标签', data: tagStats, roseType: true, refreshFn: refreshTagStats })" />
      </div>
      <div class="chart-card">
        <LineChart title="评论趋势" :data="commentTrend" :height="200" :loading="loadingCommentTrend" color="#10b981" :area-style="true" :show-export="true" :show-expand="true" @refresh="refreshCommentTrend" @expand="openChartModal({ type: 'line', title: '评论趋势', data: commentTrend, color: '#10b981', areaStyle: true, refreshFn: refreshCommentTrend })" />
      </div>
      <div class="chart-card">
        <BarChart title="访问趋势" :data="accessTrendChartData" :height="200" :loading="loadingAccessTrend" :colors="['#00d4ff', '#7c3aed']" :show-export="true" :show-expand="true" @refresh="refreshAccessTrend" @expand="openChartModal({ type: 'bar', title: '访问趋势', data: accessTrendChartData, colors: ['#00d4ff', '#7c3aed'], refreshFn: refreshAccessTrend })" />
      </div>
    </div>

    <div class="rank-section">
      <div class="rank-card">
        <div class="rank-header">
          <h3 class="rank-title">热门文章</h3>
          <div class="rank-tabs">
            <button v-for="sort in ['views', 'likes', 'comments']" :key="sort" :class="['rank-tab', { active: rankSortBy === sort }]" @click="rankSortBy = sort as any; refreshArticleRank()">
              {{ sort === 'views' ? '浏览' : sort === 'likes' ? '点赞' : '评论' }}
            </button>
          </div>
        </div>
        <div class="rank-list">
          <div v-if="loadingArticleRank" class="rank-loading">
            <div class="loading-spinner" />
            <span>加载中...</span>
          </div>
          <template v-else>
            <div v-for="(article, index) in articleRank" :key="article.id" class="rank-item">
              <span v-if="index < 3" class="rank-number top">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="white">
                  <path d="M12 2C12 2 8 6 8 10C8 12 9 13 9 13C9 13 7 11 7 8C7 8 4 12 4 15C4 19 7 22 12 22C17 22 20 19 20 15C20 11 17 7 17 7C17 7 18 9 18 11C18 11 16 9 16 7C16 5 14 3 14 3C14 3 15 5 15 7C15 9 13 11 13 11C13 11 14 9 14 7C14 5 12 2 12 2Z"/>
                </svg>
              </span>
              <span v-else class="rank-number">{{ index + 1 }}</span>
              <div class="rank-content">
                <span class="rank-name">{{ article.title }}</span>
                <div class="rank-stats">
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>{{ article.views }}</span>
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>{{ article.likes }}</span>
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>{{ article.comments }}</span>
                </div>
              </div>
            </div>
            <div v-if="articleRank.length === 0" class="rank-empty">暂无数据</div>
          </template>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showChartModal" class="chart-modal-overlay" @click.self="closeChartModal">
          <div class="chart-modal">
            <div class="chart-modal-header">
              <h3 class="chart-modal-title">{{ modalChart?.title }}</h3>
              <button class="chart-modal-close" @click="closeChartModal">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="chart-modal-content">
              <LineChart
                v-if="modalChart?.type === 'line'"
                :title="modalChart.title"
                :data="modalChart.data as TrendData[]"
                :height="400"
                :color="modalChart.color"
                :area-style="modalChart.areaStyle"
                :loading="modalLoading"
                :show-refresh="true"
                :show-export="true"
                @refresh="handleModalRefresh"
              />
              <BarChart
                v-else-if="modalChart?.type === 'bar'"
                :title="modalChart.title"
                :data="modalChart.data as { name: string; value: number }[]"
                :height="400"
                :colors="modalChart.colors"
                :loading="modalLoading"
                :show-refresh="true"
                :show-export="true"
                @refresh="handleModalRefresh"
              />
              <PieChart
                v-else-if="modalChart?.type === 'pie'"
                :title="modalChart.title"
                :data="modalChart.data as CategoryStats[]"
                :height="400"
                :rose-type="modalChart.roseType"
                :loading="modalLoading"
                :show-refresh="true"
                :show-export="true"
                @refresh="handleModalRefresh"
              />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 0;
  overflow-x: hidden;
}

.dashboard-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 12px;
}

@media (min-width: 640px) {
  .dashboard-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
}

.header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  width: 100%;
}

@media (min-width: 640px) {
  .header-actions {
    width: auto;
  }
}

.trend-select {
  padding: 5px 8px;
  font-size: 11px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
}

@media (min-width: 640px) {
  .trend-select {
    padding: 6px 10px;
    font-size: 12px;
    flex: none;
  }
}

.dark .trend-select {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
  color: #e5e7eb;
}

.trend-select:hover {
  border-color: #00d4ff;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  font-size: 11px;
  color: white;
  background: #00d4ff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

@media (min-width: 640px) {
  .refresh-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
}

.refresh-btn:hover {
  opacity: 0.9;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

@media (min-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

@media (min-width: 640px) {
  .stat-card {
    padding: 12px;
    gap: 10px;
  }
}

.dark .stat-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

@media (min-width: 640px) {
  .stat-icon {
    width: 36px;
    height: 36px;
  }
}

.stat-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.stat-label {
  font-size: 10px;
  color: #6b7280;
  white-space: nowrap;
}

@media (min-width: 640px) {
  .stat-label {
    font-size: 11px;
  }
}

.dark .stat-label {
  color: #9ca3af;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
}

@media (min-width: 640px) {
  .stat-value {
    font-size: 16px;
  }
}

.dark .stat-value {
  color: #f3f4f6;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

@media (min-width: 768px) {
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }
}

@media (min-width: 1280px) {
  .charts-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

@media (min-width: 640px) {
  .chart-card {
    padding: 16px;
  }
}

.dark .chart-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.chart-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.rank-section {
  margin-bottom: 12px;
}

.rank-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 12px;
}

@media (min-width: 640px) {
  .rank-card {
    padding: 16px;
  }
}

.dark .rank-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.rank-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.rank-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

@media (min-width: 640px) {
  .rank-title {
    font-size: 16px;
  }
}

.dark .rank-title {
  color: #f3f4f6;
}

.rank-tabs {
  display: flex;
  gap: 4px;
}

.rank-tab {
  padding: 4px 10px;
  font-size: 11px;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

@media (min-width: 640px) {
  .rank-tab {
    padding: 6px 12px;
    font-size: 12px;
  }
}

.dark .rank-tab {
  background: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
}

.rank-tab:hover {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
}

.rank-tab.active {
  background: #00d4ff;
  color: white;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #6b7280;
}

.dark .rank-loading {
  color: #9ca3af;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 212, 255, 0.2);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.02);
  transition: all 0.2s;
}

@media (min-width: 640px) {
  .rank-item {
    padding: 10px;
    gap: 12px;
  }
}

.dark .rank-item {
  background: rgba(255, 255, 255, 0.02);
}

.rank-item:hover {
  background: rgba(0, 212, 255, 0.05);
}

.rank-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
  color: #6b7280;
}

@media (min-width: 640px) {
  .rank-number {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
}

.dark .rank-number {
  background: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
}

.rank-number.top {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: white;
  box-shadow: 0 0 8px rgba(249, 115, 22, 0.4);
}

.rank-content {
  flex: 1;
  min-width: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.rank-name {
  font-size: 12px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (min-width: 640px) {
  .rank-name {
    font-size: 13px;
  }
}

.dark .rank-name {
  color: #e5e7eb;
}

.rank-stats {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.rank-stats span {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: #6b7280;
}

@media (min-width: 640px) {
  .rank-stats span {
    font-size: 11px;
    gap: 3px;
  }
}

.dark .rank-stats span {
  color: #9ca3af;
}

.rank-stats svg {
  opacity: 0.6;
}

.rank-empty {
  text-align: center;
  padding: 20px;
  color: #6b7280;
  font-size: 12px;
}

.dark .rank-empty {
  color: #9ca3af;
}

.chart-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.chart-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dark .chart-modal {
  background: #1f2937;
}

.chart-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.dark .chart-modal-header {
  border-color: rgba(255, 255, 255, 0.05);
}

.chart-modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.dark .chart-modal-title {
  color: #f3f4f6;
}

.chart-modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.dark .chart-modal-close {
  background: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
}

.chart-modal-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #111827;
}

.dark .chart-modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f3f4f6;
}

.chart-modal-content {
  padding: 20px;
  overflow-y: auto;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .chart-modal,
.modal-leave-to .chart-modal {
  transform: scale(0.95);
}
</style>
