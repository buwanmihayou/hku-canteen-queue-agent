"""Offline export and JavaScript/Python parity with synthetic inputs only."""
from datetime import time
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from build_offline import build, export_data
from calibration import STALL_RATES, estimated_queue_count
from routing import WALK_TIMES, rank_canteens


class OfflinePlannerTests(unittest.TestCase):
    def test_export_all_canteens_all_minutes(self):
        data = export_data()
        self.assertEqual(len(data["canteens"]), 8)
        self.assertEqual(len(data["walk_times"]), 7)
        for canteen in data["canteens"]:
            self.assertEqual(len(canteen["counts"]), 1440)
            for minute, count in enumerate(canteen["counts"]):
                self.assertEqual(count, estimated_queue_count(canteen["name"], time(minute // 60, minute % 60)))

    def test_build_self_contained_and_versioned(self):
        with tempfile.TemporaryDirectory() as directory:
            output = build(directory)
            standalone = (output / "offline.html").read_text(encoding="utf-8")
            self.assertNotIn("%%", standalone)
            self.assertNotIn('src="', standalone)
            self.assertNotIn('rel="manifest"', standalone)
            self.assertNotIn("serviceWorker.register", standalone)
            self.assertIn("serviceWorker.register", (output / "index.html").read_text(encoding="utf-8"))
            self.assertNotIn("%%VERSION%%", (output / "sw.js").read_text(encoding="utf-8"))
            before = (output / "sw.js").read_bytes()
            build(directory)
            self.assertEqual(before, (output / "sw.js").read_bytes())

    def test_javascript_matches_python(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable; run parity with Node.js installed")
        cases = []
        for origin in WALK_TIMES:
            for hhmm in ("00:00", "11:30", "11:50", "12:00", "12:30", "13:30", "17:30", "18:00", "18:30", "19:30", "23:59"):
                hour, minute = map(int, hhmm.split(":"))
                for rush in (False, True):
                    expected = rank_canteens(STALL_RATES, origin, rush, dining_time=time(hour, minute))
                    cases.append({"origin": origin, "hhmm": hhmm, "rush": rush, "expected": [list(row) for row in expected]})
        planner = str(Path(__file__).with_name("offline") / "planner.js")
        script = """
const fs=require('fs'), assert=require('assert');
const payload=JSON.parse(fs.readFileSync(0,'utf8'));
const planner=require(payload.planner);
for(const item of payload.cases){
 const actual=planner.rank(payload.data,item.origin,item.hhmm,item.rush);
 assert.equal(actual.length,item.expected.length);
 actual.forEach((row,i)=>{
  const expected=item.expected[i]; assert.equal(row.name,expected[0]);
  [row.walk,row.wait,row.total,row.score].forEach((value,j)=>assert.ok(Math.abs(value-expected[j+1])<1e-9));
 });
}
for(const count of ['',-1,1.5]) assert.throws(()=>planner.manualWait(payload.data,payload.data.canteens[0].name,count));
assert.throws(()=>planner.minuteOfDay('24:00'));
assert.equal(planner.manualWait(payload.data,payload.data.canteens[0].name,0),0);
"""
        result = subprocess.run([node, "-e", script], input=json.dumps({"planner": planner, "data": export_data(), "cases": cases}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
