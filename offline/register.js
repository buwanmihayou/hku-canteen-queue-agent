(function () {
  "use strict";
  const status = document.getElementById("offline-status");
  if (!("serviceWorker" in navigator) || !window.isSecureContext) {
    status.textContent = "Calculations work offline in this open page. Download offline.html for later, or serve this PWA over HTTPS/localhost.";
    return;
  }
  navigator.serviceWorker.register("./sw.js").then(() => navigator.serviceWorker.ready).then(() => {
    status.textContent = "Offline ready. You can reopen or reload this planner without a connection.";
  }).catch(() => {
    status.textContent = "Calculations are ready. Offline installation could not finish; save offline.html before disconnecting.";
  });
})();
