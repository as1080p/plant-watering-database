from flask import Flask, render_template_string, request, redirect, jsonify
import psycopg2
from datetime import datetime

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(
        dbname="plant_watering",
        user="postgres",
        password="admin",  # change if needed
        host="localhost",
        port=5433
    )

# ---------------------------------------------------------------------
# 🌱 HTML Template (Dashboard + Chart.js Modal)
# ---------------------------------------------------------------------
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Plant Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { background: #f2fdf2; }
    .card:hover { transform: scale(1.03); transition: 0.3s; }
    .progress-bar { transition: width 0.8s ease-in-out; }
  </style>
</head>
<body>
<div class="container py-4">
  <h2 class="mb-4 text-center">🌿 Smart Plant Dashboard</h2>
  <div class="d-flex justify-content-end mb-3">
    <a href="/logs" class="btn btn-outline-secondary">🧾 View Water Log</a>
  </div>
  <div class="row g-4">
    {% for r in rows %}
    <div class="col-md-4">
      <div class="card shadow-sm h-100">
        <img src="{{ url_for('static', filename='images/' ~ r[1] ~ '.jpg') }}" class="card-img-top" alt="{{ r[1] }}">
        <div class="card-body">
          <h5 class="card-title">{{ r[1] }}</h5>
          <p class="card-text mb-1">Moisture: {{ r[3]|round(1) }}%</p>
          <div class="progress mb-3" style="height: 20px;">
            {% set perc = (r[3] / 100 * 100) %}
            <div class="progress-bar {% if r[3] < r[2] %}bg-danger{% else %}bg-success{% endif %}" role="progressbar"
              style="width: {{ perc }}%;" aria-valuenow="{{ r[3] }}" aria-valuemin="0" aria-valuemax="100">
              {{ r[3]|round(1) }}%
            </div>
          </div>
          <p class="card-text"><strong>Threshold:</strong> {{ r[2] }}%</p>
          <form method="post" action="/water" class="mb-2">
            <input type="hidden" name="plantid" value="{{ r[0] }}">
            <button type="submit" class="btn btn-primary w-100">💧 Water</button>
          </form>
          <form method="post" action="/dewater" class="mb-2">
            <input type="hidden" name="plantid" value="{{ r[0] }}">
            <button type="submit" class="btn btn-warning w-100">🌵 Dewater</button>
          </form>
          <button class="btn btn-outline-success w-100" onclick="showChart({{ r[0] }}, '{{ r[1] }}')">📈 Moisture History</button>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<!-- 📊 Modal for Moisture Chart -->
<div class="modal fade" id="chartModal" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Moisture History</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <canvas id="moistureChart"></canvas>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js"></script>
<script>
let chartInstance;

function showChart(plantID, plantName) {
  fetch(`/moisture_history/${plantID}`)
    .then(res => res.json())
    .then(data => {
      const labels = data.map(d => d[1]);
      const values = data.map(d => d[0]);
      const ctx = document.getElementById('moistureChart').getContext('2d');
      if (chartInstance) chartInstance.destroy();
      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Moisture (%)',
            data: values,
            borderColor: 'green',
            tension: 0.3,
            fill: true,
            backgroundColor: 'rgba(0,255,0,0.1)'
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: true, labels: { color: 'green' } } },
          scales: { y: { beginAtZero: true, max: 100 } }
        }
      });
      new bootstrap.Modal(document.getElementById('chartModal')).show();
    });
}
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------
# 🌿 Routes
# ---------------------------------------------------------------------
@app.route('/')
def idx():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.PlantID, p.PlantName, p.MoistureThreshold, s.MoistureValue
        FROM Plant p
        JOIN (
            SELECT sr1.PlantID, sr1.MoistureValue, sr1.ReadingTime
            FROM SoilReading sr1
            WHERE sr1.ReadingTime = (
                SELECT MAX(sr2.ReadingTime)
                FROM SoilReading sr2
                WHERE sr2.PlantID = sr1.PlantID
            )
        ) s ON p.PlantID = s.PlantID
        ORDER BY p.PlantName;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(TEMPLATE, rows=rows)

@app.route('/water', methods=['POST'])
def water():
    pid = int(request.form['plantid'])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT water_plant(%s, %s, %s);", (pid, 300.0, 'UI'))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/dewater', methods=['POST'])
def dewater():
    pid = int(request.form['plantid'])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT dewater_plant(%s, %s, %s);", (pid, 300.0, 'UI'))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/moisture_history/<int:plant_id>')
def moisture_history(plant_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT MoistureValue, ReadingTime 
        FROM SoilReading 
        WHERE PlantID = %s 
        ORDER BY ReadingTime DESC LIMIT 10;
    """, (plant_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data[::-1])

@app.route('/logs')
def logs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.PlantName, w.Amount, w.WateredOn, w.Method
        FROM WaterLog w 
        JOIN Plant p ON w.PlantID = p.PlantID
        ORDER BY w.WateredOn DESC;
    """)
    logs = cur.fetchall()
    cur.close()
    conn.close()
    table_html = "<div class='container py-4'><h3>🧾 Watering History</h3><table class='table table-striped table-bordered'><thead><tr><th>Plant</th><th>Amount</th><th>Time</th><th>Method</th></tr></thead><tbody>"
    for l in logs:
        table_html += f"<tr><td>{l[0]}</td><td>{l[1]}</td><td>{l[2]}</td><td>{l[3]}</td></tr>"
    table_html += "</tbody></table><a href='/' class='btn btn-outline-success'>⬅ Back to Dashboard</a></div>"
    return table_html

if __name__ == '__main__':
    app.run(debug=True)
