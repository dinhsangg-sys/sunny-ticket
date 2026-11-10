(() => {
  const video = document.getElementById('svIntroVideo');
  const button = document.getElementById('svListen');
  const status = document.getElementById('svVideoStatus');
  if (!video || !button || !status) return;
  let interacted = false;
  const sync = () => { button.hidden = !video.paused && !video.muted && video.volume > 0; };
  const failed = () => { button.hidden = false; status.textContent = status.dataset.error; };
  for (const event of ['playing', 'pause', 'volumechange', 'ended']) video.addEventListener(event, sync);
  video.addEventListener('error', failed);
  button.addEventListener('click', () => {
    interacted = true;
    video.muted = false;
    if (video.volume === 0) video.volume = 1;
    // Keep play() in the click handler so the browser recognizes the gesture.
    video.play().then(() => { status.textContent = ''; sync(); }).catch(failed);
  });
  video.muted = false;
  video.play().then(() => { status.textContent = ''; sync(); }).catch(async error => {
    if (interacted) return;
    if (error.name !== 'NotAllowedError') { failed(); return; }
    status.textContent = status.dataset.blocked;
    button.hidden = false;
    video.muted = true;
    try { await video.play(); sync(); } catch (_) { button.hidden = false; }
  });
})();
