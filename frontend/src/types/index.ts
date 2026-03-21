export interface Token {
  access_token: string
  token_type: string
  refresh_token?: string
  expires_in?: number
}

export interface SessionInfo {
  id: number
  ip_address?: string
  user_agent?: string
  last_used_at?: string
  created_at?: string
  is_current: boolean
}

export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  avatar_type?: string
  avatar_url?: string
  oauth_avatar_url?: string
  avatar_gradient?: string[]
  bio?: string
  is_admin: boolean
  is_verified: boolean
  created_at: string
}

export interface Category {
  id: number
  name: string
  slug: string
  description?: string
  icon?: string
  color: string
  order: number
  article_count: number
  created_at: string
}

export interface Tag {
  id: number
  name: string
  slug: string
  color: string
  article_count: number
  created_at: string
}

export interface Article {
  id: number
  title: string
  slug: string
  summary?: string
  content: string
  cover_image?: string
  is_published: boolean
  is_featured: boolean
  is_pinned: boolean
  view_count: number
  like_count: number
  reading_time: number
  category_id?: number
  author_id?: number
  created_at: string
  updated_at: string
  published_at?: string
  category?: Category
  tags: Tag[]
  author?: User
  is_liked?: boolean
}

export interface ArticleListItem {
  id: number
  title: string
  slug: string
  summary?: string
  cover_image?: string
  is_published: boolean
  is_featured: boolean
  is_pinned: boolean
  view_count: number
  like_count: number
  comment_count: number
  reading_time: number
  created_at: string
  published_at?: string
  category?: Category
  tags: Tag[]
  is_liked?: boolean
}

export interface LikeResponse {
  article_id: number
  like_count: number
  is_liked: boolean
}

export interface Resource {
  id: number
  title: string
  description?: string
  url: string
  icon?: string
  category: string
  is_active: boolean
  order: number
  created_at: string
}

export interface Comment {
  id: number
  content: string
  user_id?: number
  author_name?: string
  author_email?: string
  author_url?: string
  author_avatar_type?: string
  author_avatar_url?: string
  author_avatar_gradient?: string[]
  article_id: number
  parent_id?: number
  status: 'pending' | 'approved' | 'rejected'
  is_deleted?: boolean
  deleted_by?: 'user' | 'admin'
  reply_to_user_id?: number
  reply_to_user_name?: string
  reply_to_user_avatar_type?: string
  reply_to_user_avatar_url?: string
  reply_to_user_avatar_gradient?: string[]
  created_at: string
  replies: Comment[]
}

export interface AdminComment {
  id: number
  content: string
  user_id?: number
  author_name?: string
  author_email?: string
  author_url?: string
  author_avatar_type?: string
  author_avatar_url?: string
  author_avatar_gradient?: string[]
  article_id: number
  article_title?: string
  article_slug?: string
  parent_id?: number
  status: 'pending' | 'approved' | 'rejected'
  is_deleted?: boolean
  deleted_by?: 'user' | 'admin'
  reply_to_user_id?: number
  reply_to_user_name?: string
  reply_to_user_avatar_type?: string
  reply_to_user_avatar_url?: string
  reply_to_user_avatar_gradient?: string[]
  created_at: string
}

export interface CommentAuditLog {
  id: number
  comment_id: number
  operator_id?: number
  operator_name?: string
  old_status?: string
  new_status: string
  reason?: string
  created_at: string
}

export interface CommentAuditRequest {
  status: 'pending' | 'approved' | 'rejected'
  reason?: string
}

export interface BatchAuditRequest {
  comment_ids: number[]
  status: 'pending' | 'approved' | 'rejected'
  reason?: string
}

export interface CommentCreate {
  content: string
  article_id: number
  parent_id?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SiteConfig {
  id: number
  key: string
  value?: string
  description?: string
  updated_at: string
}

export interface Profile {
  id: number
  name: string
  alias?: string
  slogan?: string
  tags: string[]
  avatar?: string
  bio?: string
  tech_stack: TechStackItem[]
  journey: JourneyItem[]
  education?: Education
  exploration_areas: string[]
  social_github?: string
  social_blog?: string
  social_email?: string
  updated_at: string
}

export interface TechStackItem {
  category: string
  items: string[]
}

export interface JourneyItem {
  period: string
  company: string
  position: string
  achievements: string
}

export interface Education {
  period: string
  school: string
  major: string
  degree: string
}

export interface SocialLinks {
  github: string
  blog: string
  email: string
}
