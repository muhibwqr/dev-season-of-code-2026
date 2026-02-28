from flask import Flask, render_template_string, request, jsonify
import sqlite3, json, datetime, os

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("contributions.db")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contributor TEXT, repo TEXT, type TEXT,
        description TEXT, points INTEGER, timestamp TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mentors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, skills TEXT, availability TEXT, contact TEXT
    )""")
    conn.commit()
    return conn

HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Dev Season of Code 2026</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg, #238636, #1f6feb); padding: 40px; text-align: center; }
.header h1 { font-size: 2.5em; color: white; margin-bottom: 10px; }
.header p { color: rgba(255,255,255,0.8); font-size: 1.1em; }
.container { max-width: 1100px; margin: 40px auto; padding: 0 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; }
.card h2 { color: #58a6ff; margin-bottom: 16px; font-size: 1.1em; }
input, select, textarea { width: 100%; padding: 10px; margin: 6px 0; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 14px; }
button { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; width: 100%; font-size: 14px; margin-top: 8px; }
button:hover { background: #2ea043; }
.leaderboard { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; }
.leaderboard h2 { color: #58a6ff; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; }
th { color: #8b949e; font-size: 12px; text-transform: uppercase; padding: 8px; text-align: left; border-bottom: 1px solid #30363d; }
td { padding: 12px 8px; border-bottom: 1px solid #21262d; }
.rank-1 { color: #ffd700; font-weight: bold; }
.rank-2 { color: #c0c0c0; }
.rank-3 { color: #cd7f32; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
.badge-pr { background: #1f6feb33; color: #58a6ff; }
.badge-issue { background: #da363333; color: #f85149; }
.badge-doc { background: #23863633; color: #3fb950; }
</style></head>
<body>
<div class="header">
  <h1>Dev Season of Code 2026</h1>
  <p>Track contributions. Find mentors. Build the future of open source.</p>
</div>
<div class="container">
  <div class="grid">
    <div class="card">
      <h2>Log a Contribution</h2>
      <input id="contributor" placeholder="Your GitHub username" />
      <input id="repo" placeholder="Repository (e.g. facebook/react)" />
      <select id="type">
        <option value="PR">Pull Request</option>
        <option value="Issue">Issue / Bug Report</option>
        <option value="Doc">Documentation</option>
        <option value="Review">Code Review</option>
      </select>
      <textarea id="desc" placeholder="What did you contribute?" rows="3"></textarea>
      <button onclick="logContribution()">Submit Contribution</button>
    </div>
    <div class="card">
      <h2>Find a Mentor</h2>
      <input id="skill_search" placeholder="Search skill (e.g. Python, React)" />
      <button onclick="findMentor()">Find Mentor</button>
      <div id="mentor_results" style="margin-top:12px;font-size:13px;"></div>
    </div>
  </div>
  <div class="leaderboard">
    <h2>Contribution Leaderboard</h2>
    <table><thead><tr><th>#</th><th>Contributor</th><th>Points</th><th>Contributions</th></tr></thead>
    <tbody id="leaderboard_body"></tbody></table>
  </div>
</div>
<script>
async function logContribution() {
  const r = await fetch('/api/contribute', {method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({contributor: document.getElementById('contributor').value,
    repo: document.getElementById('repo').value, type: document.getElementById('type').value,
    description: document.getElementById('desc').value})});
  const d = await r.json();
  alert(d.message || 'Logged!');
  loadLeaderboard();
}
async function findMentor() {
  const skill = document.getElementById('skill_search').value;
  const r = await fetch('/api/mentors?skill=' + encodeURIComponent(skill));
  const d = await r.json();
  document.getElementById('mentor_results').innerHTML = d.length
    ? d.map(m => `<div style="padding:8px;border-bottom:1px solid #30363d"><strong>${m.name}</strong><br><small>${m.skills}</small><br><a href="mailto:${m.contact}" style="color:#58a6ff">${m.contact}</a></div>`).join('')
    : '<p style="color:#8b949e">No mentors found. <a href="#" style="color:#58a6ff">Volunteer as a mentor</a></p>';
}
async function loadLeaderboard() {
  const r = await fetch('/api/leaderboard');
  const d = await r.json();
  const classes = ['rank-1','rank-2','rank-3'];
  document.getElementById('leaderboard_body').innerHTML = d.map((row, i) =>
    `<tr><td class="${classes[i]||''}">${i+1}</td><td>${row.contributor}</td><td><strong>${row.points}</strong></td><td>${row.count}</td></tr>`
  ).join('') || '<tr><td colspan="4" style="color:#8b949e;text-align:center;padding:20px">No contributions yet. Be the first!</td></tr>';
}
loadLeaderboard();
</script></body></html>"""

@app.route("/")
def index():
    return HTML

@app.route("/api/contribute", methods=["POST"])
def contribute():
    data = request.json
    points = {"PR": 10, "Issue": 5, "Doc": 7, "Review": 6}.get(data.get("type", "PR"), 5)
    db = get_db()
    db.execute("INSERT INTO contributions VALUES (NULL,?,?,?,?,?,?)",
        (data["contributor"], data["repo"], data["type"], data["description"],
         points, datetime.datetime.utcnow().isoformat()))
    db.commit()
    return jsonify({"message": f"Logged! +{points} points", "points": points})

@app.route("/api/leaderboard")
def leaderboard():
    db = get_db()
    rows = db.execute("""SELECT contributor, SUM(points) as points, COUNT(*) as count
        FROM contributions GROUP BY contributor ORDER BY points DESC LIMIT 20""").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/mentors")
def mentors():
    skill = request.args.get("skill", "")
    db = get_db()
    rows = db.execute("SELECT * FROM mentors WHERE skills LIKE ?", (f"%{skill}%",)).fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
