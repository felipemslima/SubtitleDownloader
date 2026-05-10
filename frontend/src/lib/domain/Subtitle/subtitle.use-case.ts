import { useMutation, useQuery } from '@tanstack/react-query';
import {
  downloadPlansDatasource,
  downloadPlansZipDatasource,
  getAndroidDirectoriesDatasource,
  getAndroidRootsDatasource,
  getEpisodesDatasource,
  scanSubtitlesDatasource,
  scanVideosDatasource,
  searchShowsDatasource,
} from '@/lib/data/Subtitle';

export function useSearchShows() {
  return useMutation({ mutationFn: searchShowsDatasource });
}

export function useEpisodes() {
  return useMutation({ mutationFn: ({ show, season }: any) => getEpisodesDatasource(show, season) });
}

export function useScanVideos() {
  return useMutation({ mutationFn: ({ source, folder }: { source: string; folder: string }) => scanVideosDatasource(source, folder) });
}

export function useAndroidRoots(enabled: boolean) {
  return useQuery({ queryKey: ['android-roots'], queryFn: getAndroidRootsDatasource, enabled });
}

export function useAndroidDirectories() {
  return useMutation({ mutationFn: getAndroidDirectoriesDatasource });
}

export function useScanSubtitles() {
  return useMutation({ mutationFn: scanSubtitlesDatasource });
}

export function useDownloadPlans() {
  return useMutation({ mutationFn: downloadPlansDatasource });
}

export function useDownloadPlansZip() {
  return useMutation({ mutationFn: downloadPlansZipDatasource });
}
