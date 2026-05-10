import { api } from '@/lib/services/api';
import { apiRequest } from '@/lib/services/api-request';
import { AndroidDirectory, AndroidRoot, Episode, EpisodeSubtitlePlan, Show, VideoFile } from '@/types/subtitle';
import { DownloadPlansRequest, ScanSubtitlesRequest } from './subtitle.datasource.model';

export function searchShowsDatasource(query: string): Promise<Show[]> {
  return apiRequest(api.get('/shows', { params: { q: query } }));
}

export function getEpisodesDatasource(show: Show, season: number): Promise<Episode[]> {
  return apiRequest(api.get(`/shows/${show.tvmazeId}/episodes`, { params: { season, imdbId: show.imdbId, name: show.name } }));
}

export function scanVideosDatasource(source: string, folder: string): Promise<VideoFile[]> {
  return apiRequest(api.post('/videos/scan', { source, folder }));
}

export function getAndroidRootsDatasource(): Promise<AndroidRoot[]> {
  return apiRequest(api.get('/android/roots'));
}

export function getAndroidDirectoriesDatasource(path: string): Promise<{ path: string; parent: string; directories: AndroidDirectory[] }> {
  return apiRequest(api.get('/android/directories', { params: { path } }));
}

export function scanSubtitlesDatasource(payload: ScanSubtitlesRequest): Promise<EpisodeSubtitlePlan[]> {
  return apiRequest(api.post('/subtitles/scan', payload));
}

export function downloadPlansDatasource(payload: DownloadPlansRequest): Promise<EpisodeSubtitlePlan[]> {
  return apiRequest(api.post('/download', payload));
}

export async function downloadPlansZipDatasource(payload: DownloadPlansRequest): Promise<Blob> {
  const response = await api.post('/download/zip', payload, { responseType: 'blob' });
  return response.data;
}
