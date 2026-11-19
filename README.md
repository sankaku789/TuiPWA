<img src="assets/icon.svg" width="64" height="64" alt="">

# TuiPWA

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

日本語 | [English](README.en.md)

TUI アプリを、独立したデスクトップアプリのように使える Linux x64 向けランチャーです。[Ghostty](https://ghostty.org/) を共有ホストとして使い、アプリごとにタブなしのウィンドウを開きます。

- 登録したアプリをデスクトップメニューから起動できます。
- アプリごとに独立したウィンドウ・PTY を持ち、終了するとウィンドウも閉じます。

## インストール

### 1. Rust / Cargo を導入

[Rust の公式インストール手順](https://www.rust-lang.org/tools/install)に従い、stable ツールチェーンを導入してください（edition 2024 対応）。`rustc --version` と `cargo --version` が実行できることを確認します。

### 2. OS のパッケージでツール・ライブラリを導入

お使いのディストリビューションに合わせて、ビルドと実行に必要なパッケージを導入してください。`desktop-file-utils` は「このアプリケーションで開く」の候補一覧を更新するために使います。あわせて、実行環境に合ったグラフィックスドライバー、Adwaita / hicolor アイコンテーマ、システムフォントが必要です（通常のデスクトップ環境では導入済みのことが多いです）。

#### Arch 系（Arch Linux など）

```sh
sudo pacman -S --needed \
  base-devel python git curl xz \
  gtk4 libadwaita gtk4-layer-shell wayland libx11 libglvnd fontconfig freetype2 \
  desktop-file-utils
```

#### Debian / Ubuntu 系（Debian 13、Ubuntu など）

```sh
sudo apt update
sudo apt install \
  build-essential pkg-config python3 git curl ca-certificates patch xz-utils binutils \
  libglib2.0-dev libgtk-4-dev libadwaita-1-dev libgtk4-layer-shell-dev \
  libwayland-dev libx11-dev libegl-dev libfontconfig-dev libfreetype-dev \
  desktop-file-utils
```

#### Red Hat / Fedora 系（Fedora など）

```sh
sudo dnf install \
  gcc make pkgconf-pkg-config python3 git curl patch tar xz binutils \
  glib2-devel gtk4-devel libadwaita-devel gtk4-layer-shell-devel \
  wayland-devel libX11-devel libglvnd-devel fontconfig-devel freetype-devel \
  desktop-file-utils
```

RHEL 互換ディストリビューションでは、`gtk4-layer-shell-devel` などの提供に EPEL 等の追加リポジトリが必要な場合があります。

#### その他のディストリビューション

上記以外では、以下のツール・ライブラリに対応するパッケージを導入してください。**ライブラリは実行用だけでなく、ヘッダーや pkg-config 設定を含む開発用パッケージ（`-dev` / `-devel` 等）も必要です。**

| 用途 | 導入するもの |
|---|---|
| コンパイル・ビルド | C コンパイラ、Make、pkg-config、Python 3、binutils |
| ソース取得・展開・パッチ適用 | Git、curl、CA 証明書、patch、tar、xz |
| ウィンドウ・UI・GLib | GTK 4、libadwaita、gtk4-layer-shell、GLib / GIO / GObject |
| 描画・フォント・ディスプレイ | Wayland クライアント、X11、EGL、fontconfig、FreeType |
| 実行時の表示・デスクトップ連携 | グラフィックスドライバー、Adwaita / hicolor アイコンテーマ、システムフォント、desktop-file-utils（`update-desktop-database`） |

用途やビルド時の扱いの詳細は [依存ライブラリ・ツール](CONTRIBUTING.md#依存ライブラリツール)を参照してください。

### 3. TuiPWA をビルド・インストール

`make` はダウンロード・ビルドの前に、主なコマンドと開発ライブラリの不足をチェックします。チェックだけを実行する場合は、リポジトリ内で `make check-deps` を使います。不足があれば一覧を表示して停止し、Arch 系・Debian / Ubuntu 系・Red Hat / Fedora 系では不足分のパッケージ名と導入コマンド例も案内します（バージョン互換性や GUI 実行環境を保証するものではありません）。

次のものはビルド時に自動取得するため、**手動での導入は不要**です。初回のビルドにはインターネット接続が必要です。

- Zig：`make` が所定のバージョンを取得します。
- 専用 Ghostty ホスト：`make` がソースを取得し、パッチを適用してビルドします。通常の Ghostty を別途インストールする必要はありません。
- Rust クレート：Cargo が `Cargo.lock` に従って取得します。

```sh
git clone https://github.com/sankaku789/tuipwa.git
cd tuipwa
make install
```

CLI は通常 `~/.cargo/bin` へ、専用ホストは通常 `~/.local/share/tuipwa/native/` へ導入されます。Cargo の `bin/` が PATH に入っていれば、そのまま `tuipwa` を使えます。`make install` に sudo は不要です。

パッチ済み Ghostty は自動でビルド・導入します。GTK 等は OS のパッケージを使用し、同梱しません。初回のビルドには時間がかかります。

## 使い方

起動する TUI アプリは、あらかじめインストールしてください。まずは登録して起動します。

```sh
tuipwa add btop
tuipwa run btop
```

登録したアプリはデスクトップメニューからも起動できます。`run`・`show`・`update`・`remove` では登録 ID を指定します（既定は実行ファイル名です）。

### コマンド一覧

| コマンド | 操作 |
|---|---|
| `tuipwa add <command>` | アプリを登録します |
| `tuipwa run <id> [id ...]` | 登録したアプリを起動します |
| `tuipwa run <id> -- <ファイル>...` | 指定したファイルを登録したアプリで開きます |
| `tuipwa list` | 登録一覧を表示します |
| `tuipwa show <id>` | 登録内容を表示します |
| `tuipwa update <id> [オプション]` | 指定した項目だけ更新します |
| `tuipwa remove <id>` | 登録を解除します。TUI 本体は削除しません |
| `tuipwa validate <manifest.json>` | マニフェストを検証します |

### 登録したアプリでファイルを開く

```sh
tuipwa run nano -- ./memo.txt "./日本語のメモ.txt"
```

`--` の前に登録 ID を1つ、後ろにローカルファイルを指定します。ファイルは登録済み引数の後ろに追加され、今回の起動だけに使われます。相対パスは**コマンド実行元のディレクトリ**を基準に絶対パス化します。未作成ファイルも指定できます。アプリの作業ディレクトリと登録内容は変更しません。

`--` の後ろはすべてファイルパスとして扱います。アプリのオプションは `add` / `update` で登録してください。URL の解釈やシェルによる再解釈は行いません。

### 「このアプリケーションで開く」の候補に登録

```sh
tuipwa add nano                         # 既存の.desktopから対応MIMEタイプを自動取得します
# 明示指定する場合や、すでに登録済みなら更新します
tuipwa update nano --mime-type text/plain --mime-type text/markdown
tuipwa show nano
```

新規登録時は、XDGのアプリケーションディレクトリにある既存の `.desktop` から、実行コマンドが一致するエントリの `MimeType` を取得します。見つかればKDEなどの「このアプリケーションで開く」の候補として登録します。`add --manifest` でも同様です。アプリ名の決め打ちやコマンドの実行による推測は行いません。

見つからない場合や手動で上書きする場合は、`--mime-type` に開けるファイルのMIMEタイプを指定してください。ラッパー経由の起動や複雑なエスケープを含む実行パスは自動判別の対象外です。選択した複数のローカルファイルは1つのアプリ起動に渡します。ファイルを指定しない通常のメニュー起動も、そのまま使えます。**既定アプリの設定は変更しません。**

`update` の `--mime-type` は対応一覧を置き換えます。省略時は維持し、`tuipwa update nano --clear-mime-types` で対応を解除できます。明示指定も自動取得もできない登録は、候補への対応を宣言しません。既存登録の `update` では自動取得し直さないため、手動設定や解除状態は維持されます。ワイルドカードや `;` 区切りではなく、タイプごとにオプションを繰り返してください。

候補一覧のキャッシュは `update-desktop-database` で更新します。ツールがない場合などは警告を表示しますが、登録内容は保存されます。警告に表示されたコマンドを実行して再反映してください。実際の候補表示にはデスクトップ側のキャッシュも影響します。

### 名前・引数・作業ディレクトリを指定

```sh
tuipwa add vim --id notes --name "Notes" --cwd ~/Documents -- ~/notes.txt
tuipwa run notes
tuipwa show notes
```

`--id` は登録 ID、`--name` はメニュー表示名、`--title` はウィンドウタイトル、`--cwd` は作業ディレクトリです。TUI に渡す引数は `--` の後ろへ指定します。シェルによる再解釈は行いません。

### アイコン・カテゴリを指定

```sh
tuipwa update btop --color "#2563EB" --category System --category Monitor
tuipwa add vim --id editor --icon ./editor.png
```

`--color` は生成アイコンの背景色、`--icon` は既存の PNG/ICO を指定します。両者は同時に指定できません。`add` でどちらも省略するとアイコンを自動決定します。カテゴリの既定は `Utility` です。

同じ ID は重複登録できません。登録済みのアプリには `update` を使います。

### 更新・登録解除

```sh
tuipwa update notes --name "My Notes"
tuipwa update notes -- ~/Documents/todo.txt       # 引数を置き換えます
tuipwa update notes --clear-args                 # 引数を空にします
tuipwa update btop --color "#0F766E"
tuipwa update btop --auto-icon                    # 自動生成アイコンに戻します
tuipwa remove notes
```

更新は次回起動から反映されます。

### JSON から登録

```sh
tuipwa validate examples/nano.json
tuipwa add --manifest examples/nano.json
```

全オプションは `tuipwa --help`、JSON の形式は [manifest v1](docs/MANIFEST.md)を参照してください。

### ヘルプの言語

`LC_ALL` → `LC_MESSAGES` → `LANG` の順で空でない値を参照し、日本語ロケールでは日本語、それ以外や未設定の場合は英語で表示します。

```sh
env LC_ALL=C tuipwa --help                  # 英語
env LC_ALL=ja_JP.UTF-8 tuipwa --help       # 日本語
```

言語の切り替えはヘルプ本文のみが対象です。その他の出力やエラーメッセージは全面翻訳していません。

## Ghostty の設定

専用ホストは、Ghostty標準の設定ファイルを読み込みます。通常は `~/.config/ghostty/config` と `~/.config/ghostty/config.ghostty` で、`XDG_CONFIG_HOME` を設定している場合はその配下を使います。両方ある場合はこの順で読み込みます。フォント・配色などをTuiPWA用にコピーする必要はありません。

TuiPWAの動作に必要な起動制御・タブなし表示・状態復元の無効化・キーバインドの無効化などは、ユーザー設定より優先します。アプリのコマンド・タイトル・作業ディレクトリは登録内容を使います。設定の反映を確実にするには、TuiPWAの全ウィンドウを閉じてから起動し直してください。

## 開発・仕様

- [CONTRIBUTING.md](CONTRIBUTING.md) — dev ビルド、テスト、リンク付き依存一覧、内部構成、配布・実機確認
- [manifest v1](docs/MANIFEST.md) — 登録 JSON の仕様

## ライセンス

TuiPWA 本体は [MIT License](LICENSE)です。Ghostty・依存ライブラリ・フォントはそれぞれのライセンスに従います。詳細は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)を参照してください。
