from flask import Flask, request, jsonify

app = Flask(__name__)

# punteggi ufficiali della F1 per GP normali (1..10)
F1_POINTS_GP = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
# punteggi per sprint (1..8)
F1_POINTS_SPRINT = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

def calc_pilot_points(p):
"""
Calcola i punti per un pilota.
p: dizionario con info della gara
Ritorna: punteggio totale e breakdown
"""
pts = 0.0
breakdown = []

is_sprint = bool(p.get("is_sprint", False))
finish_pos = p.get("finish_position")

# 1) Punti ufficiali della gara
if finish_pos and isinstance(finish_pos, int):
if is_sprint:
base = F1_POINTS_SPRINT.get(finish_pos, 0)
else:
base = F1_POINTS_GP.get(finish_pos, 0)
pts += base
breakdown.append(("race_points", base))
else:
breakdown.append(("race_points", 0))

# 2) Bonus
if p.get("pole", False) and not is_sprint:
pts += 2
breakdown.append(("bonus_pole", 2))

if p.get("fastest_lap", False):
pts += 1
breakdown.append(("bonus_fastest_lap", 1))

if p.get("driver_of_the_day", False):
pts += 1
breakdown.append(("bonus_dotd", 1))

if p.get("fastest_pitstop", False):
pts += 2
breakdown.append(("bonus_fastest_pitstop", 2))

if p.get("started_last_two_rows", False):
earned = 0
if finish_pos and isinstance(finish_pos, int):
if is_sprint:
earned = F1_POINTS_SPRINT.get(finish_pos, 0)
else:
earned = F1_POINTS_GP.get(finish_pos, 0)
if earned > 0:
pts += 2
breakdown.append(("bonus_start_last_rows_to_points", 2))

pos_gained = p.get("positions_gained", 0) or 0
if pos_gained > 0:
add = 0.5 * pos_gained
pts += add
breakdown.append(("bonus_positions_gained", add))

if not is_sprint and finish_pos == 1:
pts += 3
breakdown.append(("bonus_victory", 3))

if not is_sprint and finish_pos in (2, 3):
pts += 2
breakdown.append(("bonus_podium", 2))

# 3) Malus
if p.get("disqualified", False):
pts -= 5
breakdown.append(("malus_disqualified", -5))

if p.get("dnf", False):
pts -= 3
breakdown.append(("malus_dnf", -3))

penalty_seconds = p.get("penalty_seconds", 0) or 0
if penalty_seconds >= 6:
pts -= 4
breakdown.append(("malus_penalty_6_or_more", -4))
elif 0 < penalty_seconds <= 5:
pts -= 3
breakdown.append(("malus_penalty_5_or_less", -3))

# 👉 Malus "gomma bucata" rimosso come richiesto

if p.get("finished", False) and isinstance(finish_pos, int):
if p.get("is_last_finisher", False):
pts -= 2
breakdown.append(("malus_last_finisher", -2))

if not p.get("dnf", False):
pos_lost = p.get("positions_lost", 0) or 0
if pos_lost > 0:
dec = 0.5 * pos_lost
pts -= dec
breakdown.append(("malus_positions_lost", -dec))

pts = round(pts, 2)
return pts, breakdown

@app.route("/compute", methods=["POST"])
def compute():
data = request.get_json()
drivers = data.get("drivers", [])
teams = data.get("teams", [])

pilot_points = {}
pilot_breakdowns = {}
for d in drivers:
pid = d.get("driver_id")
pts, breakdown = calc_pilot_points(d)
pilot_points[pid] = pts
pilot_breakdowns[pid] = breakdown

team_results = []
for t in teams:
tid = t.get("team_id")
players = t.get("players", [])
for pl in players:
pl_id = pl.get("player_id")
schierati = pl.get("drivers_to_field", [])
total = 0.0
breakdowns = {}
for dname in schierati:
val = pilot_points.get(dname, 0.0)
total += val
breakdowns[dname] = {"points": val, "breakdown": pilot_breakdowns.get(dname, [])}
team_results.append({
"team_id": tid,
"player_id": pl_id,
"drivers_fielded": schierati,
"total_points": round(total, 2),
"drivers": breakdowns
})

return jsonify({
"pilot_points": pilot_points,
"pilot_breakdowns": pilot_breakdowns,
"team_results": team_results
}), 200

if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)
