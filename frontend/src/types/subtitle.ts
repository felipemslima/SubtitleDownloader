export type Show = {
  index: number;
  name: string;
  premiered: string;
  status: string;
  imdbId: string;
  tvmazeId: number | null;
};

export type Episode = {
  season: number;
  number: number;
  code: string;
  title: string;
  airdate: string;
};

export type Subtitle = {
  index: number;
  subtitleId: string;
  language: string;
  url: string;
  encoding: string;
  matchKind: string;
};

export type VideoFile = {
  path: string;
  displayName: string;
  season: number | null;
  episode: number | null;
  source: 'local' | 'android' | 'browser';
  key: string;
};

export type EpisodeSubtitlePlan = {
  episode: Episode;
  subtitles: Subtitle[];
  selectedSubtitle: Subtitle | null;
  enabled: boolean;
  status: string;
  outputPath: string | null;
  targetVideo: VideoFile | null;
  subtitleCount: number;
};

export type AndroidDirectory = {
  name: string;
  path: string;
};

export type AndroidRoot = {
  label: string;
  path: string;
};
