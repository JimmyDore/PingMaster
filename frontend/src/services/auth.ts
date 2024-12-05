export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface SignUpCredentials {
  username: string;
  password: string;
}

class AuthService {
  private tokenKey = 'auth_token';
  private apiUrl = import.meta.env.PUBLIC_API_URL;

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await fetch(`${this.apiUrl}/auth/sign-in`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const token = await response.json();
    this.setToken(token);
    return token;
  }

  async signUp(credentials: SignUpCredentials): Promise<AuthToken> {
    const response = await fetch(`${this.apiUrl}/auth/sign-up`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Sign up failed');
    }

    const token = await response.json();
    this.setToken(token);
    return token;
  }

  getToken(): AuthToken | null {
    const token = localStorage.getItem(this.tokenKey);
    return token ? JSON.parse(token) : null;
  }

  setToken(token: AuthToken): void {
    localStorage.setItem(this.tokenKey, JSON.stringify(token));
  }

  removeToken(): void {
    localStorage.removeItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getAuthorizationHeader(): string | null {
    const token = this.getToken();
    return token ? `${token.token_type} ${token.access_token}` : null;
  }
}

export const authService = new AuthService(); 