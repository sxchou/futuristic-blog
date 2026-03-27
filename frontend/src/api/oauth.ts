import apiClient from './client'

export interface OAuthProvider {
  id: number
  name: string
  display_name: string
  icon: string | null
  client_id: string | null
  client_secret: string | null
  redirect_uri: string | null
  authorize_url: string | null
  token_url: string | null
  userinfo_url: string | null
  scope: string | null
  is_enabled: boolean
  show_on_login: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface OAuthProviderResponse {
  id: number
  name: string
  display_name: string
  icon: string | null
  is_enabled: boolean
  show_on_login: boolean
  is_configured: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface OAuthProviderDetail extends OAuthProviderResponse {
  client_id: string | null
  redirect_uri: string | null
  authorize_url: string | null
  token_url: string | null
  userinfo_url: string | null
  scope: string | null
}

export interface OAuthProviderUpdate {
  display_name?: string
  icon?: string
  client_id?: string
  client_secret?: string
  redirect_uri?: string
  authorize_url?: string
  token_url?: string
  userinfo_url?: string
  scope?: string
  is_enabled?: boolean
  show_on_login?: boolean
  order?: number
}

export interface OAuthLoginResponse {
  authorize_url: string
  state: string
}

export interface OAuthCallbackResponse {
  access_token: string
  token_type: string
  refresh_token?: string
  expires_in?: number
  user: {
    id: number
    username: string
    email: string
    avatar: string | null
    is_admin: boolean
  }
  needs_email?: boolean
  temp_token?: string
}

export interface OAuthEmailVerifyResponse {
  message: string
  temp_token: string
}

export interface ResendVerificationResponse {
  message: string
  email: string
  delivery_time: string
  expires_at?: string
}

export interface PendingVerificationInfo {
  username: string
  has_email: boolean
  email?: string
  is_verified: boolean
  provider_name: string
  expires_at?: string
  is_expired?: boolean
}

export const oauthApi = {
  getProviders: async (): Promise<OAuthProviderResponse[]> => {
    const response = await apiClient.get<OAuthProviderResponse[]>('/oauth/providers')
    return response.data
  },

  getLoginProviders: async (): Promise<OAuthProviderResponse[]> => {
    const response = await apiClient.get<OAuthProviderResponse[]>('/oauth/providers/login')
    return response.data
  },

  getProvider: async (id: number): Promise<OAuthProviderDetail> => {
    const response = await apiClient.get<OAuthProviderDetail>(`/oauth/providers/${id}`)
    return response.data
  },

  updateProvider: async (id: number, data: Partial<OAuthProviderUpdate>): Promise<OAuthProviderDetail> => {
    const response = await apiClient.put<OAuthProviderDetail>(`/oauth/providers/${id}`, data)
    return response.data
  },

  getLoginUrl: async (provider: string): Promise<OAuthLoginResponse> => {
    const response = await apiClient.get<OAuthLoginResponse>(`/oauth/login/${provider}`)
    return response.data
  },

  handleCallback: async (provider: string, code: string, state: string): Promise<OAuthCallbackResponse> => {
    const response = await apiClient.get<OAuthCallbackResponse>(`/oauth/callback/${provider}`, {
      params: { code, state }
    })
    return response.data
  },

  submitEmail: async (email: string, tempToken: string): Promise<OAuthEmailVerifyResponse> => {
    const response = await apiClient.post<OAuthEmailVerifyResponse>('/oauth/submit-email-with-token', {
      email,
      temp_token: tempToken
    })
    return response.data
  },

  verifyEmail: async (token: string, email: string): Promise<OAuthCallbackResponse> => {
    const response = await apiClient.get<OAuthCallbackResponse>('/oauth/verify-email', {
      params: { token, email }
    })
    return response.data
  },

  getPendingVerification: async (tempToken: string): Promise<PendingVerificationInfo> => {
    const response = await apiClient.get<PendingVerificationInfo>(`/oauth/pending-verification/${tempToken}`)
    return response.data
  },

  resendVerification: async (tempToken: string): Promise<ResendVerificationResponse> => {
    const response = await apiClient.post<ResendVerificationResponse>('/oauth/resend-verification', {
      temp_token: tempToken
    })
    return response.data
  },

  changeEmail: async (tempToken: string, newEmail: string): Promise<ResendVerificationResponse> => {
    const response = await apiClient.post<ResendVerificationResponse>('/oauth/change-email', {
      temp_token: tempToken,
      new_email: newEmail
    })
    return response.data
  }
}
