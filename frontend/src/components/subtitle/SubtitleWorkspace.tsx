import { Check, Download, Files, RefreshCw, Search, Subtitles, Video } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/Button';
import {
  useDownloadPlansZip,
  useEpisodes,
  useScanSubtitles,
  useSearchShows,
} from '@/lib/domain/Subtitle';
import { EpisodeSubtitlePlan, Show, VideoFile } from '@/types/subtitle';

type BrowserVideoFile = File & { webkitRelativePath?: string };

const videoExtensions = new Set([
  '.mkv',
  '.mp4',
  '.avi',
  '.mov',
  '.m4v',
  '.wmv',
  '.mpg',
  '.mpeg',
  '.ts',
  '.m2ts',
  '.vob',
]);

function getExtension(name: string) {
  const dotIndex = name.lastIndexOf('.');
  return dotIndex >= 0 ? name.slice(dotIndex).toLowerCase() : '';
}

function parseEpisodeFromName(name: string): { season: number | null; episode: number | null } {
  const value = name.toLowerCase();
  const patterns = [
    /s(?<season>\d{1,2})[ ._-]*e(?<episode>\d{1,3})/,
    /(?<season>\d{1,2})x(?<episode>\d{1,3})/,
    /season[ ._-]*(?<season>\d{1,2}).*episode[ ._-]*(?<episode>\d{1,3})/,
  ];

  for (const pattern of patterns) {
    const match = value.match(pattern);
    if (match?.groups?.season && match.groups.episode) {
      return { season: Number(match.groups.season), episode: Number(match.groups.episode) };
    }
  }

  return { season: null, episode: null };
}

function filesToVideos(fileList: FileList | null): VideoFile[] {
  if (!fileList) return [];

  return Array.from(fileList)
    .filter((file) => videoExtensions.has(getExtension(file.name)))
    .map((file) => {
      const browserFile = file as BrowserVideoFile;
      const path = browserFile.webkitRelativePath || file.name;
      const parsed = parseEpisodeFromName(file.name);
      return {
        path,
        displayName: file.name,
        season: parsed.season,
        episode: parsed.episode,
        source: 'browser' as const,
        key: `browser:${path}`,
      };
    })
    .sort((left, right) => left.path.localeCompare(right.path));
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function safeDownloadName(show: Show | null, season: number) {
  const baseName = (show?.name || 'legendas').replace(/[^a-z0-9._-]+/gi, '-').replace(/^-|-$/g, '');
  return `${baseName || 'legendas'}-season-${String(season).padStart(2, '0')}-subtitles.zip`;
}

export function SubtitleWorkspace() {
  const [query, setQuery] = useState('');
  const [season, setSeason] = useState('1');
  const [language, setLanguage] = useState('pob');
  const [shows, setShows] = useState<Show[]>([]);
  const [selectedShow, setSelectedShow] = useState<Show | null>(null);
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [plans, setPlans] = useState<EpisodeSubtitlePlan[]>([]);
  const [log, setLog] = useState<string[]>([]);

  const searchShows = useSearchShows();
  const loadEpisodes = useEpisodes();
  const scanSubtitles = useScanSubtitles();
  const downloadPlansZip = useDownloadPlansZip();

  const busy = searchShows.isPending || loadEpisodes.isPending || scanSubtitles.isPending || downloadPlansZip.isPending;
  const selectedPlans = useMemo(() => plans.filter((plan) => plan.enabled && plan.selectedSubtitle), [plans]);

  function pushLog(message: string) {
    setLog((current) => [`${new Date().toLocaleTimeString()} ${message}`, ...current].slice(0, 80));
  }

  function getSeasonNumber() {
    const parsed = Number(season);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  }

  async function handleSearchShows() {
    const result = await searchShows.mutateAsync(query);
    setShows(result);
    setSelectedShow(result[0] || null);
    setEpisodes([]);
    setPlans([]);
    pushLog('Series pesquisadas');
  }

  async function handleLoadEpisodes() {
    if (!selectedShow) return;
    const seasonNumber = getSeasonNumber();
    if (!seasonNumber) {
      pushLog('Informe uma temporada valida antes de carregar');
      return;
    }
    const result = await loadEpisodes.mutateAsync({ show: selectedShow, season: seasonNumber });
    setEpisodes(result);
    setPlans(result.map((episode: any) => ({ episode, subtitles: [], selectedSubtitle: null, enabled: false, status: 'Pendente', outputPath: null, targetVideo: null, subtitleCount: 0 })));
    pushLog('Temporada carregada');
  }

  function handleVideoFiles(fileList: FileList | null) {
    const result = filesToVideos(fileList);
    setVideos(result);
    setPlans((current) => current.map((plan) => ({ ...plan, targetVideo: null })));
    pushLog(`${result.length} nome(s) de video carregado(s) do navegador`);
  }

  async function handleScanSubtitles() {
    if (!selectedShow) return;
    const result = await scanSubtitles.mutateAsync({ show: selectedShow, episodes, language, videos });
    setPlans(result);
    pushLog('Legendas buscadas e videos associados por nome');
  }

  async function handleDownloadZip() {
    if (!selectedShow) return;
    const seasonNumber = getSeasonNumber();
    if (!seasonNumber) {
      pushLog('Informe uma temporada valida antes de baixar');
      return;
    }
    const blob = await downloadPlansZip.mutateAsync({ show: selectedShow, plans: selectedPlans });
    downloadBlob(blob, safeDownloadName(selectedShow, seasonNumber));
    setPlans((current) => current.map((plan) => (plan.enabled && plan.selectedSubtitle ? { ...plan, status: 'ZIP baixado', outputPath: 'zip' } : plan)));
    pushLog('ZIP de legendas baixado');
  }

  function updatePlan(index: number, patch: Partial<EpisodeSubtitlePlan>) {
    setPlans((current) => current.map((plan, idx) => (idx === index ? { ...plan, ...patch } : plan)));
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>Subtitle Downloader</h1>
          <p>Busca legendas PT-BR a partir dos nomes dos seus videos e baixa um ZIP com os arquivos .srt.</p>
        </div>
        <div className="status">{busy ? 'Processando...' : 'Pronto'}</div>
      </header>

      <section className="toolbar">
        <label>
          Serie ou IMDb
          <div className="inputAction">
            <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && handleSearchShows()} />
            <Button onClick={handleSearchShows} disabled={!query}><Search size={16} /> Buscar</Button>
          </div>
        </label>
        <label>Temporada<input type="number" min="1" value={season} onChange={(event) => setSeason(event.target.value)} /></label>
        <label>Idioma<input value={language} onChange={(event) => setLanguage(event.target.value)} /></label>
        <div className="sourceSummary"><Files size={16} /> Somente nomes dos videos</div>
      </section>

      <section className="folderBar">
        <label>
          Arquivos de video
          <input type="file" multiple accept=".mkv,.mp4,.avi,.mov,.m4v,.wmv,.mpg,.mpeg,.ts,.m2ts,.vob" onChange={(event) => handleVideoFiles(event.target.files)} />
        </label>
        <label>
          Pasta de videos
          <input type="file" multiple {...{ webkitdirectory: '', directory: '' }} onChange={(event) => handleVideoFiles(event.target.files)} />
        </label>
        <div className="videoCount"><Video size={16} /> {videos.length} video(s)</div>
      </section>

      <section className="layout">
        <aside>
          <div className="panelHeader"><h2>Series</h2></div>
          <div className="list">
            {shows.map((show) => (
              <Button key={`${show.tvmazeId}-${show.imdbId}`} className={selectedShow?.imdbId === show.imdbId ? 'selected' : ''} onClick={() => setSelectedShow(show)}>
                <strong>{show.name}</strong><span>{show.premiered} - {show.status} - {show.imdbId}</span>
              </Button>
            ))}
          </div>
          <Button className="wide" disabled={!selectedShow} onClick={handleLoadEpisodes}><RefreshCw size={16} /> Carregar temporada</Button>
        </aside>

        <section className="workspace">
          <div className="panelHeader">
            <h2>Temporada</h2>
            <div className="actions">
              <Button disabled={episodes.length === 0} onClick={handleScanSubtitles}><Subtitles size={16} /> Buscar legendas</Button>
              <Button disabled={selectedPlans.length === 0} onClick={handleDownloadZip}><Download size={16} /> Baixar ZIP</Button>
            </div>
          </div>
          <div className="tableWrap">
            <table>
              <thead><tr><th>Baixar</th><th>Ep</th><th>Titulo</th><th>Legenda</th><th>Arquivo destino no ZIP</th><th>Status</th></tr></thead>
              <tbody>
                {plans.map((plan, index) => (
                  <tr key={plan.episode.code}>
                    <td><input type="checkbox" checked={plan.enabled} onChange={(event) => updatePlan(index, { enabled: event.target.checked })} /></td>
                    <td>{plan.episode.code}</td>
                    <td>{plan.episode.title}</td>
                    <td><select value={plan.selectedSubtitle?.subtitleId || ''} onChange={(event) => updatePlan(index, { selectedSubtitle: plan.subtitles.find((subtitle) => subtitle.subtitleId === event.target.value) || null, enabled: Boolean(event.target.value) })}><option value="">Sem legenda</option>{plan.subtitles.map((subtitle) => <option key={subtitle.subtitleId} value={subtitle.subtitleId}>{subtitle.language} - {subtitle.subtitleId} - {subtitle.encoding}</option>)}</select></td>
                    <td><select value={plan.targetVideo?.key || ''} onChange={(event) => updatePlan(index, { targetVideo: videos.find((video) => video.key === event.target.value) || null })}><option value="">Nome gerado automaticamente</option>{videos.map((video) => <option key={video.key} value={video.key}>{video.displayName}</option>)}</select></td>
                    <td>{plan.outputPath ? <span className="done"><Check size={14} /> Pronto</span> : plan.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <section className="log">{log.map((item, index) => <div key={`${item}-${index}`}>{item}</div>)}</section>
    </main>
  );
}
