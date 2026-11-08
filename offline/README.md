# Offline companion

`offline.html` is one self-contained file. Download it from the Streamlit app,
save it on the device while connected, then open it in a JavaScript-enabled
browser. It needs no Python server, API key or internet connection. It provides
Top-3 routes at a selected Hong Kong dining time and a manual-headcount wait
calculator. It does not analyze photographs.

`index.html` is the installable PWA version. Serve this directory over HTTPS
or localhost, open it once online and wait for **Offline ready**. Then the app
can reload without the network. Service workers do not install from `file://`
or an insecure remote HTTP site. On a phone, use an HTTPS host; a laptop's
LAN IP served over plain HTTP is not equivalent to localhost on that phone.

For a local desktop check:

```powershell
python build_offline.py
python -m http.server 8765 --directory offline --bind 127.0.0.1
```

Open `http://localhost:8765/`. Installation controls depend on the browser.
The Streamlit app is still a server application: its existing page cannot
rerun Python after a lost connection. Keep this companion available separately.

Generated data comes directly from `calibration.py` and `routing.py` at
minute resolution. Re-run `python build_offline.py` after editing either.
The service-worker cache version changes with the generated assets. Do not
edit generated `index.html`, `offline.html`, `data.json` or `sw.js` by hand.

All service rates, queues and walks are empirical assumptions awaiting field
validation. Opening hours are not modeled. Synthetic parity tests check the
implementation, not measured headcount accuracy or real phone compatibility.

Service-worker behavior follows the
[MDN guide](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).
