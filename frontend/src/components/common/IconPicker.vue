<template>
  <div class="icon-picker relative inline-block">
    <div
      ref="triggerRef"
      class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:border-primary/50 transition-colors"
      @click.stop="togglePicker"
    >
      <div
        v-if="modelValue"
        class="w-6 h-6 flex items-center justify-center text-lg"
      >
        <span v-if="iconType === 'emoji'">{{ modelValue }}</span>
        <i
          v-else-if="iconType === 'fontawesome'"
          :class="modelValue"
          class="text-base"
        />
        <span
          v-else-if="iconType === 'material'"
          class="material-icons text-base"
        >{{ modelValue }}</span>
        <component
          v-else-if="iconType === 'heroicon'"
          :is="getHeroicon(modelValue)"
          class="w-5 h-5"
        />
      </div>
      <div
        v-else
        class="w-6 h-6 flex items-center justify-center text-gray-400"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
      <span class="text-sm text-gray-600 dark:text-gray-300 flex-1">
        {{ modelValue || '选择图标' }}
      </span>
      <svg
        class="w-4 h-4 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </div>

    <Teleport to="body">
      <div
        v-if="showPicker"
        class="fixed z-[9999] bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg shadow-2xl p-4 w-96"
        :style="pickerStyle"
        @click.stop
      >
        <div class="flex items-center justify-between mb-3 cursor-move select-none" @mousedown="handleDragStart">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">选择图标</span>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
            @click.stop="showPicker = false"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="flex gap-1 mb-3">
          <button
            v-for="lib in iconLibraries"
            :key="lib.id"
            type="button"
            :class="[
              'px-3 py-1.5 text-xs rounded transition-colors',
              activeLibrary === lib.id
                ? 'bg-primary text-white'
                : 'bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
            ]"
            @click.stop="activeLibrary = lib.id"
          >
            {{ lib.label }}
          </button>
        </div>

        <div class="mb-3">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索图标..."
            class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
          >
        </div>

        <div
          v-if="activeLibrary === 'emoji'"
          class="space-y-3"
        >
          <div class="flex gap-1">
            <button
              v-for="cat in emojiCategories"
              :key="cat.name"
              type="button"
              :class="[
                'px-2 py-1 text-xs rounded transition-colors',
                activeEmojiCategory === cat.name
                  ? 'bg-primary/20 text-primary'
                  : 'bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
              ]"
              @click.stop="activeEmojiCategory = cat.name"
            >
              {{ cat.icon }} {{ cat.label }}
            </button>
          </div>
          <div class="grid grid-cols-8 gap-1 max-h-64 overflow-y-auto">
            <button
              v-for="emoji in filteredEmojis"
              :key="emoji"
              type="button"
              :class="[
                'w-8 h-8 flex items-center justify-center text-lg hover:bg-primary/10 rounded transition-colors',
                modelValue === emoji ? 'bg-primary/20 ring-2 ring-primary' : ''
              ]"
              @click.stop="selectIcon(emoji, 'emoji')"
            >
              {{ emoji }}
            </button>
          </div>
        </div>

        <div
          v-else-if="activeLibrary === 'fontawesome'"
          class="space-y-3"
        >
          <div class="flex gap-1 flex-wrap">
            <button
              v-for="cat in faCategories"
              :key="cat.id"
              type="button"
              :class="[
                'px-2 py-1 text-xs rounded transition-colors',
                activeFaCategory === cat.id
                  ? 'bg-primary/20 text-primary'
                  : 'bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
              ]"
              @click.stop="activeFaCategory = cat.id"
            >
              {{ cat.label }}
            </button>
          </div>
          <div class="grid grid-cols-6 gap-2 max-h-64 overflow-y-auto">
            <button
              v-for="icon in filteredFaIcons"
              :key="icon"
              type="button"
              :class="[
                'w-12 h-12 flex flex-col items-center justify-center gap-1 hover:bg-primary/10 rounded transition-colors',
                modelValue === icon ? 'bg-primary/20 ring-2 ring-primary' : ''
              ]"
              :title="icon"
              @click.stop="selectIcon(icon, 'fontawesome')"
            >
              <i :class="icon" />
              <span class="text-[10px] text-gray-500 truncate w-full text-center">{{ getIconName(icon) }}</span>
            </button>
          </div>
        </div>

        <div
          v-else-if="activeLibrary === 'material'"
          class="grid grid-cols-6 gap-2 max-h-80 overflow-y-auto"
        >
          <button
            v-for="icon in filteredMaterialIcons"
            :key="icon"
            type="button"
            :class="[
              'w-12 h-12 flex flex-col items-center justify-center gap-1 hover:bg-primary/10 rounded transition-colors',
              modelValue === icon ? 'bg-primary/20 ring-2 ring-primary' : ''
            ]"
            :title="icon"
            @click.stop="selectIcon(icon, 'material')"
          >
            <span class="material-icons text-xl">{{ icon }}</span>
            <span class="text-[10px] text-gray-500 truncate w-full text-center">{{ icon }}</span>
          </button>
        </div>

        <div
          v-else-if="activeLibrary === 'heroicon'"
          class="grid grid-cols-4 gap-2 max-h-80 overflow-y-auto"
        >
          <button
            v-for="icon in filteredHeroicons"
            :key="icon"
            type="button"
            :class="[
              'w-full h-16 flex flex-col items-center justify-center gap-1 hover:bg-primary/10 rounded transition-colors',
              modelValue === icon ? 'bg-primary/20 ring-2 ring-primary' : ''
            ]"
            :title="icon"
            @click.stop="selectIcon(icon, 'heroicon')"
          >
            <component
              :is="getHeroicon(icon)"
              class="w-6 h-6"
            />
            <span class="text-[10px] text-gray-500 truncate w-full text-center px-1">{{ icon }}</span>
          </button>
        </div>

        <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-200 dark:border-white/10">
          <button
            type="button"
            class="text-xs text-gray-500 hover:text-red-400 transition-colors"
            @click.stop="clearIcon"
          >
            清除图标
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs bg-primary text-white rounded hover:bg-primary/80 transition-colors"
            @click.stop="showPicker = false"
          >
            确定
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { h } from 'vue'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | undefined]
}>()

const showPicker = ref(false)
const activeLibrary = ref('emoji')
const searchQuery = ref('')
const activeEmojiCategory = ref('smileys')
const activeFaCategory = ref('solid')
const triggerRef = ref<HTMLElement | null>(null)
const pickerPosition = ref({ top: 0, left: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0, top: 0, left: 0 })

const iconLibraries = [
  { id: 'emoji', label: 'Emoji' },
  { id: 'fontawesome', label: 'Font Awesome' },
  { id: 'material', label: 'Material Icons' },
  { id: 'heroicon', label: 'Heroicons' },
]

const emojiCategories = [
  { name: 'smileys', icon: '😊', label: '表情' },
  { name: 'gestures', icon: '👋', label: '手势' },
  { name: 'animals', icon: '🐱', label: '动物' },
  { name: 'food', icon: '🍕', label: '食物' },
  { name: 'symbols', icon: '❤️', label: '符号' },
  { name: 'objects', icon: '💡', label: '物品' },
  { name: 'nature', icon: '🌸', label: '自然' },
]

const emojis: Record<string, string[]> = {
  smileys: [
    '😊', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😋', '😎',
    '😍', '😘', '🥰', '😗', '😙', '😚', '🙂', '🤗', '🤩', '🤔',
    '🤨', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮', '🤐',
    '😯', '😪', '😫', '😴', '😌', '😛', '😜', '😝', '🤤', '😒',
    '😓', '😔', '😕', '🙃', '🤑', '😲', '🙁', '😖', '😞', '😟',
    '😤', '😢', '😭', '😦', '😧', '😨', '😩', '🤯', '😬', '😰',
    '😱', '🥵', '🥶', '😳', '🤪', '😵', '🥴', '😠', '😡', '🤬',
    '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥳', '🥺', '🤥', '🤫',
  ],
  gestures: [
    '👋', '🤚', '🖐️', '✋', '🖖', '👌', '🤌', '🤏', '✌️', '🤞',
    '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍',
    '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝',
    '🙏', '✍️', '💪', '🦾', '🦿', '🦵', '🦶', '👂', '🦻', '👃',
  ],
  animals: [
    '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
    '🦁', '🐮', '🐷', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔',
    '🐧', '🐦', '🐤', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇', '🐺',
    '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🦟',
    '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🦐', '🦞', '🦀',
    '🐡', '🐠', '🐟', '🐬', '🐳', '🐋', '🦈', '🐊', '🐅', '🐆',
  ],
  food: [
    '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈',
    '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦',
    '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔',
    '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈',
    '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟',
    '🍕', '🫓', '🥪', '🥙', '🧆', '🌮', '🌯', '🫔', '🥗', '🥘',
  ],
  symbols: [
    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
    '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️',
    '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐',
    '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐',
    '♑', '♒', '♓', '🆔', '⚛️', '🉑', '☢️', '☣️', '📴', '📳',
    '🈶', '🈚', '🈸', '🈺', '🈷️', '✴️', '🆚', '💮', '🉐', '㊙️',
  ],
  objects: [
    '💡', '🔦', '🏮', '📱', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️',
    '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️',
    '🎬', '📺', '📻', '🎙️', '🎚️', '🎛️', '🎤', '🎧', '🎼', '🎵',
    '🎶', '🎹', '🥁', '🎷', '🎺', '🎸', '🪕', '🎻', '🪗', '🥁',
    '⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '🕹️',
    '🗜️', '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥',
  ],
  nature: [
    '🌸', '🌺', '🌻', '🌹', '🥀', '🌷', '🌱', '🌲', '🌳', '🌴',
    '🌵', '🌾', '🌿', '☘️', '🍀', '🍁', '🍂', '🍃', '🌊', '💧',
    '💦', '☔', '🌈', '⭐', '🌟', '✨', '⚡', '☄️', '💥', '🔥',
    '🌪️', '🌈', '☀️', '🌤️', '⛅', '🌥️', '☁️', '🌦️', '🌧️', '🌨️',
    '❄️', '☃️', '⛄', '🌬️', '💨', '🌪️', '🌫️', '🌊', '💧', '💦',
    '☔', '🌈', '⭐', '🌟', '✨', '⚡', '☄️', '💥', '🔥', '🌙',
  ],
}

const faCategories = [
  { id: 'solid', label: '实心' },
  { id: 'brands', label: '品牌' },
  { id: 'arrows', label: '箭头' },
  { id: 'communication', label: '通讯' },
  { id: 'files', label: '文件' },
  { id: 'users', label: '用户' },
  { id: 'web', label: '网页' },
]

const faIcons: Record<string, string[]> = {
  solid: [
    'fas fa-home', 'fas fa-user', 'fas fa-cog', 'fas fa-search', 'fas fa-heart',
    'fas fa-star', 'fas fa-check', 'fas fa-times', 'fas fa-plus', 'fas fa-minus',
    'fas fa-edit', 'fas fa-trash', 'fas fa-save', 'fas fa-download', 'fas fa-upload',
    'fas fa-share', 'fas fa-link', 'fas fa-image', 'fas fa-video', 'fas fa-music',
    'fas fa-book', 'fas fa-file', 'fas fa-folder', 'fas fa-database', 'fas fa-server',
    'fas fa-cloud', 'fas fa-lock', 'fas fa-unlock', 'fas fa-key', 'fas fa-shield-alt',
    'fas fa-bell', 'fas fa-envelope', 'fas fa-comment', 'fas fa-comments', 'fas fa-phone',
    'fas fa-camera', 'fas fa-map-marker-alt', 'fas fa-globe', 'fas fa-wifi', 'fas fa-bluetooth',
  ],
  brands: [
    'fab fa-github', 'fab fa-gitlab', 'fab fa-bitbucket', 'fab fa-docker', 'fab fa-aws',
    'fab fa-google', 'fab fa-microsoft', 'fab fa-apple', 'fab fa-linux', 'fab fa-windows',
    'fab fa-android', 'fab fa-chrome', 'fab fa-firefox', 'fab fa-safari', 'fab fa-edge',
    'fab fa-facebook', 'fab fa-twitter', 'fab fa-instagram', 'fab fa-linkedin', 'fab fa-youtube',
    'fab fa-weixin', 'fab fa-weibo', 'fab fa-qq', 'fab fa-zhihu', 'fab fa-tiktok',
    'fab fa-discord', 'fab fa-slack', 'fab fa-telegram', 'fab fa-whatsapp', 'fab fa-reddit',
  ],
  arrows: [
    'fas fa-arrow-up', 'fas fa-arrow-down', 'fas fa-arrow-left', 'fas fa-arrow-right',
    'fas fa-arrow-circle-up', 'fas fa-arrow-circle-down', 'fas fa-arrow-circle-left', 'fas fa-arrow-circle-right',
    'fas fa-chevron-up', 'fas fa-chevron-down', 'fas fa-chevron-left', 'fas fa-chevron-right',
    'fas fa-angle-up', 'fas fa-angle-down', 'fas fa-angle-left', 'fas fa-angle-right',
    'fas fa-caret-up', 'fas fa-caret-down', 'fas fa-caret-left', 'fas fa-caret-right',
    'fas fa-long-arrow-up', 'fas fa-long-arrow-down', 'fas fa-long-arrow-left', 'fas fa-long-arrow-right',
    'fas fa-exchange-alt', 'fas fa-random', 'fas fa-sync', 'fas fa-undo', 'fas fa-redo',
  ],
  communication: [
    'fas fa-envelope', 'fas fa-envelope-open', 'fas fa-paper-plane', 'fas fa-inbox',
    'fas fa-comment', 'fas fa-comments', 'fas fa-comment-dots', 'fas fa-sms',
    'fas fa-phone', 'fas fa-phone-alt', 'fas fa-phone-square', 'fas fa-mobile',
    'fas fa-mobile-alt', 'fas fa-at', 'fas fa-mail-bulk', 'fas fa-reply',
    'fas fa-reply-all', 'fas fa-forward', 'fas fa-bell', 'fas fa-bell-slash',
  ],
  files: [
    'fas fa-file', 'fas fa-file-alt', 'fas fa-file-archive', 'fas fa-file-audio',
    'fas fa-file-code', 'fas fa-file-excel', 'fas fa-file-image', 'fas fa-file-pdf',
    'fas fa-file-powerpoint', 'fas fa-file-video', 'fas fa-file-word', 'fas fa-folder',
    'fas fa-folder-open', 'fas fa-folder-plus', 'fas fa-folder-minus', 'fas fa-archive',
    'fas fa-clipboard', 'fas fa-clipboard-list', 'fas fa-paste', 'fas fa-copy',
  ],
  users: [
    'fas fa-user', 'fas fa-user-alt', 'fas fa-user-circle', 'fas fa-user-plus',
    'fas fa-user-minus', 'fas fa-user-edit', 'fas fa-user-lock', 'fas fa-user-tag',
    'fas fa-users', 'fas fa-users-cog', 'fas fa-user-friends', 'fas fa-user-shield',
    'fas fa-id-card', 'fas fa-id-badge', 'fas fa-address-card', 'fas fa-address-book',
    'fas fa-crown', 'fas fa-user-tie', 'fas fa-user-graduate', 'fas fa-user-ninja',
  ],
  web: [
    'fas fa-globe', 'fas fa-globe-americas', 'fas fa-globe-asia', 'fas fa-globe-europe',
    'fas fa-wifi', 'fas fa-signal', 'fas fa-network-wired', 'fas fa-network-wired',
    'fas fa-server', 'fas fa-database', 'fas fa-cloud', 'fas fa-cloud-upload-alt',
    'fas fa-cloud-download-alt', 'fas fa-cloud-meatball', 'fas fa-code', 'fas fa-code-branch',
    'fas fa-terminal', 'fas fa-laptop-code', 'fas fa-browser', 'fas fa-internet-explorer',
  ],
}

const materialIcons = [
  'home', 'person', 'settings', 'search', 'favorite', 'star', 'check', 'close',
  'add', 'remove', 'edit', 'delete', 'save', 'download', 'upload', 'share',
  'link', 'image', 'videocam', 'music_note', 'book', 'description', 'folder',
  'storage', 'dns', 'cloud', 'lock', 'lock_open', 'vpn_key', 'security',
  'notifications', 'email', 'comment', 'chat', 'phone', 'camera', 'location_on',
  'language', 'wifi', 'bluetooth', 'code', 'terminal', 'computer', 'laptop',
  'phone_android', 'tablet', 'watch', 'headset', 'mic', 'volume_up', 'play_arrow',
  'pause', 'stop', 'skip_next', 'skip_previous', 'fast_forward', 'fast_rewind',
  'arrow_upward', 'arrow_downward', 'arrow_back', 'arrow_forward', 'expand_more',
  'expand_less', 'chevron_right', 'chevron_left', 'more_vert', 'more_horiz',
  'menu', 'apps', 'dashboard', 'widgets', 'view_list', 'view_module', 'grid_view',
  'refresh', 'sync', 'undo', 'redo', 'content_copy', 'content_paste', 'content_cut',
  'visibility', 'visibility_off', 'visibility', 'info', 'warning', 'error', 'help',
  'lightbulb', 'flash_on', 'power', 'battery_full', 'battery_alert', 'access_time',
  'schedule', 'today', 'event', 'calendar_today', 'date_range', 'history',
  'shopping_cart', 'shopping_bag', 'store', 'local_mall', 'credit_card', 'payment',
  'attach_money', 'monetization_on', 'account_balance', 'account_balance_wallet',
  'trending_up', 'trending_down', 'show_chart', 'bar_chart', 'pie_chart', 'analytics',
]

const heroiconsList = [
  'home', 'user', 'cog', 'search', 'heart', 'star', 'check', 'x',
  'plus', 'minus', 'pencil', 'trash', 'save', 'download', 'upload', 'share',
  'link', 'photograph', 'video-camera', 'music-note', 'book-open', 'document', 'folder',
  'database', 'server', 'cloud', 'lock-closed', 'lock-open', 'key', 'shield-check',
  'bell', 'mail', 'chat', 'phone', 'camera', 'location-marker', 'globe',
  'wifi', 'code', 'terminal', 'desktop-computer', 'laptop', 'device-mobile',
  'chip', 'cpu', 'lightning-bolt', 'fire', 'sparkles', 'sun', 'moon',
  'arrow-up', 'arrow-down', 'arrow-left', 'arrow-right', 'chevron-up', 'chevron-down',
  'chevron-left', 'chevron-right', 'menu', 'dots-vertical', 'dots-horizontal',
  'refresh', 'reply', 'eye', 'eye-off', 'information-circle', 'exclamation', 'question-mark-circle',
  'chart-bar', 'chart-pie', 'trending-up', 'currency-dollar', 'shopping-cart', 'gift',
  'tag', 'bookmark', 'flag', 'thumb-up', 'thumb-down', 'chat-alt-2', 'annotation',
]

const iconType = computed(() => {
  if (!props.modelValue) return null
  if (props.modelValue.startsWith('fas ') || props.modelValue.startsWith('fab ') || props.modelValue.startsWith('far ')) {
    return 'fontawesome'
  }
  if (materialIcons.includes(props.modelValue)) {
    return 'material'
  }
  if (heroiconsList.includes(props.modelValue)) {
    return 'heroicon'
  }
  return 'emoji'
})

const filteredEmojis = computed(() => {
  const categoryEmojis = emojis[activeEmojiCategory.value] || []
  if (!searchQuery.value) return categoryEmojis
  return categoryEmojis.filter(() => true)
})

const filteredFaIcons = computed(() => {
  const categoryIcons = faIcons[activeFaCategory.value] || []
  if (!searchQuery.value) return categoryIcons
  return categoryIcons.filter(icon => 
    icon.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const filteredMaterialIcons = computed(() => {
  if (!searchQuery.value) return materialIcons
  return materialIcons.filter(icon => 
    icon.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const filteredHeroicons = computed(() => {
  if (!searchQuery.value) return heroiconsList
  return heroiconsList.filter(icon => 
    icon.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const pickerStyle = computed(() => {
  return {
    top: `${pickerPosition.value.top}px`,
    left: `${pickerPosition.value.left}px`
  }
})

const updatePickerPosition = () => {
  if (!triggerRef.value) return
  
  const rect = triggerRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth
  const pickerHeight = 500
  const pickerWidth = 384
  const margin = 8
  
  let top = rect.bottom + margin
  let left = rect.left
  
  if (top + pickerHeight > viewportHeight) {
    top = rect.top - pickerHeight - margin
  }
  
  if (top < margin) {
    top = margin
  }
  
  if (left + pickerWidth > viewportWidth) {
    left = viewportWidth - pickerWidth - margin
  }
  
  if (left < margin) {
    left = margin
  }
  
  pickerPosition.value = { top, left }
}

const getIconName = (icon: string) => {
  const parts = icon.split(' ')
  return parts[parts.length - 1].replace('fa-', '')
}

const getHeroicon = (name: string) => {
  const iconPaths: Record<string, string> = {
    home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
    user: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    cog: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    heart: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    star: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
    check: 'M5 13l4 4L19 7',
    x: 'M6 18L18 6M6 6l12 12',
    plus: 'M12 4v16m8-8H4',
    minus: 'M20 12H4',
    pencil: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z',
    trash: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
    save: 'M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4',
    download: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
    upload: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
    share: 'M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z',
    link: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
  }
  
  const path = iconPaths[name] || 'M4 6h16M4 12h16M4 18h16'
  
  return {
    render() {
      return h('svg', {
        fill: 'none',
        stroke: 'currentColor',
        viewBox: '0 0 24 24',
        xmlns: 'http://www.w3.org/2000/svg'
      }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: path
        })
      ])
    }
  }
}

const togglePicker = () => {
  if (!showPicker.value) {
    updatePickerPosition()
  }
  showPicker.value = !showPicker.value
}

const selectIcon = (icon: string, _type: string) => {
  emit('update:modelValue', icon)
}

const clearIcon = () => {
  emit('update:modelValue', undefined)
  showPicker.value = false
}

const handleDragStart = (event: MouseEvent) => {
  if ((event.target as HTMLElement).tagName === 'BUTTON') return
  
  isDragging.value = true
  dragStart.value = {
    x: event.clientX,
    y: event.clientY,
    top: pickerPosition.value.top,
    left: pickerPosition.value.left
  }
  
  event.preventDefault()
}

const handleDragMove = (event: MouseEvent) => {
  if (!isDragging.value) return
  
  const deltaX = event.clientX - dragStart.value.x
  const deltaY = event.clientY - dragStart.value.y
  
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth
  const pickerHeight = 500
  const pickerWidth = 384
  const margin = 8
  
  let newTop = dragStart.value.top + deltaY
  let newLeft = dragStart.value.left + deltaX
  
  newTop = Math.max(margin, Math.min(newTop, viewportHeight - pickerHeight - margin))
  newLeft = Math.max(margin, Math.min(newLeft, viewportWidth - pickerWidth - margin))
  
  pickerPosition.value = { top: newTop, left: newLeft }
}

const handleDragEnd = () => {
  isDragging.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (isDragging.value) return
  
  const target = event.target as HTMLElement
  if (!target.closest('.icon-picker')) {
    showPicker.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
})
</script>
