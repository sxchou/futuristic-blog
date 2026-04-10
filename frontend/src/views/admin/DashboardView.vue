<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dashboardApi } from '@/api'
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
import { useAdminCheck } from '@/composables/useAdminCheck'

const { requireAdmin } = useAdminCheck()

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

const accessTrendChartData = computed(() => {
  return accessTrend.value.map(item => ({
    name: item.date,
    value: item.page_views
  }))
})

const fetchAllData = async () => {
  loading.value = true
  try {
    const [
      overviewRes,
      viewsTrendRes,
      articlesTrendRes,
      commentTrendRes,
      categoryStatsRes,
      tagStatsRes,
      articleRankRes,
      accessTrendRes
    ] = await Promise.all([
      dashboardApi.getOverview(),
      dashboardApi.getViewsTrend(trendDays.value),
      dashboardApi.getArticlesTrend(trendDays.value),
      dashboardApi.getCommentTrend(trendDays.value),
      dashboardApi.getCategoryStats(),
      dashboardApi.getTagStats(10),
      dashboardApi.getArticleRank(rankLimit.value, rankSortBy.value),
      dashboardApi.getAccessTrend(7)
    ])
    
    overview.value = overviewRes.data
    viewsTrend.value = viewsTrendRes.data
    articlesTrend.value = articlesTrendRes.data
    commentTrend.value = commentTrendRes.data
    categoryStats.value = categoryStatsRes.data
    tagStats.value = tagStatsRes.data
    articleRank.value = articleRankRes.data
    accessTrend.value = accessTrendRes.data
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  if (!await requireAdmin('刷新仪表盘数据')) return
  await fetchAllData()
}

const refreshViewsTrend = async () => {
  if (!await requireAdmin('刷新浏览量趋势')) return
  
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
  if (!await requireAdmin('刷新文章发布趋势')) return
  
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
  if (!await requireAdmin('刷新评论趋势')) return
  
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
  if (!await requireAdmin('刷新分类统计')) return
  
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
  if (!await requireAdmin('刷新标签统计')) return
  
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
  if (!await requireAdmin('刷新文章排行')) return
  
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
  if (!await requireAdmin('刷新访问量趋势')) return
  
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
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">仪表盘</h1>
      <div class="header-actions">
        <select 
          v-model="trendDays" 
          @change="fetchAllData"
          class="trend-select"
        >
          <option :value="7">近 7 天</option>
          <option :value="14">近 14 天</option>
          <option :value="30">近 30 天</option>
          <option :value="60">近 60 天</option>
          <option :value="90">近 90 天</option>
        </select>
        <button @click="handleRefresh" class="refresh-btn" :disabled="loading">
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新数据
        </button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon bg-primary/20">
          <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">文章总数</span>
          <span class="stat-value">{{ overview?.total_articles || 0 }}</span>
          <span class="stat-extra">已发布 {{ overview?.published_articles || 0 }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-secondary/20">
          <svg class="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">总浏览量</span>
          <span class="stat-value">{{ formatNumber(overview?.total_views || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-accent/20">
          <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">总点赞数</span>
          <span class="stat-value">{{ formatNumber(overview?.total_likes || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-green-500/20">
          <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">评论数</span>
          <span class="stat-value">{{ formatNumber(overview?.total_comments || 0) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-yellow-500/20">
          <svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">用户总数</span>
          <span class="stat-value">{{ overview?.total_users || 0 }}</span>
          <span class="stat-extra">今日新增 {{ overview?.new_users_today || 0 }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-pink-500/20">
          <svg class="w-5 h-5 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-label">今日文章</span>
          <span class="stat-value">{{ overview?.new_articles_today || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card chart-card-large">
        <LineChart
          title="浏览量趋势"
          :data="viewsTrend"
          :height="280"
          :loading="loadingViewsTrend"
          color="#00d4ff"
          @refresh="refreshViewsTrend"
        />
      </div>

      <div class="chart-card chart-card-large">
        <LineChart
          title="文章发布趋势"
          :data="articlesTrend"
          :height="280"
          :loading="loadingArticlesTrend"
          color="#7c3aed"
          @refresh="refreshArticlesTrend"
        />
      </div>

      <div class="chart-card">
        <PieChart
          title="文章分类分布"
          :data="categoryStats"
          :height="280"
          :loading="loadingCategoryStats"
          @refresh="refreshCategoryStats"
        />
      </div>

      <div class="chart-card">
        <PieChart
          title="热门标签"
          :data="tagStats"
          :height="280"
          :loading="loadingTagStats"
          :rose-type="true"
          @refresh="refreshTagStats"
        />
      </div>

      <div class="chart-card chart-card-large">
        <LineChart
          title="评论趋势"
          :data="commentTrend"
          :height="280"
          :loading="loadingCommentTrend"
          color="#10b981"
          :area-style="true"
          @refresh="refreshCommentTrend"
        />
      </div>

      <div class="chart-card chart-card-large">
        <BarChart
          title="访问量趋势"
          :data="accessTrendChartData"
          :height="280"
          :loading="loadingAccessTrend"
          :colors="['#00d4ff', '#7c3aed']"
          @refresh="refreshAccessTrend"
        />
      </div>
    </div>

    <div class="rank-section">
      <div class="rank-card">
        <div class="rank-header">
          <h3 class="rank-title">热门文章排行</h3>
          <div class="rank-tabs">
            <button 
              v-for="sort in ['views', 'likes', 'comments']" 
              :key="sort"
              :class="['rank-tab', { active: rankSortBy === sort }]"
              @click="rankSortBy = sort as any; refreshArticleRank()"
            >
              {{ sort === 'views' ? '浏览' : sort === 'likes' ? '点赞' : '评论' }}
            </button>
          </div>
        </div>
        <div class="rank-list">
          <div v-if="loadingArticleRank" class="rank-loading">
            <div class="loading-spinner"></div>
            <span>加载中...</span>
          </div>
          <template v-else>
            <div 
              v-for="(article, index) in articleRank" 
              :key="article.id"
              class="rank-item"
            >
              <span class="rank-number" :class="{ top: index < 3 }">{{ index + 1 }}</span>
              <div class="rank-content">
                <span class="rank-name">{{ article.title }}</span>
                <div class="rank-stats">
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>{{ article.views }}</span>
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>{{ article.likes }}</span>
                  <span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>{{ article.comments }}</span>
                </div>
              </div>
            </div>
            <div v-if="articleRank.length === 0" class="rank-empty">
              暂无数据
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 0;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.trend-select {
  padding: 8px 12px;
  font-size: 13px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
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
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  color: white;
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.refresh-btn:hover {
  opacity: 0.9;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .stat-card {
    padding: 12px;
    gap: 8px;
  }
  
  .stat-icon {
    width: 36px;
    height: 36px;
  }
  
  .stat-value {
    font-size: 16px;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .rank-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .rank-stats {
    gap: 8px;
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: transform 0.2s, box-shadow 0.2s;
}

.dark .stat-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.dark .stat-label {
  color: #9ca3af;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.dark .stat-value {
  color: #f3f4f6;
}

.stat-extra {
  font-size: 11px;
  color: #9ca3af;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.dark .chart-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.chart-card-large {
  grid-column: span 1;
}

@media (min-width: 1200px) {
  .chart-card-large {
    grid-column: span 1;
  }
}

.rank-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.rank-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.dark .rank-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.rank-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.rank-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.dark .rank-title {
  color: #f3f4f6;
}

.rank-tabs {
  display: flex;
  gap: 4px;
}

.rank-tab {
  padding: 6px 12px;
  font-size: 12px;
  color: #6b7280;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.dark .rank-tab {
  border-color: rgba(255, 255, 255, 0.1);
  color: #9ca3af;
}

.rank-tab:hover {
  border-color: #00d4ff;
  color: #00d4ff;
}

.rank-tab.active {
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  border-color: transparent;
  color: white;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  transition: background 0.2s;
}

.dark .rank-item {
  background: rgba(255, 255, 255, 0.02);
}

.rank-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.dark .rank-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.rank-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
}

.dark .rank-number {
  background: rgba(255, 255, 255, 0.1);
  color: #9ca3af;
}

.rank-number.top {
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  color: white;
}

.rank-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.rank-name {
  font-size: 13px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .rank-name {
  color: #e5e7eb;
}

.rank-stats {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.rank-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.rank-stats svg {
  opacity: 0.6;
}

.rank-empty {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
  font-size: 14px;
}

.rank-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
  color: #9ca3af;
  font-size: 14px;
}

.rank-loading .loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 212, 255, 0.2);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
