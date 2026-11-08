/* Pure calculations shared by the UI and parity tests. */
(function (root) {
  "use strict";
  function minuteOfDay(value) {
    if (!/^\d{2}:\d{2}$/.test(value)) throw new Error("Choose a valid dining time.");
    const parts = value.split(":").map(Number);
    if (parts[0] > 23 || parts[1] > 59) throw new Error("Choose a valid dining time.");
    return parts[0] * 60 + parts[1];
  }
  function manualWait(data, name, count) {
    const canteen = data.canteens.find(item => item.name === name);
    if (!canteen) throw new Error("Choose a dining location.");
    if (String(count).trim() === "" || !Number.isInteger(Number(count)) || Number(count) < 0 || Number(count) > 10000) {
      throw new Error("Enter a whole-number headcount from 0 to 10000.");
    }
    return Number(count) * canteen.rate;
  }
  function rank(data, origin, hhmm, rush) {
    const minute = minuteOfDay(hhmm);
    const walks = data.walk_times[origin];
    if (!walks) throw new Error("Choose your current campus location.");
    return data.canteens.map(canteen => {
      const count = canteen.counts[minute];
      const walk = walks[canteen.name];
      const wait = count * canteen.rate;
      return {name: canteen.name, count, walk, wait, total: walk + wait, score: (rush ? 1.5 : 1) * walk + wait};
    }).sort((a, b) => a.score - b.score);
  }
  const planner = {minuteOfDay, manualWait, rank};
  if (typeof module !== "undefined" && module.exports) module.exports = planner;
  root.HKUPlanner = planner;
})(typeof globalThis !== "undefined" ? globalThis : this);
