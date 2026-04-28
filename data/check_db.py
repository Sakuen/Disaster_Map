import sqlite3

c = sqlite3.connect('../backend/disasters.db').cursor()
print("Volcanoes in DB:", c.execute('SELECT COUNT(*) FROM disasters WHERE type="volcano"').fetchone()[0])
print("Tsunamis in DB:", c.execute('SELECT COUNT(*) FROM disasters WHERE type="tsunami"').fetchone()[0])
print("Earthquakes in DB:", c.execute('SELECT COUNT(*) FROM disasters WHERE type="earthquake"').fetchone()[0])
