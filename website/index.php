<?php
declare(strict_types=1);

const REPOSITORY = 'mrjohndowe/PlaylistPorter';
const REPOSITORY_URL = 'https://github.com/' . REPOSITORY;

function githubJson(string $endpoint): ?array
{
    $url = 'https://api.github.com/repos/' . REPOSITORY . '/' . ltrim($endpoint, '/');
    $headers = ['Accept: application/vnd.github+json', 'User-Agent: Playlist-Porter-Website'];
    $body = false;

    if (function_exists('curl_init')) {
        $handle = curl_init($url);
        curl_setopt_array($handle, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 3,
            CURLOPT_TIMEOUT => 6,
            CURLOPT_HTTPHEADER => $headers,
        ]);
        $body = curl_exec($handle);
        $status = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
        curl_close($handle);
        if ($status < 200 || $status >= 300) $body = false;
    } elseif (filter_var(ini_get('allow_url_fopen'), FILTER_VALIDATE_BOOLEAN)) {
        $context = stream_context_create(['http' => ['header' => implode("\r\n", $headers), 'timeout' => 6]]);
        $body = @file_get_contents($url, false, $context);
    }

    if (!is_string($body)) return null;
    $data = json_decode($body, true);
    return is_array($data) ? $data : null;
}

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function releaseNotes(string $markdown): string
{
    $lines = preg_split('/\R/', trim($markdown)) ?: [];
    $html = '';
    foreach (array_slice($lines, 0, 24) as $line) {
        $line = trim($line);
        if ($line === '') continue;
        $line = preg_replace('/^#{1,6}\s+/', '', $line) ?? $line;
        $line = preg_replace('/^[-*]\s+/', '• ', $line) ?? $line;
        $html .= '<li>' . e($line) . '</li>';
    }
    return $html;
}

$repository = githubJson('');
$release = githubJson('releases/latest');
$downloadUrl = null;
$downloadName = 'Latest release';

if ($release) {
    $assets = is_array($release['assets'] ?? null) ? $release['assets'] : [];
    foreach ($assets as $asset) {
        $assetName = (string) ($asset['name'] ?? '');
        if (preg_match('/\.exe$/i', $assetName) && !empty($asset['browser_download_url'])) {
            $downloadUrl = (string) $asset['browser_download_url'];
            $downloadName = $assetName;
            break;
        }
    }
}

$releaseUrl = (string) ($release['html_url'] ?? (REPOSITORY_URL . '/releases'));
$releaseTitle = (string) ($release['name'] ?? $release['tag_name'] ?? 'Release notes coming soon');
$releaseTag = (string) ($release['tag_name'] ?? 'No published release yet');
$releaseDate = !empty($release['published_at']) ? date('F j, Y', strtotime((string) $release['published_at'])) : 'The first GitHub release has not been published yet.';
$repoDescription = (string) ($repository['description'] ?? 'A Windows desktop app that turns playlists into organized MP3 folders.');
$repoUpdated = !empty($repository['updated_at']) ? date('F j, Y', strtotime((string) $repository['updated_at'])) : 'Recently';
$notes = releaseNotes((string) ($release['body'] ?? 'Release notes will appear here automatically when a GitHub release is published.'));
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#111318"><meta name="description" content="Playlist Porter turns public YouTube and accessible Spotify playlists into neatly organized MP3 folders on Windows.">
  <meta property="og:title" content="Playlist Porter — Playlists, packed to go"><meta property="og:description" content="A Windows app for turning playlists into organized, numbered MP3 folders."><meta property="og:image" content="assets/playlist-porter-logo.png">
  <title>Playlist Porter — Playlists, packed to go</title><link rel="icon" href="assets/playlist-porter-logo.png"><script>try{const t=localStorage.getItem('playlist-porter-theme');if(t)document.documentElement.dataset.theme=t;else if(matchMedia('(prefers-color-scheme:dark)').matches)document.documentElement.dataset.theme='dark'}catch(e){}</script><link rel="stylesheet" href="styles.css">
</head>
<body>
  <header><a class="brand" href="#top"><img src="assets/playlist-porter-logo.png" alt="" width="44" height="44"><b>Playlist Porter</b></a><nav><a href="#features">Features</a><a href="#how">How it works</a><a href="#changelog">Changelog</a></nav><button class="theme-toggle" type="button" aria-label="Switch to dark mode" aria-pressed="false"><span aria-hidden="true">☾</span><b>Dark</b></button><a class="button small" href="#download">Get the app</a></header>
  <main id="top">
    <section class="hero shell">
      <div class="reveal"><p class="eyebrow">Built for Windows</p><h1>Playlists,<br><em>packed to go.</em></h1><p class="lede">Turn a public YouTube playlist or an accessible Spotify playlist into a clean, numbered MP3 folder—without wrestling with filenames, formats, or extra tools.</p><div class="actions"><a class="button" href="#download">Download Playlist Porter ↓</a><a class="text-link" href="#how">See how it works →</a></div><p class="micro">Windows desktop app · Bundled FFmpeg · 192 kbps MP3</p></div>
      <div class="app reveal" aria-label="Illustration of the Playlist Porter app">
        <div class="titlebar"><span><img src="assets/playlist-porter-logo.png" alt="" width="28" height="28">Playlist Porter</span><i>−　□　×</i></div>
        <div class="appbody"><div class="source"><span class="play">▶</span><span><small>SOURCE PLAYLIST</small><strong>Late Night Coding</strong></span><em>24 tracks</em></div><div class="url">https://open.spotify.com/playlist/… <b>Preview</b></div>
          <div class="tracks"><div><b>01</b><span><strong>Midnight Drive</strong><small>Satellite Coast</small></span><i>Ready</i></div><div><b>02</b><span><strong>Soft Focus</strong><small>Analog Hearts</small></span><i>Ready</i></div><div><b>03</b><span><strong>Neon Weather</strong><small>City Signals</small></span><i>Ready</i></div></div>
          <div class="progress"><span><b>Saving your playlist</b><em>18 of 24</em></span><div><i></i></div></div><div class="appfoot"><span>MP3 · 192 kbps</span><button>Stop</button></div>
        </div>
      </div>
    </section>
    <section class="sources"><span>Works with public playlists from</span><strong class="yt">▶ YouTube</strong><strong class="sp">● Spotify</strong><a href="<?= e(REPOSITORY_URL) ?>" target="_blank" rel="noopener">GitHub repository ↗</a><small><?= e($repoDescription) ?></small></section>
    <section class="features shell" id="features"><div class="heading reveal"><p class="eyebrow">Less friction, more listening</p><h2>From link to library.<br><em>Neatly.</em></h2></div><div class="grid">
      <article class="reveal"><sup>01</sup><div class="icon folder"></div><h3>Organized by default</h3><p>Every conversion gets a Windows-safe folder named after the playlist, with every track numbered in order.</p></article>
      <article class="reveal"><sup>02</sup><div class="icon wave">▮▰▮▰▮</div><h3>Ready-to-play MP3s</h3><p>Audio is converted to consistent 192 kbps MP3 files using bundled FFmpeg—no separate installation needed.</p></article>
      <article class="reveal"><sup>03</sup><div class="icon stop">■</div><h3>You stay in control</h3><p>Preview the track list first. Stop a conversion at any time and keep every track that already finished.</p></article>
    </div></section>
    <section class="workflow" id="how"><div class="shell workflow-grid"><div class="reveal"><p class="eyebrow light">Three simple steps</p><h2>Your playlist has places to be.</h2><p>Playlist Porter handles the repetitive work while keeping the decisions clear and visible.</p></div><ol><li class="reveal"><b>1</b><div><h3>Paste a playlist link</h3><p>Use a public YouTube playlist or a Spotify playlist you own or collaborate on.</p></div></li><li class="reveal"><b>2</b><div><h3>Preview before you save</h3><p>Review the playlist name, track order, artists, and destination folder.</p></div></li><li class="reveal"><b>3</b><div><h3>Start the conversion</h3><p>Watch progress track by track, then open the finished playlist folder.</p></div></li></ol></div></section>
    <section class="details shell" id="setup"><div class="reveal"><p class="eyebrow">Thoughtful details</p><h2>Made for real-world playlists.</h2><div class="detail-grid"><div><b>Continues past unavailable tracks</b><p>One failed match does not derail the whole playlist.</p></div><div><b>Keeps a conversion record</b><p>A playlist-info.json file records the source and any failures.</p></div><div><b>Supports restricted videos</b><p>Optional browser or cookies.txt access helps with age-restricted YouTube media.</p></div><div><b>Remembers your preferences</b><p>Your destination, appearance, and Spotify setup stay on your Windows account.</p></div></div></div><aside class="reveal"><small>GOOD TO KNOW</small><h3>Spotify supplies the map, not the music.</h3><p>Spotify provides playlist titles, artists, order, and naming. Playlist Porter searches YouTube for matching audio, so a result can differ from the original recording.</p><p>Only save media you own or have permission to download, and follow each platform’s terms.</p></aside></section>
    <section class="release shell" id="changelog"><div class="release-heading reveal"><p class="eyebrow">From the repository</p><h2>What’s New</h2><p>The latest version and changes are loaded automatically from the newest GitHub release.</p><dl><div><dt>Latest version</dt><dd><?= e($releaseTag) ?></dd></div><div><dt>Published</dt><dd><?= e($releaseDate) ?></dd></div><div><dt>Repository updated</dt><dd><?= e($repoUpdated) ?></dd></div></dl></div><article class="release-card reveal"><span>LATEST RELEASE</span><h3><?= e($releaseTitle) ?></h3><ul><?= $notes ?></ul><a href="<?= e($releaseUrl) ?>" target="_blank" rel="noopener">View the full release on GitHub →</a></article></section>
    <section class="download" id="download"><div class="orb"></div><img class="reveal" src="assets/playlist-porter-logo.png" alt="Playlist Porter logo" width="120" height="120"><p class="eyebrow light">Latest Windows release</p><h2 class="reveal">Download Playlist Porter<br><em><?= e($releaseTag) ?></em></h2><p class="reveal">The version and download link update automatically from the latest GitHub release.</p><?php if ($downloadUrl): ?><a class="button lime reveal" href="<?= e($downloadUrl) ?>">Download the latest EXE ↓</a><small>Direct GitHub release asset: <?= e($downloadName) ?></small><?php else: ?><a class="button lime reveal" href="<?= e($releaseUrl) ?>" target="_blank" rel="noopener">View releases on GitHub →</a><small>The latest release does not contain an EXE yet. Add an .exe asset to make this a direct download automatically.</small><?php endif; ?></section>
  </main>
  <footer><a class="brand" href="#top"><img src="assets/playlist-porter-logo.png" alt="" width="38" height="38"><b>Playlist Porter</b></a><p>Playlists, packed to go.</p><p>© <?= date('Y') ?> Playlist Porter</p></footer><script src="script.js"></script>
</body></html>

