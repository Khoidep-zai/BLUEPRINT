---
name: office-master-hub
description: Central orchestrator for all Office document generation, analysis, and modification (.docx, .xlsx, .pptx, .pdf) in the NAB project using the single-binary OfficeCLI tool. Directs requests to specialized skills (financial models, dashboards, pitch decks, BRD/PRD documents) with native validation and zero external Python/LibreOffice dependencies.
---

# NAB Office Document Automation Master Hub (`officecli`)

## Overview
This skill provides the centralized coordination for generating, auditing, and formatting all Microsoft Office documents (`.docx`, `.xlsx`, `.pptx`) and PDF reports in the NAB banking ecosystem. In this environment, **`OfficeCLI` (`officecli.exe`)** is preinstalled and configured as the **primary, high-performance engine**.

> [!IMPORTANT]
> **No Python/LibreOffice scripts needed:** `officecli` handles reading, editing (DOM & OpenXML), formula calculation, schema validation, and visual rendering natively.

---

## Specialized Skill Directory & Routing

Depending on the deliverable requested, immediately delegate to the appropriate specialized sub-skill:

| Document Type & Banking Deliverable | Primary Sub-Skill | Auxiliary Skill |
| :--- | :--- | :--- |
| **NAB Business Spec / PRD / BRD / ADR (`.docx`)** | `officecli-docx` | `docx` + `doc-coauthoring` |
| **Financial Models, Cash Flow, Capital Allocation (`.xlsx`)** | `officecli-financial-model` | `xlsx` |
| **Data Dashboards, KPI Tracking, Reconcile Sheets (`.xlsx`)** | `officecli-data-dashboard` | `officecli-xlsx` |
| **SteerCo Presentations, Architecture Pitch Decks (`.pptx`)** | `officecli-pitch-deck` | `officecli-pptx` + `pptx` |
| **Interactive Slide Transitions / Morph Animations (`.pptx`)** | `morph-ppt` | `morph-ppt-3d` |
| **Customer Application Forms / Fillable Documents (`.docx`)** | `officecli-word-form` | `officecli-docx` |
| **Regulatory APRA / AUSTRAC Compliance Papers (`.docx`)** | `officecli-academic-paper` | `pdf` |
| **Incident Post-mortems, Release Notes, Internal FAQs** | `internal-comms` | `officecli-docx` |

> **Model note (all runtimes):** each sub-skill name above maps to a file at `.agents/skills/<name>/SKILL.md` — read that file before executing (Antigravity: `view_file`). If your catalog does not list a name (some runtimes only auto-register top-level skills), open the path directly instead of skipping the step.

---

## NAB Banking Standards for Office Documents

### 1. Word Documents (`.docx`)
- **Cover Page:** Formal NAB document header with Title, Subtitle, Author, Date, Security Classification (`NAB Internal` / `Confidential`).
- **Version Control Table:** Revision number, Author, Date, Change Description, Approver.
- **Requirements Traceability Matrix (RTM):** Explicit cross-reference table linking:
  $$\text{Business Rule ID} \longrightarrow \text{User Story ID} \longrightarrow \text{API Endpoint} \longrightarrow \text{Test Case ID}$$
- **Typography:** Clear visual hierarchy (Heading 1: 18pt bold, Heading 2: 14pt bold, Body: 11pt Calibri/Arial, 1.15 line spacing).

### 2. Excel Spreadsheets (`.xlsx`)
- **Three-Sheet Architecture:**
  1. `Inputs & Assumptions`: Input parameters in **Blue font** (`#0000FF`).
  2. `Calculations`: Formula engine in **Black font** (`#000000`). **NEVER hardcode calculated totals.** Always write dynamic formulas (`=SUM()`, `=XLOOKUP()`, `=NPV()`).
  3. `Summary & KPIs`: Visual KPI cards, Net Interest Margin ($NIM$), Cost-to-Income ($CIR$), and executive charts.
- **Currency & Precision:** Format AUD as `"$#,##0.00"` with Banker's Rounding (`HALF_EVEN`).
- **Error Guarantee:** Must pass `officecli validate` with zero `#REF!`, `#VALUE!`, `#DIV/0!`, or `#N/A` errors.

### 3. PowerPoint Presentations (`.pptx`)
- **Aspect Ratio:** 16:9 Widescreen standard.
- **Minto Pyramid Principle:** Every slide title MUST be an **Action Title** (a complete takeaway sentence, e.g., *"Automated Fraud Detection Reduces Operational Loss by 34%"*), never a passive label (e.g., *"Fraud Statistics"*).
- **Layout Rhythm:** Alternate between KPI cards (3-4 columns), Comparison tables, and Process Flow diagrams.
- **Zero Text Overflow:** Ensure text frames have sufficient margins and do not clip or extend beyond the slide boundary.

---

## The 3-Step High-Performance `OfficeCLI` Execution Loop

When creating or modifying documents, always follow this atomic workflow:

```text
[BƯỚC 1: TRA CỨU SCHEMA & RESIDENT]
  ├─ Khi không chắc chắn tên thuộc tính: officecli help <docx|xlsx|pptx> <element>
  └─ Mở resident process (nếu làm việc phiên dài): officecli open document.docx
         │
         ▼
[BƯỚC 2: THỰC THI BATCH NGUYÊN TỬ]
  ├─ Sử dụng lệnh `officecli batch <file> --commands '[...]'`
  └─ Gom toàn bộ thao tác add/set vào 1 JSON array để hoàn tất trong 1 chu kỳ I/O duy nhất
         │
         ▼
[BƯỚC 3: KIỂM CHỨNG THỊ GIÁC & VALIDATE]
  ├─ Kiểm tra tính hợp lệ OpenXML: officecli validate document.docx
  ├─ Kiểm tra hiển thị thị giác: officecli view document.docx html (hoặc render ảnh)
  └─ Đóng resident process: officecli close document.docx
```
