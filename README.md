# Subtitle Downloader

Aplicativo em Python para buscar legendas de episodios de series no OpenSubtitles V3 usado pelo Stremio.

Ele:

- busca a serie no TVMaze para descobrir o IMDb id;
- consulta `https://opensubtitles-v3.strem.io`;
- baixa um episodio pelo CLI;
- baixa uma temporada inteira pela interface grafica;
- associa legendas aos arquivos de video da pasta destino e copia a legenda com o mesmo nome do video;
- suporta pasta local do Windows ou pasta Android via ADB.

## Requisitos

- Python 3.10 ou superior
- Nenhuma dependencia externa

## Interface grafica

```powershell
python .\subtitle_downloader.py --gui
```

Fluxo recomendado:

1. digite a serie e clique em `Buscar`;
2. selecione a serie correta;
3. escolha `Local` ou `Android ADB`;
4. selecione/digite a `Pasta dos videos` e clique em `Ler videos`;
5. informe a temporada e clique em `Carregar temporada`;
6. clique em `Buscar legendas`;
7. revise as colunas `Selecionada` e `Video destino`;
8. use `Escolher legenda` quando quiser trocar a legenda de um episodio;
9. use `Arquivo destino` quando o casamento automatico escolher o arquivo errado;
10. clique em `Baixar selecionados`.

Quando um episodio tem `Video destino`, a legenda e copiada para a mesma pasta do video com o mesmo nome-base:

```text
D:\Series\Nome da Serie\Season 01\
  Nome.da.Serie.S01E01.mkv
  Nome.da.Serie.S01E01.srt
```

Se um episodio nao tiver video associado, a legenda ainda e salva na estrutura padrao `downloads/Nome da Serie/Season XX/`.

### Android via ADB

Arquivos Android conectados por USB geralmente aparecem no Windows Explorer via MTP, nao como uma pasta normal. Bibliotecas Python/Tkinter nao conseguem navegar esse local do mesmo jeito que o Explorer. Para Android, use o modo `Android ADB`:

1. instale Android Platform Tools;
2. habilite `USB debugging` no Android;
3. conecte o aparelho e aceite a autorizacao;
4. no app, selecione `Android ADB`;
5. clique em `Procurar` para navegar pelas pastas do Android via ADB;
6. clique em `Ler videos`.

O navegador Android começa com atalhos para `/sdcard`, `/storage/emulated/0` e tambem tenta mostrar cartoes/armazenamentos externos encontrados em `/storage`, como `/storage/XXXX-XXXX`.

Voce ainda pode digitar uma pasta manualmente, por exemplo `/sdcard/Movies`, `/sdcard/Download` ou `/storage/XXXX-XXXX/Movies`.

Se o app disser que `ADB nao encontrado`, adicione a pasta do Platform Tools ao `PATH` do Windows ou defina `ADB_PATH` com o caminho completo:

```powershell
$env:ADB_PATH="C:\platform-tools\adb.exe"
python .\subtitle_downloader.py --gui
```

Quando baixar, a legenda e enviada com `adb push` para a mesma pasta do video:

```text
/sdcard/Movies/Show.S01E01.mkv
/sdcard/Movies/Show.S01E01.srt
```

## CLI interativo

```powershell
python .\subtitle_downloader.py
```

O script vai perguntar:

- serie ou IMDb id;
- temporada;
- episodio;
- qual serie da lista voce quer;
- qual legenda baixar.

Por padrao ele filtra por `pob`, que e o codigo retornado pelo OpenSubtitles V3 para Portugues Brasil.

## Uso direto

```powershell
python .\subtitle_downloader.py --series "Game of Thrones" --season 1 --episode 1
```

Selecionar automaticamente o primeiro resultado de serie e a primeira legenda:

```powershell
python .\subtitle_downloader.py --series "Game of Thrones" --season 1 --episode 1 --first-show --first-subtitle
```

Listar todos os idiomas:

```powershell
python .\subtitle_downloader.py --series "Game of Thrones" --season 1 --episode 1 --all-languages
```

Usar IMDb id direto, sem depender do TVMaze:

```powershell
python .\subtitle_downloader.py --series tt0944947 --season 1 --episode 1
```

Arquivos baixados ficam em `downloads/` por padrao. Para trocar:

```powershell
python .\subtitle_downloader.py --series "Breaking Bad" --season 1 --episode 1 --output-dir "C:\Legendas"
```

## Observacoes

Esse endpoint V3 nao exige login nem API key, mas ele e um servico publico do ecossistema Stremio/OpenSubtitles. Para automacoes grandes, use fila, baixa concorrencia e cache local para evitar bloqueios temporarios.

## Arquitetura

- `subtitle_app/models.py`: dataclasses do dominio.
- `subtitle_app/http_client.py`: chamadas HTTP sem dependencias externas.
- `subtitle_app/providers.py`: clientes TVMaze e OpenSubtitles V3.
- `subtitle_app/downloader.py`: regras de scan, escolha padrao e download.
- `subtitle_app/video_library.py`: leitura da pasta de videos e casamento por episodio.
- `subtitle_app/adb_client.py`: leitura e envio de arquivos Android via ADB.
- `subtitle_app/cli.py`: interface de linha de comando.
- `subtitle_app/gui.py`: interface grafica Tkinter.
