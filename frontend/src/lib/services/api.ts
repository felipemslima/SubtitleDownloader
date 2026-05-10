import axios from 'axios';
import { ENV } from './env';

export const api = axios.create({
  baseURL: ENV.VITE_API_LOCAL_BASE_URL,
  timeout: 120000,
});
