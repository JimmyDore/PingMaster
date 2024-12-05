import { authService } from '../services/auth';

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const authHeader = authService.getAuthorizationHeader();
  
  if (!authHeader) {
    throw new Error('No authentication token available');
  }

  const headers = {
    ...options.headers,
    'Authorization': authHeader,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authService.removeToken();
    window.location.href = '/login';
    throw new Error('Authentication expired');
  }

  return response;
} 