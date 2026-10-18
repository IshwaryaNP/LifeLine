# Lifeline Triage - 2-Minute Demo Script

Follow this step-by-step path for a live presentation or screen-recorded evaluation of Lifeline Triage.

---

## 00:00 - 00:25: Setup & "Before Landfall" Preparedness (Tab 1)
1. **Show the Simulated Data Banner:**
   - Point out the persistent red banner: `"SIMULATED DATA ONLY — FOR CYCLONE TRIAGE DECISION-SUPPORT EVALUATION"`.
2. **Review Zone Risk Map:**
   - Click on **Tab 1: Before Landfall**.
   - Show the offline vector map displaying 12 zones of the fictional Sundarbari District colored by composite risk score.
   - Highlight the orange dashed outlines on **Z01 (Kalingapatnam Sands)**, **Z04 (Dhamra Creek Estuary)**, and **Z07 (Baruva Lowlands)**. Explain that these are vulnerable low-elevation zones with poor mobile connectivity (<20%).
3. **Official Warning & Targeted Directives:**
   - In the right-hand panel, note the pre-populated warning: *"MONSOON-V1 (Cat 4)"*.
   - Click **"Generate Targeted Preparedness Drafts"**.
   - Show how the system produces custom evacuation and HAM radio directives tailored to each zone's specific vulnerability factors.
   - Click **"Approve Directive"** to demonstrate human-in-the-loop sign-off.

---

## 00:25 - 01:15: Landfall Streaming & Triage Queue (Tab 2)
4. **Simulate Landfall:**
   - Navigate to **Tab 2: After Landfall (Live Queue)**.
   - Click **"Simulate Landfall"** with speed set to **5x** or **20x**.
   - Observe the progress bar advance from minute T+0 to T+240. Notice the raw reports streaming in and consolidating into prioritized incident clusters on both the map and queue.
5. **Demonstrate Duplicate Deduplication:**
   - Select an incident at the top of the queue (e.g., rescue crisis).
   - In the **Why This Rank** explanation card, point out:
     - The **Merged Reports** list showing 3 to 6 raw reports from multiple channels (SMS, calls, social) collapsed into a single actionable incident.
     - The transparent horizontal factor bars: **Need Severity**, **People Affected**, **Vulnerability**, and **Corroboration**, multiplied by the **Reliability Score**.
6. **Show Silence Gap Protection:**
   - Scroll to the bottom of the map panel to the **Silence Gap Panel**.
   - Show how **Z01, Z04, and Z07** are prominently flagged:
     - *"Received 0-2 reports, but high risk (Risk: 70-75%). Silence Index: 0.65+. Possible unreported need. Dispatch Scout / VHF Call."*
   - Explain why this matters: In standard volume-based systems, loud urban areas get all the ambulances while silent flooded areas are ignored. Lifeline Triage fixes this volume bias.

---

## 01:15 - 01:40: Coordinator Action & Mandatory Justification
7. **Perform a Priority Override:**
   - With the incident selected, click **"Override Priority"**.
   - Change the priority score (e.g., to `0.95`).
   - Enter a reason: `"Field volunteer on motorbike confirmed embankment breach near primary school."`
   - Click **"Record Override"**.
   - Show that the incident status immediately changes to **OVERRIDDEN** and reflects the new priority.

---

## 01:40 - 02:00: Results & Audit Trail (Tabs 3 & 4)
8. **Evaluation Metrics (Tab 3):**
   - Click **Tab 3: Evaluation & Results**.
   - Note the prominent caveat: *"Evaluated on simulated data with self-generated ground truth."*
   - Review the Recharts chart comparing Lifeline Triage against the raw volume baseline:
     - **3 out of 3 silent zones flagged** vs. **0 in baseline**.
     - **Duplicate-merge compression ratio** reducing cognitive overload by over 50%.
     - **0 fake/spam reports** infiltrating the top 10 incidents.
9. **Audit Trail (Tab 4):**
   - Click **Tab 4: Coordinator Audit Log**.
   - Show the recorded override with exact timestamp, user name, action type, and mandatory justification.
   - Conclude: *"Lifeline Triage empowers emergency controllers with clear explanations, surfaces the silent zones, and keeps humans firmly in control."*
