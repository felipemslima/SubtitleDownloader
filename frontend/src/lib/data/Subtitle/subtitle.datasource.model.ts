import { Episode, EpisodeSubtitlePlan, Show, VideoFile } from '@/types/subtitle';

export type ScanSubtitlesRequest = {
  show: Show;
  episodes: Episode[];
  language: string;
  videos: VideoFile[];
};

export type DownloadPlansRequest = {
  show: Show;
  outputDir?: string;
  plans: EpisodeSubtitlePlan[];
};
