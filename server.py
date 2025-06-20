from flask import Flask, request, render_template, url_for
import os, json, re
from datetime import datetime, timezone
from pyvis.network import Network

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)




# Function to generate a Pyvis graph from pathping output
def visualize_pathping(output, html_file="static/pathping_graph.html"):
    net = Network(height='500px', width='100%', directed=True)
    lines = output.splitlines()

    parsing = False
    hops = []

    for line in lines:
        if line.strip().startswith("Hop") and "Lost/Sent" in line:
            parsing = True
            continue
        if parsing and re.match(r'^\s*\d+', line):
            # Sample: "  1     1ms     0/100 =  0%   0/100 =  0%   192.168.0.1"
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 5:
                ip = parts[-1]
                try:
                    loss_info = parts[-2]
                    loss_pct = int(re.search(r'(\d+)%', loss_info).group(1))
                except:
                    loss_pct = 0

                hops.append((ip, loss_pct))

    # Draw nodes and edges
    for i, (ip, loss) in enumerate(hops):
        color = "green" if loss < 10 else "orange" if loss < 50 else "red"
        label = f"{ip}\nLoss: {loss}%"
        net.add_node(ip, label=label, color=color, title=label)
        if i > 0:
            net.add_edge(hops[i - 1][0], ip)

    net.write_html(html_file)




@app.route("/report", methods=["POST"])
def receive_report():
    data = request.get_json()
    filename = f"{REPORTS_DIR}/{data['agent_id']}_{datetime.now(timezone.utc).isoformat()}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return {"status": "received"}, 200

@app.route("/")
def dashboard():
    files = sorted(os.listdir(REPORTS_DIR), reverse=True)[:10]
    data = []
    for f in files:
        with open(f"{REPORTS_DIR}/{f}") as fp:
            report = json.load(fp)
            data.append(report)

    # Generate Pyvis graph from latest report pathping
    latest = data[0] if data else None
    if latest and "pathping" in latest and latest["pathping"]:
        output = latest["pathping"][0]["output"]
        visualize_pathping(output, os.path.join(STATIC_DIR, "pathping_graph.html"))

    return render_template("dashboard.html", reports=data)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000, ssl_context=("cert.pem", "key.pem"))
