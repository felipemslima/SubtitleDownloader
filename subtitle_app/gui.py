from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from .config import DEFAULT_OUTPUT_DIR
from .adb_client import get_android_start_locations, list_android_directories, parent_remote_path, scan_android_video_files
from .downloader import SubtitleDownloadService
from .models import EpisodeSubtitlePlan, ShowCandidate, Subtitle, VideoFile
from .providers import TvMazeClient
from .video_library import assign_videos_to_plans, scan_video_files


class SubtitleDownloaderGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Subtitle Downloader")
        self.geometry("1120x720")
        self.minsize(980, 620)

        self.tvmaze = TvMazeClient()
        self.downloader = SubtitleDownloadService()
        self.ui_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.search_results: list[ShowCandidate] = []
        self.selected_show: ShowCandidate | None = None
        self.plans: list[EpisodeSubtitlePlan] = []
        self.video_files: list[VideoFile] = []

        self.series_var = tk.StringVar()
        self.language_var = tk.StringVar(value="pob")
        self.season_var = tk.IntVar(value=1)
        self.output_dir_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.source_var = tk.StringVar(value="local")
        self.status_var = tk.StringVar(value="Pronto")

        self._build_ui()
        self.after(100, self._drain_queue)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        search_frame = ttk.Frame(self, padding=(12, 12, 12, 6))
        search_frame.grid(row=0, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Serie ou IMDb").grid(row=0, column=0, sticky="w")
        series_entry = ttk.Entry(search_frame, textvariable=self.series_var)
        series_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        series_entry.bind("<Return>", lambda _event: self.search_shows())
        ttk.Button(search_frame, text="Buscar", command=self.search_shows).grid(row=0, column=2)

        controls_frame = ttk.Frame(self, padding=(12, 0, 12, 8))
        controls_frame.grid(row=1, column=0, sticky="ew")
        controls_frame.columnconfigure(7, weight=1)

        ttk.Label(controls_frame, text="Temporada").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(controls_frame, from_=1, to=99, textvariable=self.season_var, width=6).grid(row=0, column=1, padx=(8, 18))
        ttk.Label(controls_frame, text="Idioma").grid(row=0, column=2, sticky="w")
        ttk.Entry(controls_frame, textvariable=self.language_var, width=10).grid(row=0, column=3, padx=(8, 18))
        ttk.Radiobutton(controls_frame, text="Local", variable=self.source_var, value="local", command=self.on_source_changed).grid(row=0, column=4)
        ttk.Radiobutton(controls_frame, text="Android ADB", variable=self.source_var, value="android", command=self.on_source_changed).grid(row=0, column=5)
        ttk.Label(controls_frame, text="Pasta dos videos").grid(row=0, column=6, sticky="w", padx=(12, 0))
        ttk.Entry(controls_frame, textvariable=self.output_dir_var).grid(row=0, column=7, sticky="ew", padx=(8, 8))
        ttk.Button(controls_frame, text="Procurar", command=self.choose_output_dir).grid(row=0, column=8)
        ttk.Button(controls_frame, text="Ler videos", command=self.scan_videos).grid(row=0, column=9, padx=(8, 0))

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))

        left = ttk.Frame(main_pane)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        ttk.Label(left, text="Resultados da serie").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.show_tree = ttk.Treeview(left, columns=("name", "premiered", "status", "imdb"), show="headings", height=10)
        self.show_tree.heading("name", text="Serie")
        self.show_tree.heading("premiered", text="Estreia")
        self.show_tree.heading("status", text="Status")
        self.show_tree.heading("imdb", text="IMDb")
        self.show_tree.column("name", width=240)
        self.show_tree.column("premiered", width=80, anchor="center")
        self.show_tree.column("status", width=80, anchor="center")
        self.show_tree.column("imdb", width=90, anchor="center")
        self.show_tree.grid(row=1, column=0, sticky="nsew")
        self.show_tree.bind("<<TreeviewSelect>>", lambda _event: self.on_show_selected())
        self.show_tree.bind("<Double-1>", lambda _event: self.load_season())
        main_pane.add(left, weight=1)

        right = ttk.Frame(main_pane)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        actions = ttk.Frame(right)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(actions, text="Carregar temporada", command=self.load_season).pack(side=tk.LEFT)
        ttk.Button(actions, text="Buscar legendas", command=self.scan_subtitles).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Escolher legenda", command=self.choose_subtitle_for_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Arquivo destino", command=self.choose_video_for_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Baixar selecionados", command=self.download_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Marcar todos", command=lambda: self.set_all_enabled(True)).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Desmarcar todos", command=lambda: self.set_all_enabled(False)).pack(side=tk.RIGHT, padx=(0, 8))

        self.episode_tree = ttk.Treeview(
            right,
            columns=("enabled", "episode", "title", "subs", "selected", "video", "status"),
            show="headings",
            height=16,
        )
        headings = {
            "enabled": "Baixar",
            "episode": "Ep",
            "title": "Titulo",
            "subs": "Legendas",
            "selected": "Selecionada",
            "video": "Video destino",
            "status": "Status",
        }
        for column, label in headings.items():
            self.episode_tree.heading(column, text=label)
        self.episode_tree.column("enabled", width=60, anchor="center", stretch=False)
        self.episode_tree.column("episode", width=70, anchor="center", stretch=False)
        self.episode_tree.column("title", width=260)
        self.episode_tree.column("subs", width=80, anchor="center", stretch=False)
        self.episode_tree.column("selected", width=120, anchor="center")
        self.episode_tree.column("video", width=240)
        self.episode_tree.column("status", width=160, anchor="center")
        self.episode_tree.grid(row=1, column=0, sticky="nsew")
        self.episode_tree.bind("<Double-1>", lambda _event: self.choose_subtitle_for_selected())
        self.episode_tree.bind("<space>", lambda _event: self.toggle_selected_episode())
        main_pane.add(right, weight=2)

        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.grid(row=3, column=0, sticky="nsew")
        bottom.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(bottom, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        self.log_text = tk.Text(bottom, height=7, wrap="word")
        self.log_text.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        bottom.rowconfigure(2, weight=1)

    def choose_output_dir(self) -> None:
        if self.source_var.get() == "android":
            self.open_android_folder_browser()
            return
        selected = filedialog.askdirectory(initialdir=self.output_dir_var.get() or str(DEFAULT_OUTPUT_DIR))
        if selected:
            self.output_dir_var.set(selected)
            self.scan_videos()

    def on_source_changed(self) -> None:
        if self.source_var.get() == "android":
            if self.output_dir_var.get() == str(DEFAULT_OUTPUT_DIR):
                self.output_dir_var.set("/sdcard")
            self.status_var.set("Modo Android: use Procurar para navegar no aparelho via ADB")
        else:
            if self.output_dir_var.get().startswith("/sdcard"):
                self.output_dir_var.set(str(DEFAULT_OUTPUT_DIR))
            self.status_var.set("Modo local")

    def scan_videos(self) -> None:
        folder = self.output_dir_var.get().strip()
        if not folder:
            messagebox.showwarning("Videos", "Selecione a pasta dos videos.")
            return

        def worker() -> tuple[str, list[VideoFile]]:
            if self.source_var.get() == "android":
                return ("videos", scan_android_video_files(folder))
            return ("videos", scan_video_files(Path(folder), recursive=True))

        self.run_worker("Lendo arquivos de video...", worker)

    def open_android_folder_browser(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Selecionar pasta Android")
        dialog.geometry("760x520")
        dialog.transient(self)
        dialog.grab_set()

        current_path = tk.StringVar(value=self.output_dir_var.get() if self.output_dir_var.get().startswith("/") else "/sdcard")
        status = tk.StringVar(value="Conectando via ADB...")
        root_options: list[tuple[str, str]] = []

        top = ttk.Frame(dialog, padding=12)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Atalhos").grid(row=0, column=0, sticky="w")
        root_var = tk.StringVar()
        root_combo = ttk.Combobox(top, textvariable=root_var, state="readonly")
        root_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(top, text="Ir", command=lambda: load_path(root_lookup.get(root_var.get(), current_path.get()))).grid(row=0, column=2)
        top.columnconfigure(1, weight=1)

        path_frame = ttk.Frame(dialog, padding=(12, 0, 12, 8))
        path_frame.pack(fill=tk.X)
        ttk.Label(path_frame, text="Pasta atual").pack(anchor="w")
        path_entry = ttk.Entry(path_frame, textvariable=current_path)
        path_entry.pack(fill=tk.X, pady=(4, 0))
        path_entry.bind("<Return>", lambda _event: load_path(current_path.get()))

        list_frame = ttk.Frame(dialog, padding=(12, 0, 12, 8))
        list_frame.pack(fill=tk.BOTH, expand=True)
        listbox = tk.Listbox(list_frame, activestyle="dotbox")
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        bottom.pack(fill=tk.X)
        ttk.Label(bottom, textvariable=status).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Voltar", command=lambda: load_path(parent_remote_path(current_path.get()))).pack(side=tk.RIGHT)
        ttk.Button(bottom, text="Usar esta pasta", command=lambda: select_current()).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(bottom, text="Atualizar", command=lambda: load_path(current_path.get())).pack(side=tk.RIGHT, padx=(0, 8))

        directory_paths: list[str] = []
        root_lookup: dict[str, str] = {}

        def set_busy(message: str) -> None:
            status.set(message)
            dialog.update_idletasks()

        def populate_roots() -> None:
            nonlocal root_options, root_lookup
            try:
                root_options = get_android_start_locations()
                root_lookup = {label: path for label, path in root_options}
                root_combo.configure(values=[label for label, _path in root_options])
                if root_options:
                    root_var.set(root_options[0][0])
            except Exception as exc:
                messagebox.showerror("Android ADB", str(exc), parent=dialog)
                status.set("Erro ao listar armazenamentos Android")

        def load_path(path: str) -> None:
            nonlocal directory_paths
            cleaned = path.strip() or "/sdcard"
            current_path.set(cleaned)
            set_busy(f"Lendo {cleaned}...")
            try:
                directory_paths = list_android_directories(cleaned)
                listbox.delete(0, tk.END)
                if cleaned != "/":
                    listbox.insert(tk.END, "..")
                for directory in directory_paths:
                    listbox.insert(tk.END, PurePosixPath(directory).name + "/")
                status.set(f"{len(directory_paths)} pasta(s) encontrada(s)")
            except Exception as exc:
                messagebox.showerror("Android ADB", str(exc), parent=dialog)
                status.set("Erro ao listar pasta")

        def open_selected(_event=None) -> None:
            selection = listbox.curselection()
            if not selection:
                return
            index = selection[0]
            label = listbox.get(index)
            if label == "..":
                load_path(parent_remote_path(current_path.get()))
                return
            offset = 1 if current_path.get().rstrip("/") != "/" else 0
            directory_index = index - offset
            if 0 <= directory_index < len(directory_paths):
                load_path(directory_paths[directory_index])

        def select_current() -> None:
            self.output_dir_var.set(current_path.get())
            dialog.destroy()
            self.scan_videos()

        listbox.bind("<Double-1>", open_selected)
        populate_roots()
        load_path(current_path.get())

    def run_worker(self, title: str, worker: Callable[[], object]) -> None:
        self.status_var.set(title)

        def wrapped() -> None:
            try:
                result = worker()
                self.ui_queue.put(("result", result))
            except Exception as exc:
                self.ui_queue.put(("error", exc))

        threading.Thread(target=wrapped, daemon=True).start()

    def search_shows(self) -> None:
        query = self.series_var.get().strip()
        if not query:
            messagebox.showwarning("Busca", "Digite o nome da serie ou IMDb id.")
            return
        self.run_worker("Buscando series...", lambda: ("shows", self.tvmaze.search_shows(query)))

    def on_show_selected(self) -> None:
        selection = self.show_tree.selection()
        if not selection:
            return
        index = int(selection[0])
        if 0 <= index < len(self.search_results):
            self.selected_show = self.search_results[index]
            self.status_var.set(f"Serie selecionada: {self.selected_show.name}")

    def load_season(self) -> None:
        if not self.selected_show:
            messagebox.showwarning("Temporada", "Selecione uma serie primeiro.")
            return
        season = int(self.season_var.get())
        self.run_worker(
            f"Carregando temporada {season}...",
            lambda: ("episodes", self.tvmaze.fetch_episodes(self.selected_show, season)),
        )

    def scan_subtitles(self) -> None:
        if not self.selected_show:
            messagebox.showwarning("Legendas", "Selecione uma serie primeiro.")
            return
        if not self.plans:
            messagebox.showwarning("Legendas", "Carregue uma temporada primeiro.")
            return

        episodes = [plan.episode for plan in self.plans]
        language = self.language_var.get().strip() or "pob"
        self.progress.configure(maximum=len(episodes), value=0)

        def worker() -> tuple[str, list[EpisodeSubtitlePlan]]:
            plans: list[EpisodeSubtitlePlan] = []
            for episode in episodes:
                plan = self.downloader.scan_episode(self.selected_show, episode, language)
                plans.append(plan)
                self.ui_queue.put(("scan_progress", plan))
            assign_videos_to_plans(plans, self.video_files)
            return ("plans", plans)

        self.run_worker("Buscando legendas da temporada...", worker)

    def download_selected(self) -> None:
        if not self.selected_show:
            messagebox.showwarning("Download", "Selecione uma serie primeiro.")
            return
        selected_plans = [plan for plan in self.plans if plan.enabled and plan.selected_subtitle]
        if not selected_plans:
            messagebox.showwarning("Download", "Nenhum episodio com legenda selecionada.")
            return

        output_dir = DEFAULT_OUTPUT_DIR if self.source_var.get() == "android" else Path(self.output_dir_var.get()).expanduser().resolve()
        self.progress.configure(maximum=len(selected_plans), value=0)

        def worker() -> tuple[str, list[EpisodeSubtitlePlan]]:
            downloaded: list[EpisodeSubtitlePlan] = []
            for plan in selected_plans:
                try:
                    path = self.downloader.download_plan(self.selected_show, plan, output_dir)
                    plan.status = "Baixado"
                    plan.output_path = path
                    self.ui_queue.put(("download_progress", plan))
                    downloaded.append(plan)
                except Exception as exc:
                    plan.status = f"Erro: {exc}"
                    self.ui_queue.put(("download_progress", plan))
            return ("downloaded", downloaded)

        self.run_worker("Baixando legendas...", worker)

    def choose_subtitle_for_selected(self) -> None:
        plan = self.get_selected_plan()
        if not plan:
            return
        if not plan.subtitles:
            messagebox.showinfo("Legendas", "Esse episodio ainda nao tem legendas carregadas.")
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Escolher legenda - {plan.episode.code}")
        dialog.geometry("760x360")
        dialog.transient(self)
        dialog.grab_set()

        tree = ttk.Treeview(dialog, columns=("idx", "lang", "id", "encoding", "url"), show="headings")
        for column, label in {
            "idx": "#",
            "lang": "Idioma",
            "id": "ID",
            "encoding": "Encoding",
            "url": "URL",
        }.items():
            tree.heading(column, text=label)
        tree.column("idx", width=45, anchor="center", stretch=False)
        tree.column("lang", width=70, anchor="center", stretch=False)
        tree.column("id", width=90, anchor="center", stretch=False)
        tree.column("encoding", width=100, anchor="center", stretch=False)
        tree.column("url", width=430)
        tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        for idx, subtitle in enumerate(plan.subtitles):
            tree.insert("", tk.END, iid=str(idx), values=(subtitle.index, subtitle.language, subtitle.subtitle_id, subtitle.encoding, subtitle.url))

        if plan.selected_subtitle:
            selected_index = plan.subtitles.index(plan.selected_subtitle)
            tree.selection_set(str(selected_index))

        def apply_selection() -> None:
            selection = tree.selection()
            if not selection:
                return
            subtitle = plan.subtitles[int(selection[0])]
            plan.selected_subtitle = subtitle
            plan.enabled = True
            plan.status = "Selecionado"
            self.refresh_episode_tree()
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=12, pady=(0, 12))
        ttk.Button(buttons, text="Usar selecionada", command=apply_selection).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 8))
        tree.bind("<Double-1>", lambda _event: apply_selection())

    def choose_video_for_selected(self) -> None:
        plan = self.get_selected_plan()
        if not plan:
            return
        if not self.video_files:
            messagebox.showinfo("Videos", "Leia uma pasta de videos primeiro.")
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Arquivo destino - {plan.episode.code}")
        dialog.geometry("820x230")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=f"{plan.episode.code} - {plan.episode.title}").pack(anchor="w", padx=12, pady=(12, 6))
        ttk.Label(dialog, text="Escolha qual arquivo de video deve receber a legenda:").pack(anchor="w", padx=12, pady=(0, 6))

        none_option = "(sem arquivo destino)"
        option_to_video: dict[str, VideoFile | None] = {none_option: None}
        options = [none_option]
        for index, video in enumerate(self.video_files, start=1):
            label = f"{index:02d}. {video.display_name}"
            if video.season is not None and video.episode is not None:
                label += f"  [S{video.season:02d}E{video.episode:02d}]"
            option_to_video[label] = video
            options.append(label)

        selected = tk.StringVar()
        current_option = none_option
        if plan.target_video:
            current_option = next(
                (label for label, video in option_to_video.items() if video and video.key == plan.target_video.key),
                none_option,
            )
        selected.set(current_option)
        combo = ttk.Combobox(dialog, textvariable=selected, values=options, state="readonly")
        combo.pack(fill=tk.X, padx=12, pady=(0, 12))

        path_var = tk.StringVar(value=str(plan.target_video.path) if plan.target_video else "")
        ttk.Label(dialog, textvariable=path_var, foreground="#555").pack(anchor="w", padx=12, pady=(0, 8))

        def update_path_preview(_event=None) -> None:
            video = option_to_video.get(selected.get())
            path_var.set(str(video.path) if video else "")

        combo.bind("<<ComboboxSelected>>", update_path_preview)

        def apply_selection() -> None:
            video = option_to_video.get(selected.get())
            if video is None:
                plan.target_video = None
                plan.status = "Arquivo destino removido"
            else:
                plan.target_video = video
                plan.status = "Arquivo destino ajustado"
            self.refresh_episode_tree()
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=12, pady=(0, 12))
        ttk.Button(buttons, text="Usar arquivo", command=apply_selection).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 8))
        combo.focus_set()

    def get_selected_plan(self) -> EpisodeSubtitlePlan | None:
        selection = self.episode_tree.selection()
        if not selection:
            messagebox.showinfo("Episodio", "Selecione um episodio.")
            return None
        index = int(selection[0])
        if 0 <= index < len(self.plans):
            return self.plans[index]
        return None

    def toggle_selected_episode(self) -> None:
        plan = self.get_selected_plan()
        if not plan:
            return
        plan.enabled = not plan.enabled
        self.refresh_episode_tree()

    def set_all_enabled(self, enabled: bool) -> None:
        for plan in self.plans:
            plan.enabled = enabled and bool(plan.selected_subtitle)
        self.refresh_episode_tree()

    def refresh_show_tree(self) -> None:
        self.show_tree.delete(*self.show_tree.get_children())
        for idx, show in enumerate(self.search_results):
            self.show_tree.insert("", tk.END, iid=str(idx), values=(show.name, show.premiered, show.status, show.imdb_id))
        if self.search_results:
            self.show_tree.selection_set("0")
            self.selected_show = self.search_results[0]

    def refresh_episode_tree(self) -> None:
        self.episode_tree.delete(*self.episode_tree.get_children())
        for idx, plan in enumerate(self.plans):
            selected = plan.selected_subtitle.subtitle_id if plan.selected_subtitle else "-"
            video = plan.target_video.display_name if plan.target_video else "-"
            self.episode_tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    "Sim" if plan.enabled else "Nao",
                    plan.episode.code,
                    plan.episode.title,
                    plan.subtitle_count,
                    selected,
                    video,
                    plan.status,
                ),
            )

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _drain_queue(self) -> None:
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "error":
                    self.status_var.set("Erro")
                    messagebox.showerror("Erro", str(payload))
                    self.log(f"Erro: {payload}")
                elif kind == "result":
                    self._handle_result(payload)
                elif kind == "scan_progress":
                    plan = payload
                    self.progress.step(1)
                    self.log(f"{plan.episode.code}: {plan.status}")
                elif kind == "download_progress":
                    plan = payload
                    self.progress.step(1)
                    self.refresh_episode_tree()
                    if plan.output_path:
                        self.log(f"{plan.episode.code}: salvo em {plan.output_path}")
                    else:
                        self.log(f"{plan.episode.code}: {plan.status}")
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _handle_result(self, payload: object) -> None:
        if not isinstance(payload, tuple) or len(payload) != 2:
            return
        result_type, value = payload
        if result_type == "shows":
            self.search_results = value
            self.refresh_show_tree()
            self.status_var.set(f"{len(self.search_results)} serie(s) encontrada(s)")
        elif result_type == "episodes":
            episodes = value
            self.plans = [EpisodeSubtitlePlan(episode=episode) for episode in episodes]
            assign_videos_to_plans(self.plans, self.video_files)
            self.refresh_episode_tree()
            self.status_var.set(f"{len(self.plans)} episodio(s) carregado(s)")
        elif result_type == "plans":
            self.plans = value
            self.refresh_episode_tree()
            self.status_var.set("Busca de legendas concluida")
        elif result_type == "downloaded":
            self.refresh_episode_tree()
            self.status_var.set(f"{len(value)} legenda(s) baixada(s)")
        elif result_type == "videos":
            self.video_files = value
            assign_videos_to_plans(self.plans, self.video_files)
            self.refresh_episode_tree()
            self.status_var.set(f"{len(self.video_files)} video(s) encontrado(s)")
            self.log(f"Videos encontrados: {len(self.video_files)}")


def main() -> None:
    app = SubtitleDownloaderGui()
    app.mainloop()
