export type OrganizationRole = 'owner' | 'admin' | 'member' | 'viewer' | 'guest';

export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  role: OrganizationRole;
  organization_id: string;
};

export type RegisterInput = {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export type AuthSessionPayload = {
  user: User;
  accessToken: string;
  refreshToken: string;
};