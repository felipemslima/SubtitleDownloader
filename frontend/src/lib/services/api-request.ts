import { AxiosPromise } from 'axios';
import { ApiEnvelope } from '@/types/api';

export async function apiRequest<T>(request: AxiosPromise<ApiEnvelope<T>>): Promise<T> {
  const response = await request;
  if (!response.data.ok) {
    throw new Error(response.data.error || 'Erro inesperado na API');
  }
  return response.data.data;
}
