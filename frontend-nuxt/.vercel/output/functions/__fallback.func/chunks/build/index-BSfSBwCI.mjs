import { defineComponent, computed, withAsyncContext, watchEffect, resolveComponent, mergeProps, unref, ref, toValue, getCurrentInstance, onServerPrefetch, shallowRef, nextTick, toRef, useSSRContext } from 'vue';
import { ssrRenderAttrs, ssrRenderComponent, ssrRenderClass, ssrRenderList } from 'vue/server-renderer';
import { e as useRoute, f as useRouter, g as useAuthStore, h as useHead, d as defineStore, b as useRuntimeConfig, u as useNuxtApp, a as asyncDataDefaults, c as createError } from './server.mjs';
import axios from 'axios';
import '../_/nitro.mjs';
import 'node:http';
import 'node:https';
import 'node:events';
import 'node:buffer';
import 'node:fs';
import 'node:path';
import 'node:crypto';
import '../routes/renderer.mjs';
import 'vue-bundle-renderer/runtime';
import 'unhead/server';
import 'devalue';
import 'unhead/utils';
import 'unhead/plugins';
import 'vue-router';

//#region src/index.ts
const DEBOUNCE_DEFAULTS = { trailing: true };
/**
Debounce functions
@param fn - Promise-returning/async function to debounce.
@param wait - Milliseconds to wait before calling `fn`. Default value is 25ms
@returns A function that delays calling `fn` until after `wait` milliseconds have elapsed since the last time it was called.
@example
```
import { debounce } from 'perfect-debounce';
const expensiveCall = async input => input;
const debouncedFn = debounce(expensiveCall, 200);
for (const number of [1, 2, 3]) {
console.log(await debouncedFn(number));
}
//=> 1
//=> 2
//=> 3
```
*/
function debounce(fn, wait = 25, options = {}) {
	options = {
		...DEBOUNCE_DEFAULTS,
		...options
	};
	if (!Number.isFinite(wait)) throw new TypeError("Expected `wait` to be a finite number");
	let leadingValue;
	let timeout;
	let resolveList = [];
	let currentPromise;
	let trailingArgs;
	const applyFn = (_this, args) => {
		currentPromise = _applyPromised(fn, _this, args);
		currentPromise.finally(() => {
			currentPromise = null;
			if (options.trailing && trailingArgs && !timeout) {
				const promise = applyFn(_this, trailingArgs);
				trailingArgs = null;
				return promise;
			}
		});
		return currentPromise;
	};
	const debounced = function(...args) {
		if (options.trailing) trailingArgs = args;
		if (currentPromise) return currentPromise;
		return new Promise((resolve) => {
			const shouldCallNow = !timeout && options.leading;
			clearTimeout(timeout);
			timeout = setTimeout(() => {
				timeout = null;
				const promise = options.leading ? leadingValue : applyFn(this, args);
				trailingArgs = null;
				for (const _resolve of resolveList) _resolve(promise);
				resolveList = [];
			}, wait);
			if (shouldCallNow) {
				leadingValue = applyFn(this, args);
				resolve(leadingValue);
			} else resolveList.push(resolve);
		});
	};
	const _clearTimeout = (timer) => {
		if (timer) {
			clearTimeout(timer);
			timeout = null;
		}
	};
	debounced.isPending = () => !!timeout;
	debounced.cancel = () => {
		_clearTimeout(timeout);
		resolveList = [];
		trailingArgs = null;
	};
	debounced.flush = () => {
		_clearTimeout(timeout);
		if (!trailingArgs || currentPromise) return;
		const args = trailingArgs;
		trailingArgs = null;
		return applyFn(this, args);
	};
	return debounced;
}
async function _applyPromised(fn, _this, args) {
	return await fn.apply(_this, args);
}

const isDefer = (dedupe) => dedupe === "defer" || dedupe === false;
function useAsyncData(...args) {
  var _a, _b, _c, _d, _e, _f, _g;
  const autoKey = typeof args[args.length - 1] === "string" ? args.pop() : void 0;
  if (_isAutoKeyNeeded(args[0], args[1])) {
    args.unshift(autoKey);
  }
  let [_key, _handler, options = {}] = args;
  const key = computed(() => toValue(_key));
  if (typeof key.value !== "string") {
    throw new TypeError("[nuxt] [useAsyncData] key must be a string.");
  }
  if (typeof _handler !== "function") {
    throw new TypeError("[nuxt] [useAsyncData] handler must be a function.");
  }
  const nuxtApp = useNuxtApp();
  (_a = options.server) != null ? _a : options.server = true;
  (_b = options.default) != null ? _b : options.default = getDefault;
  (_c = options.getCachedData) != null ? _c : options.getCachedData = getDefaultCachedData;
  (_d = options.lazy) != null ? _d : options.lazy = false;
  (_e = options.immediate) != null ? _e : options.immediate = true;
  (_f = options.deep) != null ? _f : options.deep = asyncDataDefaults.deep;
  (_g = options.dedupe) != null ? _g : options.dedupe = "cancel";
  options._functionName || "useAsyncData";
  nuxtApp._asyncData[key.value];
  function createInitialFetch() {
    var _a2;
    const initialFetchOptions = { cause: "initial", dedupe: options.dedupe };
    if (!((_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2._init)) {
      initialFetchOptions.cachedData = options.getCachedData(key.value, nuxtApp, { cause: "initial" });
      nuxtApp._asyncData[key.value] = createAsyncData(nuxtApp, key.value, _handler, options, initialFetchOptions.cachedData);
    }
    return () => nuxtApp._asyncData[key.value].execute(initialFetchOptions);
  }
  const initialFetch = createInitialFetch();
  const asyncData = nuxtApp._asyncData[key.value];
  asyncData._deps++;
  const fetchOnServer = options.server !== false && nuxtApp.payload.serverRendered;
  if (fetchOnServer && options.immediate) {
    const promise = initialFetch();
    if (getCurrentInstance()) {
      onServerPrefetch(() => promise);
    } else {
      nuxtApp.hook("app:created", async () => {
        await promise;
      });
    }
  }
  const asyncReturn = {
    data: writableComputedRef(() => {
      var _a2;
      return (_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2.data;
    }),
    pending: writableComputedRef(() => {
      var _a2;
      return (_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2.pending;
    }),
    status: writableComputedRef(() => {
      var _a2;
      return (_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2.status;
    }),
    error: writableComputedRef(() => {
      var _a2;
      return (_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2.error;
    }),
    refresh: (...args2) => {
      var _a2;
      if (!((_a2 = nuxtApp._asyncData[key.value]) == null ? void 0 : _a2._init)) {
        const initialFetch2 = createInitialFetch();
        return initialFetch2();
      }
      return nuxtApp._asyncData[key.value].execute(...args2);
    },
    execute: (...args2) => asyncReturn.refresh(...args2),
    clear: () => {
      const entry = nuxtApp._asyncData[key.value];
      if (entry == null ? void 0 : entry._abortController) {
        try {
          entry._abortController.abort(new DOMException("AsyncData aborted by user.", "AbortError"));
        } finally {
          entry._abortController = void 0;
        }
      }
      clearNuxtDataByKey(nuxtApp, key.value);
    }
  };
  const asyncDataPromise = Promise.resolve(nuxtApp._asyncDataPromises[key.value]).then(() => asyncReturn);
  Object.assign(asyncDataPromise, asyncReturn);
  Object.defineProperties(asyncDataPromise, {
    then: { enumerable: true, value: asyncDataPromise.then.bind(asyncDataPromise) },
    catch: { enumerable: true, value: asyncDataPromise.catch.bind(asyncDataPromise) },
    finally: { enumerable: true, value: asyncDataPromise.finally.bind(asyncDataPromise) }
  });
  return asyncDataPromise;
}
function writableComputedRef(getter) {
  return computed({
    get() {
      var _a;
      return (_a = getter()) == null ? void 0 : _a.value;
    },
    set(value) {
      const ref2 = getter();
      if (ref2) {
        ref2.value = value;
      }
    }
  });
}
function _isAutoKeyNeeded(keyOrFetcher, fetcher) {
  if (typeof keyOrFetcher === "string") {
    return false;
  }
  if (typeof keyOrFetcher === "object" && keyOrFetcher !== null) {
    return false;
  }
  if (typeof keyOrFetcher === "function" && typeof fetcher === "function") {
    return false;
  }
  return true;
}
function clearNuxtDataByKey(nuxtApp, key) {
  if (key in nuxtApp.payload.data) {
    nuxtApp.payload.data[key] = void 0;
  }
  if (key in nuxtApp.payload._errors) {
    nuxtApp.payload._errors[key] = asyncDataDefaults.errorValue;
  }
  if (nuxtApp._asyncData[key]) {
    nuxtApp._asyncData[key].data.value = void 0;
    nuxtApp._asyncData[key].error.value = asyncDataDefaults.errorValue;
    {
      nuxtApp._asyncData[key].pending.value = false;
    }
    nuxtApp._asyncData[key].status.value = "idle";
  }
  if (key in nuxtApp._asyncDataPromises) {
    nuxtApp._asyncDataPromises[key] = void 0;
  }
}
function pick(obj, keys) {
  const newObj = {};
  for (const key of keys) {
    newObj[key] = obj[key];
  }
  return newObj;
}
function createAsyncData(nuxtApp, key, _handler, options, initialCachedData) {
  var _a, _b;
  (_b = (_a = nuxtApp.payload._errors)[key]) != null ? _b : _a[key] = asyncDataDefaults.errorValue;
  const hasCustomGetCachedData = options.getCachedData !== getDefaultCachedData;
  const handler = _handler ;
  const _ref = options.deep ? ref : shallowRef;
  const hasCachedData = initialCachedData != null;
  const unsubRefreshAsyncData = nuxtApp.hook("app:data:refresh", async (keys) => {
    if (!keys || keys.includes(key)) {
      await asyncData.execute({ cause: "refresh:hook" });
    }
  });
  const asyncData = {
    data: _ref(hasCachedData ? initialCachedData : options.default()),
    pending: shallowRef(!hasCachedData),
    error: toRef(nuxtApp.payload._errors, key),
    status: shallowRef("idle"),
    execute: (...args) => {
      var _a2, _b2;
      const [_opts, newValue = void 0] = args;
      const opts = _opts && newValue === void 0 && typeof _opts === "object" ? _opts : {};
      if (nuxtApp._asyncDataPromises[key]) {
        if (isDefer((_a2 = opts.dedupe) != null ? _a2 : options.dedupe)) {
          return nuxtApp._asyncDataPromises[key];
        }
      }
      if (opts.cause === "initial" || nuxtApp.isHydrating) {
        const cachedData = "cachedData" in opts ? opts.cachedData : options.getCachedData(key, nuxtApp, { cause: (_b2 = opts.cause) != null ? _b2 : "refresh:manual" });
        if (cachedData != null) {
          nuxtApp.payload.data[key] = asyncData.data.value = cachedData;
          asyncData.error.value = asyncDataDefaults.errorValue;
          asyncData.status.value = "success";
          return Promise.resolve(cachedData);
        }
      }
      {
        asyncData.pending.value = true;
      }
      if (asyncData._abortController) {
        asyncData._abortController.abort(new DOMException("AsyncData request cancelled by deduplication", "AbortError"));
      }
      asyncData._abortController = new AbortController();
      asyncData.status.value = "pending";
      const cleanupController = new AbortController();
      const promise = new Promise(
        (resolve, reject) => {
          var _a3, _b3;
          try {
            const timeout = (_a3 = opts.timeout) != null ? _a3 : options.timeout;
            const mergedSignal = mergeAbortSignals([(_b3 = asyncData._abortController) == null ? void 0 : _b3.signal, opts == null ? void 0 : opts.signal], cleanupController.signal, timeout);
            if (mergedSignal.aborted) {
              const reason = mergedSignal.reason;
              reject(reason instanceof Error ? reason : new DOMException(String(reason != null ? reason : "Aborted"), "AbortError"));
              return;
            }
            mergedSignal.addEventListener("abort", () => {
              const reason = mergedSignal.reason;
              reject(reason instanceof Error ? reason : new DOMException(String(reason != null ? reason : "Aborted"), "AbortError"));
            }, { once: true, signal: cleanupController.signal });
            return Promise.resolve(handler(nuxtApp, { signal: mergedSignal })).then(resolve, reject);
          } catch (err) {
            reject(err);
          }
        }
      ).then(async (_result) => {
        let result = _result;
        if (options.transform) {
          result = await options.transform(_result);
        }
        if (options.pick) {
          result = pick(result, options.pick);
        }
        nuxtApp.payload.data[key] = result;
        asyncData.data.value = result;
        asyncData.error.value = asyncDataDefaults.errorValue;
        asyncData.status.value = "success";
      }).catch((error) => {
        var _a3;
        if (nuxtApp._asyncDataPromises[key] && nuxtApp._asyncDataPromises[key] !== promise) {
          return nuxtApp._asyncDataPromises[key];
        }
        if ((_a3 = asyncData._abortController) == null ? void 0 : _a3.signal.aborted) {
          return nuxtApp._asyncDataPromises[key];
        }
        if (typeof DOMException !== "undefined" && error instanceof DOMException && error.name === "AbortError") {
          asyncData.status.value = "idle";
          return nuxtApp._asyncDataPromises[key];
        }
        asyncData.error.value = createError(error);
        asyncData.data.value = unref(options.default());
        asyncData.status.value = "error";
      }).finally(() => {
        {
          asyncData.pending.value = false;
        }
        cleanupController.abort();
        delete nuxtApp._asyncDataPromises[key];
      });
      nuxtApp._asyncDataPromises[key] = promise;
      return nuxtApp._asyncDataPromises[key];
    },
    _execute: debounce((...args) => asyncData.execute(...args), 0, { leading: true }),
    _default: options.default,
    _deps: 0,
    _init: true,
    _hash: void 0,
    _off: () => {
      var _a2;
      unsubRefreshAsyncData();
      if ((_a2 = nuxtApp._asyncData[key]) == null ? void 0 : _a2._init) {
        nuxtApp._asyncData[key]._init = false;
      }
      if (!hasCustomGetCachedData) {
        nextTick(() => {
          var _a3;
          if (!((_a3 = nuxtApp._asyncData[key]) == null ? void 0 : _a3._init)) {
            clearNuxtDataByKey(nuxtApp, key);
            asyncData.execute = () => Promise.resolve();
            asyncData.data.value = asyncDataDefaults.value;
          }
        });
      }
    }
  };
  return asyncData;
}
const getDefault = () => asyncDataDefaults.value;
const getDefaultCachedData = (key, nuxtApp, ctx) => {
  if (nuxtApp.isHydrating) {
    return nuxtApp.payload.data[key];
  }
  if (ctx.cause !== "refresh:manual" && ctx.cause !== "refresh:hook") {
    return nuxtApp.static.data[key];
  }
};
function mergeAbortSignals(signals, cleanupSignal, timeout) {
  var _a, _b, _c;
  const list = signals.filter((s) => !!s);
  if (typeof timeout === "number" && timeout >= 0) {
    const timeoutSignal = (_a = AbortSignal.timeout) == null ? void 0 : _a.call(AbortSignal, timeout);
    if (timeoutSignal) {
      list.push(timeoutSignal);
    }
  }
  if (AbortSignal.any) {
    return AbortSignal.any(list);
  }
  const controller = new AbortController();
  for (const sig of list) {
    if (sig.aborted) {
      const reason = (_b = sig.reason) != null ? _b : new DOMException("Aborted", "AbortError");
      try {
        controller.abort(reason);
      } catch {
        controller.abort();
      }
      return controller.signal;
    }
  }
  const onAbort = () => {
    var _a2;
    const abortedSignal = list.find((s) => s.aborted);
    const reason = (_a2 = abortedSignal == null ? void 0 : abortedSignal.reason) != null ? _a2 : new DOMException("Aborted", "AbortError");
    try {
      controller.abort(reason);
    } catch {
      controller.abort();
    }
  };
  for (const sig of list) {
    (_c = sig.addEventListener) == null ? void 0 : _c.call(sig, "abort", onAbort, { once: true, signal: cleanupSignal });
  }
  return controller.signal;
}
const useBlogStore = defineStore("blog", () => {
  const articles = ref([]);
  const categories = ref([]);
  const tags = ref([]);
  const announcements = ref([]);
  const pagination = ref({
    page: 1,
    pageSize: 6,
    total: 0,
    totalPages: 0
  });
  const setArticles = (data) => {
    articles.value = data;
  };
  const setCategories = (data) => {
    categories.value = data;
  };
  const setTags = (data) => {
    tags.value = data;
  };
  const setAnnouncements = (data) => {
    announcements.value = data;
  };
  const setPagination = (data) => {
    pagination.value = data;
  };
  const setArticlesPaginated = (data) => {
    articles.value = data.items;
    pagination.value = {
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
      totalPages: data.total_pages
    };
  };
  return {
    articles,
    categories,
    tags,
    announcements,
    pagination,
    setArticles,
    setCategories,
    setTags,
    setAnnouncements,
    setPagination,
    setArticlesPaginated
  };
});
const useSiteConfigStore = defineStore("siteConfig", () => {
  const configs = ref({});
  const githubStats = ref(null);
  const siteName = computed(() => configs.value.site_name || "Futuristic Blog");
  const siteDescription = computed(() => configs.value.site_description || "");
  const siteKeywords = computed(() => configs.value.site_keywords || "");
  const siteLogo = computed(() => configs.value.site_logo || "");
  const siteFavicon = computed(() => configs.value.site_favicon || "");
  const socialLinks = computed(() => {
    try {
      return JSON.parse(configs.value.social_links || "[]");
    } catch {
      return [];
    }
  });
  const mobileArticleLayout = computed(() => configs.value.mobile_article_layout || "grid");
  const setConfigs = (data) => {
    const configMap = {};
    data.forEach((config2) => {
      configMap[config2.key] = config2.value;
    });
    configs.value = configMap;
  };
  const setGithubStats = (data) => {
    githubStats.value = data;
  };
  const getConfig = (key, defaultValue = "") => {
    return configs.value[key] || defaultValue;
  };
  return {
    configs,
    githubStats,
    siteName,
    siteDescription,
    siteKeywords,
    siteLogo,
    siteFavicon,
    socialLinks,
    mobileArticleLayout,
    setConfigs,
    setGithubStats,
    getConfig
  };
});
const useUserInteractionStore = defineStore("userInteraction", () => {
  const likedArticleIds = ref(/* @__PURE__ */ new Set());
  const bookmarkedArticleIds = ref(/* @__PURE__ */ new Set());
  const setLikedIds = (ids) => {
    likedArticleIds.value = new Set(ids);
  };
  const setBookmarkedIds = (ids) => {
    bookmarkedArticleIds.value = new Set(ids);
  };
  const isLiked = (articleId) => likedArticleIds.value.has(articleId);
  const isBookmarked = (articleId) => bookmarkedArticleIds.value.has(articleId);
  const toggleLike = (articleId) => {
    if (likedArticleIds.value.has(articleId)) {
      likedArticleIds.value.delete(articleId);
      return false;
    } else {
      likedArticleIds.value.add(articleId);
      return true;
    }
  };
  const toggleBookmark = (articleId) => {
    if (bookmarkedArticleIds.value.has(articleId)) {
      bookmarkedArticleIds.value.delete(articleId);
      return false;
    } else {
      bookmarkedArticleIds.value.add(articleId);
      return true;
    }
  };
  return {
    likedArticleIds,
    bookmarkedArticleIds,
    setLikedIds,
    setBookmarkedIds,
    isLiked,
    isBookmarked,
    toggleLike,
    toggleBookmark
  };
});
const config = useRuntimeConfig();
const client = axios.create({
  baseURL: config.public.apiBase,
  timeout: 3e4,
  headers: {
    "Content-Type": "application/json"
  }
});
client.interceptors.request.use(
  (config2) => {
    return config2;
  },
  (error) => Promise.reject(error)
);
client.interceptors.response.use(
  (response) => response,
  (error) => {
    var _a;
    if (((_a = error.response) == null ? void 0 : _a.status) === 401) ;
    return Promise.reject(error);
  }
);
const useApi = () => {
  const get = (url, config2) => client.get(url, config2).then((res) => res.data);
  const post = (url, data, config2) => client.post(url, data, config2).then((res) => res.data);
  const put = (url, data, config2) => client.put(url, data, config2).then((res) => res.data);
  const del = (url, config2) => client.delete(url, config2).then((res) => res.data);
  return { client, get, post, put, del };
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "index",
  __ssrInlineRender: true,
  async setup(__props) {
    let __temp, __restore;
    const route = useRoute();
    const router = useRouter();
    const config2 = useRuntimeConfig();
    const authStore = useAuthStore();
    const blogStore = useBlogStore();
    const siteConfigStore = useSiteConfigStore();
    const userInteractionStore = useUserInteractionStore();
    const page = computed(() => parseInt(route.query.page) || 1);
    const isStackedLayout = computed(() => siteConfigStore.mobileArticleLayout === "stacked");
    const apiBase = config2.public.apiBase;
    const { data, pending, error } = ([__temp, __restore] = withAsyncContext(() => useAsyncData(
      () => `home-${page.value}`,
      () => $fetch(`${apiBase}/init`, {
        params: {
          page: page.value,
          page_size: 6,
          featured_page_size: 5
        }
      }),
      {
        server: false,
        lazy: true
      }
    )), __temp = await __temp, __restore(), __temp);
    const articles = computed(() => {
      var _a, _b;
      if (!((_b = (_a = data.value) == null ? void 0 : _a.articles) == null ? void 0 : _b.items)) return [];
      const items = data.value.articles.items;
      return items.map((article) => ({
        ...article,
        is_liked: userInteractionStore.isLiked(article.id),
        is_bookmarked: userInteractionStore.isBookmarked(article.id)
      }));
    });
    const featuredArticles = computed(() => {
      var _a, _b;
      if (!((_b = (_a = data.value) == null ? void 0 : _a.featured_articles) == null ? void 0 : _b.items)) return [];
      return data.value.featured_articles.items;
    });
    const announcements = computed(() => {
      var _a;
      return ((_a = data.value) == null ? void 0 : _a.announcements) || [];
    });
    const githubStats = computed(() => {
      var _a;
      return ((_a = data.value) == null ? void 0 : _a.github_stats) || null;
    });
    const pagination = computed(() => {
      var _a;
      if (!((_a = data.value) == null ? void 0 : _a.articles)) return { page: 1, totalPages: 1, total: 0 };
      return {
        page: data.value.articles.page,
        totalPages: data.value.articles.total_pages,
        total: data.value.articles.total
      };
    });
    watchEffect(() => {
      if (data.value) {
        if (data.value.site_config) {
          siteConfigStore.setConfigs(data.value.site_config);
        }
        if (data.value.categories) {
          blogStore.setCategories(data.value.categories);
        }
        if (data.value.tags) {
          blogStore.setTags(data.value.tags);
        }
        if (data.value.github_stats) {
          siteConfigStore.setGithubStats(data.value.github_stats);
        }
        if (authStore.isAuthenticated && data.value.liked_article_ids) {
          userInteractionStore.setLikedIds(data.value.liked_article_ids);
        }
        if (authStore.isAuthenticated && data.value.bookmarked_article_ids) {
          userInteractionStore.setBookmarkedIds(data.value.bookmarked_article_ids);
        }
      }
    });
    useHead({
      title: computed(() => `${siteConfigStore.siteName} - \u9996\u9875`),
      meta: [
        { name: "description", content: siteConfigStore.siteDescription },
        { name: "keywords", content: siteConfigStore.siteKeywords }
      ]
    });
    const handleLike = async (article) => {
      if (!authStore.isAuthenticated) {
        router.push("/login");
        return;
      }
      const { post } = useApi();
      try {
        const result = await post(`/likes/toggle`, { article_id: article.id });
        if (result) {
          userInteractionStore.toggleLike(article.id);
          article.is_liked = result.is_liked;
          article.like_count = result.like_count;
        }
      } catch (err) {
        console.error("Failed to toggle like:", err);
      }
    };
    const handleBookmark = async (article) => {
      if (!authStore.isAuthenticated) {
        router.push("/login");
        return;
      }
      const { post } = useApi();
      try {
        const result = await post(`/bookmarks/toggle`, { article_id: article.id });
        if (result) {
          userInteractionStore.toggleBookmark(article.id);
          article.is_bookmarked = result.is_bookmarked;
        }
      } catch (err) {
        console.error("Failed to toggle bookmark:", err);
      }
    };
    const handlePageChange = (newPage) => {
      router.push({ query: { page: newPage } });
    };
    return (_ctx, _push, _parent, _attrs) => {
      const _component_LeftSidebar = resolveComponent("LeftSidebar");
      const _component_FeaturedSlider = resolveComponent("FeaturedSlider");
      const _component_AnnouncementBanner = resolveComponent("AnnouncementBanner");
      const _component_Icon = resolveComponent("Icon");
      const _component_ArticleCard = resolveComponent("ArticleCard");
      const _component_Pagination = resolveComponent("Pagination");
      const _component_BlogSidebar = resolveComponent("BlogSidebar");
      _push(`<div${ssrRenderAttrs(mergeProps({ class: "container mx-auto px-4 py-8" }, _attrs))}><div class="flex flex-col lg:flex-row gap-8"><div class="hidden lg:block w-64 flex-shrink-0">`);
      _push(ssrRenderComponent(_component_LeftSidebar, null, null, _parent));
      _push(`</div><div class="flex-1 min-w-0">`);
      if (unref(featuredArticles).length > 0) {
        _push(`<div class="mb-8">`);
        _push(ssrRenderComponent(_component_FeaturedSlider, { articles: unref(featuredArticles) }, null, _parent));
        _push(`</div>`);
      } else {
        _push(`<!---->`);
      }
      if (unref(announcements).length > 0) {
        _push(`<div class="mb-8">`);
        _push(ssrRenderComponent(_component_AnnouncementBanner, { announcements: unref(announcements) }, null, _parent));
        _push(`</div>`);
      } else {
        _push(`<!---->`);
      }
      _push(`<div class="mb-6"><h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">`);
      _push(ssrRenderComponent(_component_Icon, {
        name: "heroicons:document-text",
        class: "w-6 h-6 text-primary-500"
      }, null, _parent));
      _push(` \u6700\u65B0\u6587\u7AE0 </h2></div>`);
      if (unref(pending)) {
        _push(`<div class="flex justify-center py-12"><div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div></div>`);
      } else if (unref(error)) {
        _push(`<div class="text-center py-12"><p class="text-red-500">\u52A0\u8F7D\u5931\u8D25\uFF0C\u8BF7\u5237\u65B0\u9875\u9762\u91CD\u8BD5</p></div>`);
      } else if (unref(articles).length === 0) {
        _push(`<div class="text-center py-12"><p class="text-gray-500 dark:text-gray-400">\u6682\u65E0\u6587\u7AE0</p></div>`);
      } else {
        _push(`<!--[--><div class="${ssrRenderClass(unref(isStackedLayout) ? "flex flex-col gap-6" : "grid grid-cols-1 md:grid-cols-2 gap-6")}"><!--[-->`);
        ssrRenderList(unref(articles), (article) => {
          _push(ssrRenderComponent(_component_ArticleCard, {
            key: article.id,
            article,
            "is-stacked": unref(isStackedLayout),
            onLike: handleLike,
            onBookmark: handleBookmark
          }, null, _parent));
        });
        _push(`<!--]--></div><div class="mt-8">`);
        _push(ssrRenderComponent(_component_Pagination, {
          "current-page": unref(pagination).page,
          "total-pages": unref(pagination).totalPages,
          total: unref(pagination).total,
          onPageChange: handlePageChange
        }, null, _parent));
        _push(`</div><!--]-->`);
      }
      _push(`</div><div class="hidden xl:block w-80 flex-shrink-0">`);
      _push(ssrRenderComponent(_component_BlogSidebar, { "github-stats": unref(githubStats) }, null, _parent));
      _push(`</div></div></div>`);
    };
  }
});
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("pages/index.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};

export { _sfc_main as default };
//# sourceMappingURL=index-BSfSBwCI.mjs.map
