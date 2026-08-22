<?php
$releasePath = __DIR__ . '/downloads/Playlist-Porter-Windows.zip';
$releaseReady = is_file($releasePath);
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#111318"><meta name="description" content="Playlist Porter turns public YouTube and accessible Spotify playlists into neatly organized MP3 folders on Windows.">
  <meta property="og:title" content="Playlist Porter — Playlists, packed to go"><meta property="og:description" content="A Windows app for turning playlists into organized, numbered MP3 folders."><meta property="og:image" content="assets/playlist-porter-logo.png">
  <title>Playlist Porter — Playlists, packed to go</title><link rel="icon" href="assets/playlist-porter-logo.png"><link rel="stylesheet" href="styles.css">
</head>
<body>
  <header><a class="brand" href="#top"><img src="assets/playlist-porter-logo.png" alt="" width="44" height="44"><b>Playlist Porter</b></a><nav><a href="#features">Features</a><a href="#how">How it works</a><a href="#setup">Setup</a></nav><a class="button small" href="#download">Get the app</a></header>
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
    <section class="sources"><span>Works with public playlists from</span><strong class="yt">▶ YouTube</strong><strong class="sp">● Spotify</strong><small>Spotify playlists must belong to you or list you as a collaborator.</small></section>
    <section class="features shell" id="features"><div class="heading reveal"><p class="eyebrow">Less friction, more listening</p><h2>From link to library.<br><em>Neatly.</em></h2></div><div class="grid">
      <article class="reveal"><sup>01</sup><div class="icon folder"></div><h3>Organized by default</h3><p>Every conversion gets a Windows-safe folder named after the playlist, with every track numbered in order.</p></article>
      <article class="reveal"><sup>02</sup><div class="icon wave">▮▰▮▰▮</div><h3>Ready-to-play MP3s</h3><p>Audio is converted to consistent 192 kbps MP3 files using bundled FFmpeg—no separate installation needed.</p></article>
      <article class="reveal"><sup>03</sup><div class="icon stop">■</div><h3>You stay in control</h3><p>Preview the track list first. Stop a conversion at any time and keep every track that already finished.</p></article>
    </div></section>
    <section class="workflow" id="how"><div class="shell workflow-grid"><div class="reveal"><p class="eyebrow light">Three simple steps</p><h2>Your playlist has places to be.</h2><p>Playlist Porter handles the repetitive work while keeping the decisions clear and visible.</p></div><ol><li class="reveal"><b>1</b><div><h3>Paste a playlist link</h3><p>Use a public YouTube playlist or a Spotify playlist you own or collaborate on.</p></div></li><li class="reveal"><b>2</b><div><h3>Preview before you save</h3><p>Review the playlist name, track order, artists, and destination folder.</p></div></li><li class="reveal"><b>3</b><div><h3>Start the conversion</h3><p>Watch progress track by track, then open the finished playlist folder.</p></div></li></ol></div></section>
    <section class="details shell" id="setup"><div class="reveal"><p class="eyebrow">Thoughtful details</p><h2>Made for real-world playlists.</h2><div class="detail-grid"><div><b>Continues past unavailable tracks</b><p>One failed match does not derail the whole playlist.</p></div><div><b>Keeps a conversion record</b><p>A playlist-info.json file records the source and any failures.</p></div><div><b>Supports restricted videos</b><p>Optional browser or cookies.txt access helps with age-restricted YouTube media.</p></div><div><b>Remembers your preferences</b><p>Your destination, appearance, and Spotify setup stay on your Windows account.</p></div></div></div><aside class="reveal"><small>GOOD TO KNOW</small><h3>Spotify supplies the map, not the music.</h3><p>Spotify provides playlist titles, artists, order, and naming. Playlist Porter searches YouTube for matching audio, so a result can differ from the original recording.</p><p>Only save media you own or have permission to download, and follow each platform’s terms.</p></aside></section>
    <section class="download" id="download"><div class="orb"></div><img class="reveal" src="assets/playlist-porter-logo.png" alt="Playlist Porter logo" width="120" height="120"><p class="eyebrow light">Your playlists, your folders</p><h2 class="reveal">Take the long way home.<br><em>Bring the soundtrack.</em></h2><p class="reveal">A focused Windows desktop app with a simple setup and no separate FFmpeg installation.</p><?php if ($releaseReady): ?><a class="button lime reveal" href="downloads/Playlist-Porter-Windows.zip" download>Download for Windows ↓</a><?php else: ?><span class="button lime reveal" aria-disabled="true">Download being prepared</span><?php endif; ?><small>Requires Windows and internet access. Spotify use requires your own developer credentials.</small></section>
  </main>
  <footer><a class="brand" href="#top"><img src="assets/playlist-porter-logo.png" alt="" width="38" height="38"><b>Playlist Porter</b></a><p>Playlists, packed to go.</p><p>© <?= date('Y') ?> Playlist Porter</p></footer><script src="script.js"></script>
</body></html>
