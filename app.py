from flask import Flask, request, jsonify

app = Flask(__name__)

# Funzione che calcola i punti di un pilota
def calc_pilot_points(p):
"""
p: dict con i dati del pilota
"""
pts = 0.0
breakdown = []

# --- Punteggio base dalla posizione in gara ---
if p.get("position_gp") is not None:
pos = p["position_gp"]
if pos == 1:
pts += 25
elif pos == 2:
pts += 18
elif pos == 3:
pts += 15
elif pos == 4:
pts += 12
elif pos == 5:
pts += 10
elif pos == 6:
pts += 8
elif pos == 7:
pts += 6
elif pos == 8:
pts += 4
elif pos == 9:
pts += 2
elif pos == 10:
pts += 1
breakdown.append(("position_gp", pts))

# --- Bonus ---
if p.get("pole", False):
pts += 2
breakdown.append(("bonus_pole", 2))

if p.get("fastest_lap", False):
pts += 1
breakdown.append(("bonus_fastest_lap", 1))

if p.get("driver_of_the_day", False):
pts += 1
breakdown.append(("bonus_driver_of_the_day", 1))

if p.get("fastest_pitstop", False):
pts += 2
breakdown.append(("bonus_fastest_pitstop", 2))

if p.get("from_back_and_points", False):
pts += 2
breakdown.append(("bonus_back_to_points", 2))

if p.get("positions_gained", 0) > 0:
bonus = 0.5 * p["positions_gained"]
pts += bonus
breakdown.append(("bonus_positions_gained", bonus))

if p.get("win_gp", False):
pts += 3
breakdown.append(("bonus_win", 3))

if p.get("podium_gp", False):
pts += 2
breakdown.append(("bonus_podium", 2))

# --- Malus ---
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

if p.get("last_in_race", False) and not p.get("dnf", False):
pts -= 2
breakdown.append(("malus_last_in_race", -2))

if p.get("no_q1", False):
pts -= 1
breakdown.append(("malus_no_q1", -1))

if p.get("positions_lost", 0) > 0 and not p.get("dnf", False):
malus = 0.5 * p["positions_lost"]
pts -= malus
breakdown.append(("malus_positions_lost", -malus))

return pts, breakdown


# --- API ---
@app.route("/calculate", methods=["POST"])
def calculate():
data = request.get_json()
players = data.get("players", [])

results = {}
for player in players:
total = 0
details = []
for pilot in player.get("pilots", []):
pts, breakdown = calc_pilot_points(pilot)
total += pts
details.append({"pilot": pilot["name"], "points": pts, "breakdown": breakdown})
results[player["name"]] = {"total": total, "details": details}

return jsonify(results)


if __name__ == "__main__":
app.run(host="0.0.0.0", port=5000)
