(function () {
  "use strict";
  const data = JSON.parse(document.getElementById("planner-data").textContent);
  const byId = id => document.getElementById(id);
  const fillSelect = (element, values) => values.forEach(value => {
    const option = document.createElement("option");
    option.value = value; option.textContent = value; element.appendChild(option);
  });
  fillSelect(byId("origin"), Object.keys(data.walk_times));
  fillSelect(byId("canteen"), data.canteens.map(item => item.name));
  const parts = new Intl.DateTimeFormat("en-GB", {timeZone: "Asia/Hong_Kong", hour: "2-digit", minute: "2-digit", hourCycle: "h23"}).formatToParts(new Date());
  byId("dining-time").value = parts.find(p => p.type === "hour").value + ":" + parts.find(p => p.type === "minute").value;
  byId("route-form").addEventListener("submit", event => {
    event.preventDefault();
    byId("route-error").textContent = ""; byId("routes").replaceChildren();
    try {
      const routes = HKUPlanner.rank(data, byId("origin").value, byId("dining-time").value, byId("rush").checked);
      routes.slice(0, 3).forEach((route, index) => {
        const article = document.createElement("article"); article.className = "route";
        const heading = document.createElement("h3"); heading.textContent = (index + 1) + ". " + route.name;
        const total = document.createElement("p"); total.className = "duration"; total.textContent = "~" + route.total.toFixed(1) + " min total";
        const detail = document.createElement("p"); detail.className = "detail";
        detail.textContent = route.walk + " min walk + " + route.wait.toFixed(1) + " min estimated wait · Assumed queue: " + Number(route.count.toFixed(1)) + " people";
        article.append(heading, total, detail); byId("routes").appendChild(article);
      });
    } catch (error) { byId("route-error").textContent = error.message; }
  });
  byId("queue-form").addEventListener("submit", event => {
    event.preventDefault(); byId("queue-error").textContent = ""; byId("queue-result").textContent = "";
    try {
      const wait = HKUPlanner.manualWait(data, byId("canteen").value, byId("headcount").value);
      byId("queue-result").textContent = "Estimated wait: " + wait.toFixed(1) + " min for " + Number(byId("headcount").value) + " people. Assumes the empirical service rate stays constant.";
    } catch (error) { byId("queue-error").textContent = error.message; }
  });
})();
