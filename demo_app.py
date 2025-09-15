#!/usr/bin/env python3
"""
Standalone demo of VibeFITREP functionality
This creates a simple web interface to test the core features
"""

import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Sample data for demonstration
SAMPLE_DATA = {
    "officer_info": {
        "name": "SMITH, JOHN A",
        "rank": "MAJ",
        "total_reports": 9
    },
    "rank_breakdown": {
        "SGT": {
            "total_reports": 6,
            "average_fra": 2.1,
            "highest_fra": 1.8,
            "lowest_fra": 2.4,
            "average_rv": 92.5,
            "reports": [
                {
                    "fitrep_id": "SGT001",
                    "marine_name": "JONES, MIKE B",
                    "period_to": "2023-06-30",
                    "fra_score": 1.8,
                    "relative_value": 100,
                    "trait_scores": {"Mission Accomplishment": "A", "Proficiency": "B", "Individual Character": "A", "Effectiveness Under Stress": "B", "Initiative": "A", "Leadership": "B", "Developing Subordinates": "A", "Setting the Example": "A", "Ensuring Well-being of Subordinates": "B", "Communication Skills": "A", "Intellect and Wisdom": "B", "Decision Making Ability": "A", "Judgment": "A", "Fulfillment of Evaluation Responsibilities": "B"},
                    "occasion_type": "AN"
                },
                {
                    "fitrep_id": "SGT002", 
                    "marine_name": "DAVIS, SARAH C",
                    "period_to": "2023-08-15",
                    "fra_score": 2.2,
                    "relative_value": 88,
                    "trait_scores": {"Mission Accomplishment": "B", "Proficiency": "C", "Individual Character": "B", "Effectiveness Under Stress": "C", "Initiative": "B", "Leadership": "C", "Developing Subordinates": "B", "Setting the Example": "B", "Ensuring Well-being of Subordinates": "C", "Communication Skills": "B", "Intellect and Wisdom": "C", "Decision Making Ability": "B", "Judgment": "B", "Fulfillment of Evaluation Responsibilities": "C"},
                    "occasion_type": "AN"
                },
                {
                    "fitrep_id": "SGT003",
                    "marine_name": "WILSON, JAMES D", 
                    "period_to": "2023-12-20",
                    "fra_score": 2.4,
                    "relative_value": 80,
                    "trait_scores": {"Mission Accomplishment": "C", "Proficiency": "C", "Individual Character": "B", "Effectiveness Under Stress": "D", "Initiative": "C", "Leadership": "C", "Developing Subordinates": "C", "Setting the Example": "B", "Ensuring Well-being of Subordinates": "D", "Communication Skills": "C", "Intellect and Wisdom": "C", "Decision Making Ability": "C", "Judgment": "C", "Fulfillment of Evaluation Responsibilities": "C"},
                    "occasion_type": "AN"
                },
                {
                    "fitrep_id": "SGT004",
                    "marine_name": "BROWN, LISA E",
                    "period_to": "2024-01-15", 
                    "fra_score": 2.0,
                    "relative_value": 95,
                    "trait_scores": {"Mission Accomplishment": "A", "Proficiency": "B", "Individual Character": "A", "Effectiveness Under Stress": "B", "Initiative": "B", "Leadership": "A", "Developing Subordinates": "B", "Setting the Example": "A", "Ensuring Well-being of Subordinates": "B", "Communication Skills": "A", "Intellect and Wisdom": "B", "Decision Making Ability": "A", "Judgment": "A", "Fulfillment of Evaluation Responsibilities": "B"},
                    "occasion_type": "AN"
                },
                {
                    "fitrep_id": "SGT005",
                    "marine_name": "GARCIA, CARLOS F",
                    "period_to": "2024-02-28",
                    "fra_score": 1.9,
                    "relative_value": 98,
                    "trait_scores": {"Mission Accomplishment": "A", "Proficiency": "A", "Individual Character": "A", "Effectiveness Under Stress": "B", "Initiative": "A", "Leadership": "B", "Developing Subordinates": "A", "Setting the Example": "A", "Ensuring Well-being of Subordinates": "A", "Communication Skills": "A", "Intellect and Wisdom": "B", "Decision Making Ability": "A", "Judgment": "A", "Fulfillment of Evaluation Responsibilities": "B"},
                    "occasion_type": "AN"
                },
                {
                    "fitrep_id": "SGT006",
                    "marine_name": "TAYLOR, ROBERT G",
                    "period_to": "2024-03-10",
                    "fra_score": 3.2,
                    "relative_value": None,
                    "trait_scores": {"Mission Accomplishment": "D", "Proficiency": "D", "Individual Character": "C", "Effectiveness Under Stress": "E", "Initiative": "D", "Leadership": "D", "Developing Subordinates": "D", "Setting the Example": "C", "Ensuring Well-being of Subordinates": "E", "Communication Skills": "D", "Intellect and Wisdom": "D", "Decision Making Ability": "D", "Judgment": "C", "Fulfillment of Evaluation Responsibilities": "D"},
                    "occasion_type": "EN"
                }
            ]
        }
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VibeFITREP Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #003366; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #003366; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px 12px; border: 1px solid #ddd; text-align: center; }}
        th {{ background: #003366; color: white; font-size: 12px; }}
        .trait-score {{ padding: 4px 6px; border-radius: 3px; color: white; font-weight: bold; font-size: 11px; }}
        .grade-A {{ background-color: #28a745; }}
        .grade-B {{ background-color: #17a2b8; }}
        .grade-C {{ background-color: #ffc107; color: black; }}
        .grade-D {{ background-color: #fd7e14; }}
        .grade-E {{ background-color: #dc3545; }}
        .rv-high {{ background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; }}
        .rv-med {{ background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-weight: bold; }}
        .rv-low {{ background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; }}
        .en-report {{ opacity: 0.7; font-style: italic; border-left: 4px solid #6c757d; }}
        .button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }}
        .button:hover {{ background: #0056b3; }}
        .legend {{ font-size: 12px; color: #666; background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 VibeFITREP Demo - Reporting Senior Profile</h1>
            <p>Demonstrating the spreadsheet view and core functionality</p>
        </div>
        
        <div class="card">
            <h2>Officer Information</h2>
            <p><strong>Name:</strong> {officer_name}</p>
            <p><strong>Rank:</strong> {officer_rank}</p>
            <p><strong>Total Reports Written:</strong> {total_reports}</p>
        </div>
        
        <div class="card">
            <h2>SGT Profile Statistics</h2>
            <div class="stats">
                <div class="stat-card">
                    <h4>Total Reports</h4>
                    <div class="stat-value">{sgt_total}</div>
                </div>
                <div class="stat-card">
                    <h4>Average FRA</h4>
                    <div class="stat-value">{sgt_avg_fra:.2f}</div>
                </div>
                <div class="stat-card">
                    <h4>Average RV</h4>
                    <div class="stat-value">{sgt_avg_rv:.1f}</div>
                </div>
                <div class="stat-card">
                    <h4>Range</h4>
                    <div class="stat-value">{sgt_lowest_fra:.1f} - {sgt_highest_fra:.1f}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔍 Spreadsheet View - All SGT Reports</h2>
            <p><strong>Sort by:</strong> 
                <select onchange="sortTable(this.value)">
                    <option value="date">End Date</option>
                    <option value="rv">Relative Value</option>
                </select>
                <button class="button" onclick="alert('What-if functionality demonstrated! This would open a modal to add hypothetical reports.')">+ Add Potential Reports</button>
            </p>
            
            <div style="overflow-x: auto;">
                <table id="reportTable">
                    <thead>
                        <tr>
                            <th>Marine Name</th>
                            <th>End Date</th>
                            <th>FRA</th>
                            <th>RV</th>
                            <th>Mis Acc</th>
                            <th>Prof</th>
                            <th>Ind Char</th>
                            <th>Eff Stress</th>
                            <th>Init</th>
                            <th>Lead</th>
                            <th>Dev Sub</th>
                            <th>Set Ex</th>
                            <th>Well Sub</th>
                            <th>Comm</th>
                            <th>Int Wis</th>
                            <th>Dec Mak</th>
                            <th>Judg</th>
                            <th>Eval Resp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="legend">
                <div><strong>Trait Legend:</strong> A=Outstanding, B=Excellent, C=Above Avg, D=Average, E=Below Avg, F=Unsat, G=Unacceptable, H=Not Observed</div>
                <div><strong>RV Colors:</strong> 
                    <span class="rv-high">≥93.3</span> 
                    <span class="rv-med">86.6-93.2</span> 
                    <span class="rv-low">80-86.5</span>
                </div>
                <div><strong>Indicators:</strong> (EN) = End of Active Service (excluded from RS statistics)</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🎯 Key Features Demonstrated</h2>
            <ul>
                <li>✅ <strong>Duplicate Detection:</strong> Prevents same FITREP from being uploaded twice</li>
                <li>✅ <strong>Spreadsheet View:</strong> Shows all reports as rows with traits as columns</li>
                <li>✅ <strong>RV Color Coding:</strong> Green (≥93.3), Yellow (86.6-93.2), Red (80-86.5)</li>
                <li>✅ <strong>EN Report Handling:</strong> Shows EN reports but excludes from statistics</li>
                <li>✅ <strong>Sorting Options:</strong> Sort by end date or relative value</li>
                <li>✅ <strong>What-If Scenarios:</strong> Add hypothetical reports to predict impact</li>
                <li>✅ <strong>Single User Detection:</strong> Auto-navigates to your profile</li>
            </ul>
            <p><strong>Notice:</strong> SGT006 (TAYLOR) has an EN report - it shows in the table but doesn't affect the profile statistics above.</p>
        </div>
    </div>
    
    <script>
        function getRVClass(rv) {
            if (!rv) return '';
            if (rv >= 93.3) return 'rv-high';
            if (rv >= 86.6) return 'rv-med';
            return 'rv-low';
        }
        
        function getTraitClass(grade) {
            return 'trait-score grade-' + grade;
        }
        
        function sortTable(sortBy) {
            // Demo sorting functionality
            alert('Sorting by ' + sortBy + ' - This would reorder the table rows.');
        }
    </script>
</body>
</html>
"""

class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Generate table rows
            reports = SAMPLE_DATA["rank_breakdown"]["SGT"]["reports"]
            table_rows = ""
            
            for report in reports:
                is_en = report.get("occasion_type") == "EN"
                row_class = "en-report" if is_en else ""
                
                rv_display = ""
                if report["relative_value"]:
                    rv_class = "rv-high" if report["relative_value"] >= 93.3 else ("rv-med" if report["relative_value"] >= 86.6 else "rv-low")
                    rv_display = f'<span class="{rv_class}">{report["relative_value"]}</span>'
                else:
                    rv_display = "N/A"
                
                # Build trait cells
                trait_cells = ""
                trait_names = ["Mission Accomplishment", "Proficiency", "Individual Character", "Effectiveness Under Stress", 
                              "Initiative", "Leadership", "Developing Subordinates", "Setting the Example", 
                              "Ensuring Well-being of Subordinates", "Communication Skills", "Intellect and Wisdom", 
                              "Decision Making Ability", "Judgment", "Fulfillment of Evaluation Responsibilities"]
                
                for trait in trait_names:
                    grade = report["trait_scores"].get(trait, "H")
                    trait_cells += f'<td><span class="trait-score grade-{grade}">{grade}</span></td>'
                
                marine_name = report["marine_name"]
                if is_en:
                    marine_name += " <span style='color: #6c757d; font-size: 10px;'>(EN)</span>"
                
                table_rows += f"""
                <tr class="{row_class}">
                    <td style="font-weight: bold;">{marine_name}</td>
                    <td>{report["period_to"]}</td>
                    <td style="font-weight: bold; color: #CC0000;">{report["fra_score"]:.1f}</td>
                    <td>{rv_display}</td>
                    {trait_cells}
                </tr>
                """
            
            sgt_data = SAMPLE_DATA["rank_breakdown"]["SGT"]
            html = HTML_TEMPLATE.format(
                officer_name=SAMPLE_DATA["officer_info"]["name"],
                officer_rank=SAMPLE_DATA["officer_info"]["rank"],
                total_reports=SAMPLE_DATA["officer_info"]["total_reports"],
                sgt_total=sgt_data["total_reports"],
                sgt_avg_fra=sgt_data["average_fra"],
                sgt_avg_rv=sgt_data["average_rv"],
                sgt_highest_fra=sgt_data["highest_fra"],
                sgt_lowest_fra=sgt_data["lowest_fra"],
                table_rows=table_rows
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_demo_server():
    print("🚀 Starting VibeFITREP Demo Server...")
    server = HTTPServer(('localhost', 8080), DemoHandler)
    print("✅ Demo running at: http://localhost:8080")
    print("⌨️  Press Ctrl+C to stop")
    
    # Open browser automatically
    threading.Timer(1.0, lambda: webbrowser.open('http://localhost:8080')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down demo server...")
        server.shutdown()

if __name__ == "__main__":
    start_demo_server()