"""
Vivrta Systems — SAP Code Analyser
Phase 1 · Production-ready Streamlit application
Reads a .txt or .abap file, sends it to the Anthropic API,
and returns a plain-English business-process explanation.
"""

import re
import textwrap
import anthropic
import streamlit as st
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vivrta.AI | SAP Code Analyser",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, footer, header  { visibility: hidden; }

        /* Light blue-grey page background */
        .stApp { background-color: #eef2fb; }

        .block-container {
            padding-top: 0 !important;
            padding-bottom: 3rem;
            max-width: 860px;
        }

        /* ── Sidebar ──────────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg,#0f0f23 0%,#1a1a3e 60%,#0f172a 100%) !important;
            border-right: 1px solid #2d2d5e;
        }
        [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        [data-testid="stSidebarContent"] { padding: 0 !important; }

        /* Sidebar toggle — visible in both open and closed states */
        /* Collapse button inside the open sidebar */
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarCollapseButton"] > button {
            background: #1e1b4b !important;
            border: 1px solid #3730a3 !important;
            border-radius: 6px !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stSidebarCollapseButton"] button svg {
            stroke: #a5b4fc !important;
            fill: #a5b4fc !important;
        }
        /* Re-open button in main area when sidebar is collapsed — all known selectors */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"],
        button[aria-label="Open sidebar"],
        button[title="Open sidebar"],
        .css-1rs6os, .css-17ziqus {
            background-color: #1e1b4b !important;
            border-radius: 0 8px 8px 0 !important;
            border: 1px solid #3730a3 !important;
            border-left: none !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: flex !important;
            z-index: 9999 !important;
        }
        [data-testid="collapsedControl"] svg,
        [data-testid="stSidebarCollapsedControl"] svg,
        button[aria-label="Open sidebar"] svg {
            fill: #a5b4fc !important;
            stroke: #a5b4fc !important;
        }

        .sb-logo {
            padding: 1.6rem 1.4rem 1.2rem;
            border-bottom: 1px solid #1e293b;
        }
        .sb-wordmark {
            font-size: 1.55rem; font-weight: 800;
            letter-spacing: -0.02em; color: #fff !important; line-height: 1;
        }
        .sb-wordmark em { font-style: normal; color: #818cf8 !important; }
        .sb-tagline {
            font-size: 0.68rem; color: #64748b !important;
            letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.3rem;
        }
        .sb-sec { padding: 1rem 1.4rem 0.4rem; }
        .sb-sec-title {
            font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em;
            text-transform: uppercase; color: #334155 !important; margin-bottom: 0.7rem;
        }
        .sb-row {
            display: flex; align-items: flex-start; gap: 0.55rem;
            margin-bottom: 0.55rem; font-size: 0.8rem;
            color: #cbd5e1 !important; line-height: 1.35;
        }
        .sb-icon { font-size: 0.82rem; margin-top: 0.05rem; flex-shrink: 0; }
        .sb-step {
            display: flex; align-items: flex-start;
            gap: 0.65rem; margin-bottom: 0.7rem;
        }
        .sb-num {
            width: 18px; height: 18px; border-radius: 50%;
            background: #3730a3; color: #fff !important;
            font-size: 0.65rem; font-weight: 700;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; margin-top: 0.06rem;
        }
        .sb-step-txt { font-size: 0.78rem; color: #94a3b8 !important; line-height: 1.35; }
        .sb-step-txt strong { color: #c7d2fe !important; }
        .sb-badge {
            display: inline-block; background: #1e1b4b;
            border: 1px solid #3730a3; color: #a5b4fc !important;
            border-radius: 999px; padding: 0.18rem 0.6rem;
            font-size: 0.66rem; font-weight: 600;
            margin: 0.15rem 0.1rem 0 0;
        }
        .sb-divider { border: none; border-top: 1px solid #1e293b; margin: 0.8rem 1.4rem; }
        .sb-footer {
            padding: 1rem 1.4rem 1.4rem; border-top: 1px solid #1e293b;
            font-size: 0.66rem; color: #334155 !important; line-height: 1.65;
        }

        /* ── Page header strip ────────────────────────────────────────── */
        .page-header {
            background: linear-gradient(90deg,#1e1b4b 0%,#312e81 100%);
            padding: 1.4rem 2rem 1.3rem;
            margin-bottom: 1.75rem;
            display: flex; align-items: center;
            justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;
        }
        .ph-left { display: flex; align-items: center; gap: 0.9rem; }
        .ph-wordmark {
            font-size: 1.2rem; font-weight: 800;
            color: #fff !important; letter-spacing: -0.02em;
        }
        .ph-wordmark em { font-style: normal; color: #818cf8 !important; }
        .ph-div { width: 1px; height: 28px; background: #3730a3; flex-shrink: 0; }
        .ph-stack { display: flex; flex-direction: column; gap: 0.1rem; }
        .ph-sub  { font-size: 0.88rem; color: #e2e8f0 !important; font-weight: 600; }
        .ph-tagline { font-size: 0.72rem; color: #94a3b8 !important; font-weight: 400; }
        .ph-pills { display: flex; gap: 0.35rem; flex-wrap: wrap; }
        .ph-pill {
            background: rgba(99,102,241,0.2);
            border: 1px solid rgba(129,140,248,0.25);
            color: #c7d2fe !important; border-radius: 999px;
            padding: 0.16rem 0.6rem; font-size: 0.67rem; font-weight: 500;
        }

        /* ── Section label ────────────────────────────────────────────── */
        .sec-label {
            font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
            text-transform: uppercase; color: #6366f1; margin-bottom: 0.55rem;
        }

        /* ── Upload zone ──────────────────────────────────────────────── */
        .upload-zone {
            background: #fff; border: 2px dashed #c7d2fe;
            border-radius: 12px; padding: 0.9rem 1.2rem 0.5rem;
        }
        .uz-hint { font-size: 0.77rem; color: #94a3b8; }
        .file-ok {
            background: #f0fdf4; border: 1px solid #bbf7d0;
            border-left: 3px solid #22c55e; border-radius: 7px;
            padding: 0.55rem 0.9rem; font-size: 0.82rem;
            color: #166534; margin-top: 0.5rem;
        }

        /* ── Report sections card ─────────────────────────────────────── */
        .rp-card {
            background: #fff; border: 1px solid #e0e7ff;
            border-radius: 12px; padding: 0.85rem 1.1rem;
        }
        .rp-item {
            display: flex; align-items: flex-start;
            gap: 0.6rem; padding: 0.42rem 0;
            border-bottom: 1px solid #f1f5f9;
        }
        .rp-item:last-child { border-bottom: none; }
        .rp-dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: #6366f1; flex-shrink: 0; margin-top: 0.4rem;
        }
        .rp-text { font-size: 0.79rem; color: #374151; line-height: 1.35; }
        .rp-text strong { color: #1e1b4b; font-weight: 600; }

        /* ── Analyse button ───────────────────────────────────────────── */
        .stButton > button {
            background: linear-gradient(135deg,#4f46e5 0%,#6366f1 100%);
            color: white !important; border: none; border-radius: 10px;
            padding: 0.65rem 2rem; font-weight: 700; font-size: 0.92rem;
            width: 100%; letter-spacing: 0.01em;
            box-shadow: 0 3px 12px rgba(99,102,241,0.3);
            transition: all 0.15s;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg,#4338ca 0%,#4f46e5 100%);
            box-shadow: 0 5px 18px rgba(99,102,241,0.4);
            transform: translateY(-1px);
        }
        .stButton > button:disabled {
            background: #e5e7eb !important; color: #9ca3af !important;
            box-shadow: none; transform: none;
        }

        /* ── Result display ───────────────────────────────────────────── */
        .result-hdr {
            background: linear-gradient(90deg,#1e1b4b 0%,#312e81 100%);
            border-radius: 12px 12px 0 0; padding: 0.8rem 1.4rem;
            display: flex; align-items: center; gap: 0.6rem;
        }
        .rh-icon  { font-size: 1rem; }
        .rh-title { font-size: 0.87rem; font-weight: 700; color: #fff !important; }
        .rh-file  { margin-left: auto; font-size: 0.69rem; color: #7c8cba !important; }
        .result-body {
            background: #fff; border: 1px solid #e0e7ff; border-top: none;
            border-radius: 0 0 12px 12px; padding: 1.6rem 1.9rem;
            line-height: 1.75; color: #111827; font-size: 0.93rem;
        }

        /* ── Download buttons ─────────────────────────────────────────── */
        .stDownloadButton > button {
            background: #fff; color: #4f46e5 !important;
            border: 1.5px solid #c7d2fe; border-radius: 9px;
            padding: 0.55rem 1.2rem; font-weight: 600; font-size: 0.85rem;
            transition: all 0.15s;
        }
        .stDownloadButton > button:hover { background: #eef2ff; border-color: #6366f1; }

        hr.light { border: none; border-top: 1px solid #e0e7ff; margin: 1.5rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Mode definitions ──────────────────────────────────────────────────────────
MODES = {
    "single":  "🔍  Single Program Analysis",
    "bundle":  "📦  Repository Bundle Analysis",
    "s4hana":  "🚀  S/4HANA Readiness Scan",
}

MODE_DESCRIPTIONS = {
    "single": "Deep analysis of one ABAP program — business process, data flow, risk, and glossary.",
    "bundle": "Upload 2–15 SAP objects together. Get individual summaries plus cross-program intelligence: shared tables, dependencies, naming compliance, and an estate overview.",
    "s4hana": "Upload 1–15 programs. Every file is scored Red / Amber / Green against ~40 S/4HANA migration patterns with a prioritised remediation plan.",
}

MODE_SECTIONS = {
    "single": [
        "<strong>Executive Brief</strong> — leadership summary (front page)",
        "Business Process Summary",
        "Key SAP Tables Identified",
        "Data Flow",
        "Business Risk & Observations",
        "Plain-English SAP Glossary",
    ],
    "bundle": [
        "<strong>Executive Brief</strong> — leadership summary (front page)",
        "Estate Executive Summary",
        "Cross-Program Object Inventory",
        "Shared Tables & Dependencies",
        "Naming Convention & Quality Audit",
        "Individual Program Summaries",
        "Consolidated Risk Register",
    ],
    "s4hana": [
        "<strong>Executive Brief</strong> — leadership summary (front page)",
        "S/4HANA Readiness Scorecard",
        "Critical Blockers (Red)",
        "Warnings Requiring Review (Amber)",
        "Best-Practice Confirmations (Green)",
        "Prioritised Remediation Plan",
        "Estimated Migration Effort",
        "<strong>Scope Estimate</strong> — total remediation developer days",
    ],
}

ACCEPTED_TYPES = ["txt", "abap", "csv", "pdf"]

# ── System prompt: Single Program ─────────────────────────────────────────────
SYSTEM_PROMPT_SINGLE = """
You are an expert SAP functional consultant and technical analyst with deep knowledge of
SAP FI, CO, SD, MM, FI-AA, and custom ABAP development.

Analyse the uploaded SAP ABAP code and produce a structured report for a non-technical
business audience (CFO, Finance Director, or Audit Committee).

ACCURACY RULES — read before writing a single word:

RULE 1 — EVIDENCE FIRST: Every finding must be anchored to a visible code statement.
  Identify the specific ABAP statement, field assignment, or value that supports it.
  If you cannot point to it, do not state it as a finding.

RULE 2 — FOUR CONFIDENCE TIERS (use exactly one per finding):
  [HIGH CONFIDENCE]         — directly visible in code; quote the evidence inline
  [MEDIUM — VERIFY]         — visible but impact depends on config or template
  [LOW — NEEDS CONTEXT]     — general SAP concern, not confirmable from code alone
  [INFERRED — NOT IN CODE]  — SAP best-practice note, not specific to this code;
                              label it clearly so the reader knows

RULE 3 — NEVER INVENT SAP OBJECT NAMES: Do not state a SAP Note number,
  transaction code, FM name, BAPI name, table name, or field name unless it
  appears in the uploaded code. If a standard replacement is relevant but you
  are not 100% certain of the exact name, write:
  "SAP provides a standard replacement — verify in official documentation."

RULE 4 — SEPARATE CODE FROM SAP STANDARD: Always distinguish:
  (a) What THIS CODE does — observable from ABAP statements
  (b) What SAP standard behaviour would be — general SAP knowledge

RULE 5 — HIGH CONFIDENCE MUST QUOTE EVIDENCE: Every [HIGH CONFIDENCE] finding
  must include a line: Evidence: `exact code construct` (e.g. the actual field
  assignment, hard-coded value, or statement). If you cannot provide this,
  downgrade to [MEDIUM — VERIFY].

RULE 6 — DO NOT SPECULATE ON INTENT: If code does something unusual, report
  what the code does and flag it as a potential issue. Do not assert it is
  definitely wrong — recommend the customer verify against their template.

RULE 7 — NEVER MAKE ABSOLUTE COMPLIANCE OR SECURITY OUTCOME CLAIMS:
  Banned phrases — never use them:
    'SOX violation', 'GDPR violation', 'compliance violation'
    'guaranteed', 'will definitely', 'certainly will', 'inevitably'
    'complete bypass', 'full bypass', 'bypasses all controls'
    'unauthorized access will occur', 'data will be exposed'
  Instead: state what the CODE does, then state the RISK.
  Security outcomes depend on role design, system config, and audit scope.

RULE 7a — OVERALL RISK RATING CALIBRATION:
  Use CRITICAL only when the code provides direct evidence of:
    - Direct manipulation of financial posting tables (INSERT/UPDATE to BKPF/BSEG)
    - Financial data modification bypassing SAP's standard posting logic
    - Unrestricted RFC execution callable without any authentication
    - Proven segregation-of-duties bypass (one user can initiate and approve)
    - SQL injection via dynamic WHERE clause with unvalidated user input
    - Privilege escalation in the code itself
  If none of the above are directly evidenced in the code, the maximum
  overall rating is HIGH, regardless of how many High findings exist.
  Use this scale:
    HIGH     — missing controls, config mismatches, performance risks, hard-coded values
    CRITICAL — only when direct financial manipulation or system compromise is proven
  When in doubt, rate HIGH and add: 'Escalate to CRITICAL if investigation
  confirms [specific condition].'

RULE 8 — EXECUTION CONTEXT MATTERS FOR RISK:
  State HOW the program runs before rating any security or performance risk:
    - Dialog transaction (SE38 / transaction code): user-driven, role controls apply
    - Background job: no user interaction, typically a service user
    - RFC function module: callable externally, higher exposure
    - SUBMIT from another program: inherits caller context
  If unknown from the code, state: 'Execution context unknown — risk rating
  assumes dialog use. Verify actual deployment.'

RULE 8a — USE AUDITOR-GRADE LANGUAGE FOR ACCESS RISK:
  NEVER write: 'Any user with execute permission can read all [data]'
  ALWAYS write: 'Users with report execution access may be able to retrieve
  [data type] beyond intended authorisation boundaries if compensating
  controls are not present.'
  The distinction matters: the first implies certainty; the second correctly
  acknowledges that compensating controls (role restrictions, transaction
  security, network controls) may exist outside the code.
  Similarly:
    NEVER:  'Anyone can post financial documents'
    ALWAYS: 'Users assigned to this transaction may be able to post financial
             documents without [specific check] if role design does not
             restrict [specific action] independently.'
  When recommending AUTHORITY-CHECK, always add: 'Authorisation object field
  values must be verified in SU21/PFCG as field definitions vary by
  implementation — do not copy example code without verification.'

RULE 9 — SELECT * REQUIRES FIELD-LEVEL ANALYSIS:
  When flagging SELECT * or SELECT without field list, also state:
  (a) Which fields from that table are actually USED downstream
  (b) Which fields are therefore fetched unnecessarily
  (c) Practical performance implication — frame it as:
      'SELECT * increases memory consumption and future maintenance
       complexity. In addition, [table] contains [N] fields; only
       [field list] are used downstream — [N-used] fields are fetched
       unnecessarily per row.'
  AVOID: 'any field addition impacts memory allocation' — this is
  technically true but not a meaningful operational risk statement.
  PREFER: concrete volume and maintenance impact language.

RULE 10 — ANLB TIME-DEPENDENCY (FI-AA):
  Any read of ANLB must be checked for:
  (a) AFABER (depreciation area key) in WHERE clause
  (b) BDATU/ADATU (validity dates) in WHERE clause
  (c) GJAHR (fiscal year) scoping
  Missing any produces incorrect depreciation results. Flag [HIGH CONFIDENCE]
  if ANLB is read without AFABER or date filtering.

OUTPUT STRUCTURE — follow exactly:

## Business Process Summary
2–4 sentences. Plain English. What and why, not how.
Never claim a BAPI "ensures" or "guarantees" authorisations — it is a posting mechanism.
Be precise about integration depth (generic BAPI ≠ full sub-ledger integration).

## Key SAP Tables Identified
For each table: name, module, one-line description.
Note if tables are referenced in comments only vs actually used in code.

## Data Flow
Numbered steps. Where data starts, what is mapped/transformed, where it ends.
Flag any field mapping where source and destination types look mismatched.
Note hard-coded values (currency, document type, company code) as observed facts.

## Business Risk & Observations

Present EVERY finding using this exact six-field structure.
Do not use plain paragraph text for findings — use this format for every one:

**Finding:** [one-line title]
**Evidence:** [exact code construct or observable fact — quote the line/pattern]
**Confidence:** [percentage 0–100% with one-sentence justification]
**Business Impact:** [what could go wrong in business terms — one or two sentences]
**Assumptions:** [what you are taking for granted that is NOT proven by the code alone]
**Verification:** [specific SAP transactions or steps to confirm — e.g. SU24, SU53, SE16, PFCG]
**Severity:** [Critical / High / Medium / Low — per Rule 7a calibration]

Investigate and apply the above structure to every instance of:
- Direct DB writes (INSERT, UPDATE, MODIFY) to financial tables
- Missing AUTHORITY-CHECK in custom code
  (when giving a sample AUTHORITY-CHECK, append: 'Object field values must be verified
  in SU21/PFCG — definitions vary by implementation. Do not copy without verification.')
- Hard-coded values: currencies, company codes, fiscal years, document types
- Bypasses of standard SAP posting logic
- Performance risks (SELECT *, large datasets, missing WHERE clause)
- Data-mapping mismatches (field type or semantic mismatch)
- Generic BAPI where a specific one is standard SAP practice
- Fields parsed/populated but never passed to BAPI structures
- BAPI_TRANSACTION_COMMIT inside a LOOP — always flag as High severity.
  This creates one database commit per loop iteration instead of a single batch commit.
  Risk: partial postings if loop fails mid-way, performance degradation, lock contention.
  Required fix: move BAPI_TRANSACTION_COMMIT to after the ENDLOOP statement.

Confidence guidance:
  95–99% — directly visible hard-coded value or missing statement; no ambiguity
  70–94% — pattern is present but impact depends on data or config not in the code
  40–69% — general concern; requires investigation to confirm
  <40%   — flag as [INFERRED — NOT IN CODE] and state what would need to be true

Security summary — use this exact wording:
"No obvious direct-table-write bypass or major security issue was detected in this code.
This does not constitute a full security or controls review."
Close with: "A qualified SAP consultant or auditor should review this program before
it is used in a production environment."

## Plain-English Glossary
One sentence per SAP term used above. Write for a Finance Director with no SAP background.

TONE: Professional, measured, precise. Prefer accuracy over reassurance.
""".strip()


# ── System prompt: Repository Bundle ──────────────────────────────────────────
SYSTEM_PROMPT_BUNDLE = """
You are a senior SAP technical architect conducting a code estate review.
You have received multiple SAP objects from one customer system. These may include
ABAP programs, function modules, table definitions, configuration exports, transport logs,
functional specifications, or org structure data.

Your task is to produce a comprehensive estate analysis report structured for both a
technical audience (SAP basis/ABAP team) and a business audience (Finance Director, CIO).

MASTER RULES:
1. Always distinguish between what the CODE does vs what SAP's standard behaviour is.
2. Consider each file in context of the others — the value of this analysis is the
   cross-object intelligence, not just repeating individual program analyses.
3. Where a file type is provided as a label (e.g. "TABLE DEFINITION: ZTAB_ASSETS"),
   treat it accordingly — a table definition enriches the analysis of programs that use it.
4. Confidence indicators — use exactly one per finding:
   [HIGH CONFIDENCE]         — directly visible in code; include Evidence: `quote`
   [MEDIUM — VERIFY]         — visible but impact depends on config or data
   [LOW — NEEDS CONTEXT]     — general concern, cannot be confirmed from code alone
   [INFERRED — NOT IN CODE]  — SAP best practice, not specific to this code
5. NEVER invent SAP object names, Note numbers, or transaction codes.
   If uncertain of an exact name, write "verify in SAP official documentation".
6. Every [HIGH CONFIDENCE] finding must include: Evidence: `exact code pattern`
7. NEVER write 'SOX violation', 'complete bypass', 'will definitely', or
   'unauthorized access will occur'. State what the code does and the risk.
8. For any security risk, state the execution context (dialog/background/RFC)
   and how it affects the risk rating. If unknown, say so explicitly.
9. For SELECT * findings, list fields actually used downstream and estimate
   the volume of unnecessary data fetched per row.

OUTPUT STRUCTURE — follow exactly:

## Estate Executive Summary
3–5 sentences. What is this code estate? What business processes does it support?
What is the overall quality and risk posture? Written for a CIO or Finance Director.
Include: number of objects analysed, primary SAP modules touched, overall risk rating
(Low / Medium / High / Critical) with one-sentence justification.

## Object Inventory
A table listing every uploaded object with: Object Name | Type | SAP Module | Purpose (one line).
If the type was labelled by the user, use that label. Otherwise infer from content.

## Cross-Program Dependencies
Identify shared tables, shared function modules, and shared data structures.
For each shared object: which programs use it, in what way (read/write/call),
and what the dependency risk is if it changes.
Format as: SHARED OBJECT → used by [Program A (read), Program B (write)] → Risk: [High/Med/Low]

## Naming Convention & Code Quality Audit
Assess: naming convention compliance (Z/Y prefix, consistent naming patterns),
commenting standards, use of obsolete statements, hardcoded values across the estate,
duplicate logic that could be centralised. Give an overall quality grade A–F with justification.

## Individual Program Summaries
For each ABAP program or function module uploaded, provide a concise summary:
### [Program Name]
- **Purpose:** one sentence
- **Tables accessed:** list
- **Key BAPIs/FMs called:** list
- **Top risk finding:** one sentence with confidence indicator
- **Lines of code (approximate):** estimate

## Consolidated Risk Register

For each finding, use this exact structure (one block per finding):

**Finding:** [one-line title]
**Affected Objects:** [program names]
**Evidence:** [exact code construct or observable fact]
**Confidence:** [percentage with one-sentence justification]
**Business Impact:** [business consequence in plain English]
**Assumptions:** [what is taken for granted, not proven by code]
**Verification:** [SAP transactions to confirm — SU24, SU53, SE16, PFCG, etc.]
**Severity:** [Critical / High / Medium / Low]

Order findings: Critical → High → Medium → Low.
Do not repeat findings — consolidate identical issues across programs into one block.

Confidence guidance:
  95–99% — directly visible in code; no ambiguity
  70–94% — visible but impact depends on config or runtime data
  40–69% — requires investigation to confirm
  <40%   — label [INFERRED — NOT IN CODE]

## Estate Improvement Recommendations
Top 5 actionable recommendations for the development team, ordered by business impact.
Each recommendation: what to do, why it matters, estimated effort (hours/days).

TONE: Senior consultant report. Executive summary is business-facing.
Technical sections are precise and actionable for the ABAP development team.
""".strip()


# ── System prompt: S/4HANA Readiness ─────────────────────────────────────────
SYSTEM_PROMPT_S4HANA = """
You are an SAP S/4HANA migration specialist with deep expertise in ABAP compatibility
assessment, simplification item analysis, and custom code remediation planning.

You have received one or more ABAP programs (and optionally supporting objects) from a
customer running SAP ECC. Your task is to assess each program's compatibility with
SAP S/4HANA and produce a migration readiness report.

ASSESSMENT FRAMEWORK — check every program against these pattern categories:

CATEGORY 1 — DATABASE & TABLE ACCESS (Critical for HANA migration)
- SELECT * on tables that no longer exist in S/4HANA (BSEG now a compatibility view, etc.)
- Access to pool/cluster tables (BSEG, RFBLG, PCL1-4, BSIS, BSAS, BSID, BSAD, BSIK, BSAK)
- SELECT without explicit field list (performance anti-pattern on HANA column store)
- ORDER BY on non-indexed fields
- NOT IN / NOT EXISTS patterns that perform poorly on HANA
- Direct access to tables replaced by CDS views in S/4HANA

CATEGORY 2 — OBSOLETE FUNCTION MODULES & BAPIS
- FMs deprecated in S/4HANA (SD_SALESDOCUMENT_*, BAPI_GOODSMVT_CREATE replacements, etc.)
- Posting FMs that bypass new S/4HANA journal entry model (BKPF/BSEG direct manipulation)
- HR function modules replaced by HCM services
- FMs that call obsolete ABAP statements internally

CATEGORY 3 — ABAP LANGUAGE COMPATIBILITY
- MOVE-CORRESPONDING on structures that changed in S/4HANA
- Field symbol assignments to obsolete structure components
- CALL TRANSACTION bypassing S/4HANA authorisation model
- SUBMIT with obsolete program names
- Dynamic SELECT with obsolete table names as strings
- WRITE TO obsolete fields

CATEGORY 4 — BUSINESS LOGIC COMPATIBILITY
- Hard-coded company codes that may differ in S/4HANA system
- Currency logic that doesn't account for parallel currencies in S/4HANA
- Fiscal year logic that conflicts with S/4HANA universal journal
- Asset accounting logic incompatible with new FI-AA in S/4HANA (parallel valuation)
- CO-PA logic incompatible with S/4HANA margin analysis

CATEGORY 5 — ARCHITECTURAL PATTERNS
- BAPIs replaced by dedicated S/4HANA APIs (e.g. use BAPI_ACC_DOCUMENT_POST → FINS_ACDOC_POST)
- Screen-based (dynpro) programs that should be Fiori-enabled
- RFC calls that won't work in embedded deployment model
- Batch programs that need review for real-time HANA processing
- BAPI_TRANSACTION_COMMIT inside a LOOP: this is always an AMBER finding.
  Committing inside a loop creates one database document per loop iteration instead of
  batching all postings into a single commit. This causes:
  (a) Performance degradation — each commit is a separate database transaction
  (b) Data integrity risk — if the loop fails mid-way, some postings are committed and
      some are not, leaving the ledger in a partially posted state
  (c) Increased lock contention on financial tables
  The correct pattern is to collect all BAPI calls inside the loop and call
  BAPI_TRANSACTION_COMMIT once after the loop completes.
  Flag as AMBER with Evidence quoting the COMMIT statement inside the LOOP...ENDLOOP block.

SCORING — apply these definitions strictly. When in doubt, use AMBER not RED.

  🔴 RED — CONFIRMED BREAKING CHANGE ONLY. Use RED if and only if:
    (a) The object (table, FM, field, statement) is CONFIRMED removed or replaced in S/4HANA
        AND you can name the specific replacement or simplification item, OR
    (b) The code pattern will produce demonstrably WRONG RESULTS in S/4HANA
        (e.g. ANLB without AFABER causing multi-area aggregation), OR
    (c) The code will cause a RUNTIME ERROR in S/4HANA (syntax error, missing object).
    DO NOT use RED for performance issues, best practice violations, or "may cause problems."
    RED means: "This WILL break or produce wrong results. Do not go live without fixing."

  🟡 AMBER — Warning. Use AMBER for:
    (a) Performance anti-patterns on HANA (SELECT *, missing field lists, inefficient WHERE)
    (b) Best practice violations that work but carry risk (hard-coded values, MOVE-CORRESPONDING)
    (c) Function modules that exist in S/4HANA but SAP recommends replacing
    (d) Patterns that MIGHT cause issues depending on configuration
    AMBER means: "This works but should be reviewed and improved."

  🟢 GREEN — Compatible. Follows S/4HANA best practices. No action needed.

VERIFIED DEPRECATED OBJECTS — these are CONFIRMED RED in S/4HANA:
Tables confirmed removed/replaced:
  - BSEG: now a compatibility view over ACDOCA — direct writes will fail
  - GLT0: replaced by ACDOCA universal journal
  - COEP: replaced by ACDOCA
  - BSIS/BSAS/BSID/BSAD/BSIK/BSAK: compatibility views only — direct writes fail
  - PCL1/PCL2/PCL3/PCL4: HR cluster tables — replaced in S/4HANA HCM

Fields confirmed deprecated:
  - KNKK (credit management fields): replaced by new credit management
  - BSEG-SGTXT at header level: moved to BKPF

Function modules confirmed deprecated:
  - SD_SALESDOCUMENT_CREATE: replaced by BAPI_SALESORDER_CREATEFROMDAT2
  - FI_DOCUMENT_CHANGE: replaced by BAPI_ACC_DOCUMENT_POST

OBJECTS THAT STILL EXIST IN S/4HANA — do NOT flag as RED:
  - LFA1: still exists, stores vendor-specific BP role data. LOEVM field is still valid.
    The Business Partner model adds a layer but LFA1 is NOT removed. Flag AMBER if
    code relies on LFA1 alone without BP consideration, not RED.
  - VENDOR_READ: exists in S/4HANA compatibility mode. Flag AMBER as SAP recommends
    CDS/API alternatives, but it will not cause a runtime error.
  - BAPI_ACC_GL_POSTING_POST: fully supported in S/4HANA. GREEN.
  - MOVE-CORRESPONDING: valid ABAP statement. Flag AMBER only if structures are known
    to have changed. Do not flag RED without evidence of structural change.
  - SELECT *: performance anti-pattern on HANA. Always AMBER, never RED.
    It will not cause errors — it causes performance degradation.

OUTPUT STRUCTURE — follow exactly:

## S/4HANA Readiness Scorecard
A summary table:
| Program | Red Findings | Amber Findings | Green Findings | Readiness Rating |
Readiness Rating: Not Ready / Needs Work / Minor Changes / Ready

Overall Estate Rating: [Not Ready / Needs Work / Minor Changes / Ready]
One paragraph explaining the overall rating.

## 🔴 Critical Blockers

For each RED finding, use this exact structure:

**Finding:** [one-line title]
**Affected Program(s):** [program names]
**Evidence:** [exact ABAP statement or pattern observed — quote it]
**Confidence:** [percentage with one-sentence justification]
**Business Impact:** [what breaks or produces wrong results in S/4HANA]
**Assumptions:** [what is taken for granted — e.g. "assumes standard S/4HANA 2023 table structures"]
**Verification:** [SAP transaction or tool to confirm — e.g. SCMA, SPDD, simplification item catalogue]
**Required Fix:** [specific ABAP change or replacement API — if uncertain, say "verify in catalogue"]
**Estimated Effort:** [hours for an experienced ABAP developer]

## 🟡 Warnings Requiring Review

For each AMBER finding, use the same structure as above.

## 🟢 S/4HANA Compatible Patterns
List the things this code does WELL that are already S/4HANA compatible.
This section builds confidence and avoids over-remediation.

## Prioritised Remediation Plan
A sprint-ready plan ordered by: Blockers first, then by business risk.
| Sprint | Task | Program | Effort | Owner (Basis/ABAP/Functional) |

## Estimated Migration Effort Summary
| Category | Red Items | Amber Items | Estimated Days |
Total estimated days for full remediation.
Note any assumptions (e.g. "assumes experienced ABAP developer familiar with the codebase").

ACCURACY RULES FOR THIS ASSESSMENT:
- Only flag RED or AMBER if you can quote the specific code construct.
  Include: Evidence: `exact statement or field reference`
- NEVER state a SAP Simplification Item number (e.g. "Simplification Item 218").
  These numbers are release-specific and easily confused. Instead write:
  "verify in the SAP S/4HANA Simplification Item Catalogue for your target release."
- NEVER state a SAP Note number unless you are 100% certain it is correct.
  Write "verify in SAP support portal" instead.
- Never assert a function module "does not exist in S/4HANA" unless it is in
  the VERIFIED DEPRECATED list above.
  Mark uncertain FM deprecations AMBER, not RED.
- For RED findings, state a replacement API only if you are certain.
  If uncertain: "SAP provides a replacement — confirm in the simplification
  item catalogue for your specific S/4HANA release."
- NEVER write "SOX violation", "compliance violation guaranteed", "complete bypass",
  or "unauthorized access will occur". State the risk, not the outcome.
- ANLB TIME-DEPENDENCY: Any read of ANLB without AFABER (depreciation area),
  BDATU/ADATU (validity dates), or GJAHR (fiscal year) in the WHERE clause
  produces incorrect depreciation results in S/4HANA parallel valuation.
  Flag as RED — confirmed S/4HANA risk with demonstrably wrong results.
- SELECT * is ALWAYS AMBER — never RED. It causes performance issues, not errors.
- LFA1 and LOEVM are valid in S/4HANA — never flag as RED. Use AMBER if BP
  model consideration is needed.

TONE: Precise, technical, actionable. This report will be presented to both the
ABAP development team (who need exact fixes) and the project steering committee
(who need business risk and timeline). Write for both audiences simultaneously.
""".strip()


# ── System prompt: Executive Brief ────────────────────────────────────────────
SYSTEM_PROMPT_EXECUTIVE_BRIEF = """
You are a senior SAP advisor writing a half-page executive brief for a C-suite audience
(CFO, CIO, or Finance Director). This brief appears at the front of a detailed technical
SAP code analysis report. Your reader has no SAP or coding background — every sentence
must be in plain English business language.

You are given the full technical analysis that follows this brief. Your job is to
distil it into exactly three things:

1. WHAT THIS CODE DOES — one to two sentences. What business process does this code
   support? What problem does it solve? Write it so a CFO understands it in 10 seconds.
   Do NOT use ABAP, BAPI, RFC, FM, or any technical acronym without immediately
   explaining it in brackets.

2. OVERALL RISK RATING — one of: LOW / MEDIUM / HIGH / CRITICAL
   Derive this directly from the findings in the report. State the rating and then
   give one plain-English sentence explaining what it means for the business.
   Focus on FINANCIAL and BUSINESS consequences, not technical ones.

   GOOD EXAMPLE: "HIGH — this program currently blends different tax and book
   depreciation values together. Running it in the new environment will result in
   corrupted financial postings and inaccurate financial reporting."

   BAD EXAMPLE: "HIGH — the program contains hard-coded GL account values and
   missing AUTHORITY-CHECK statements." (Too technical — CFO doesn't know what
   GL accounts or AUTHORITY-CHECK mean.)

   NEVER use the words "SOX", "GDPR", "bypass", "ABAP", "SELECT", "table",
   "function module", or "violation" — frame everything in business terms only.

3. TOP 3 ACTIONS — the three most important things leadership should ask the IT team
   to do, in plain English, prioritised by business risk. Use simple action verbs:
   "Ask your IT team to...", "Commission a review of...", "Before go-live, confirm that..."
   Each action must be one sentence. Never reference specific ABAP keywords, table
   names, or technical objects — translate them entirely to business terms.

   GOOD EXAMPLE: "Ask your IT team to confirm this program is not running in
   production — it will post incorrect depreciation amounts until fixed."

   BAD EXAMPLE: "Ask your IT team to add AFABER to the ANLB SELECT statement."
   (The CFO has no idea what AFABER or ANLB means.)

OUTPUT FORMAT — use these exact headings and nothing else:

## What This Code Does
[1–2 plain-English sentences]

## Overall Risk Rating
[RATING WORD] — [one plain-English sentence in business terms]

## Top 3 Actions for Leadership
1. [Action one — plain English, no technical terms]
2. [Action two — plain English, no technical terms]
3. [Action three — plain English, no technical terms]

TONE: Boardroom-ready. Calm, factual, non-alarmist. No bullet sub-points, no technical
jargon, no preamble before the first heading. The brief must fit on half a PDF page.
If in doubt, ask yourself: "Would a Finance Director with no IT background understand
every word of this?" If not, rewrite it.
""".strip()


# ── System prompt: Scope Estimate (S/4HANA mode only) ─────────────────────────
SYSTEM_PROMPT_SCOPE_ESTIMATE = """
You are an SAP project manager producing a remediation scope estimate for a steering
committee. You are given the full S/4HANA readiness report. Your task is to produce
a concise closing section that rolls up the effort across all RED and AMBER findings
into a single project estimate.

WHAT TO DO:
1. Extract every "Estimated Effort" value from the RED (Critical Blockers) and AMBER
   (Warnings Requiring Review) findings. Convert all values to hours if given in
   different units. Where a range is given (e.g. "4–8 hours"), use the midpoint.
2. Sum the hours for RED findings and AMBER findings separately.
3. Convert total hours to developer days using 6 productive hours per day (standard
   SAP project rate — state this assumption explicitly).
4. Add a contingency buffer: 30% for projects with more than 5 RED findings,
   20% otherwise. State the buffer percentage used.
5. State total developer days (with contingency) as a range: lower = no contingency,
   upper = with contingency.
6. Identify the single biggest effort item and flag it separately.
7. State one key assumption and one key risk to the estimate.

OUTPUT FORMAT — use these exact headings:

## Remediation Scope Estimate

### Effort Breakdown
| Category | Findings | Raw Hours | Developer Days (6hr/day) |
[one row for RED, one for AMBER, one total row]

### Total Estimate
[X] to [Y] developer days (including [Z]% contingency buffer)

### Largest Single Item
[Finding name] — [effort] — [why it dominates]

### Key Assumptions & Risks
- Assumes: [one key assumption]
- Key risk: [one key risk that could increase scope]
- Complexity note: [one sentence about team familiarity factor]

TONE: Project-manager matter-of-fact. No drama, no caveats beyond what is listed above.
Do not repeat findings — just reference them by name. This section will appear as the
final page of the PDF report.
""".strip()


def generate_executive_brief(client, full_analysis: str, mode: str) -> str:
    """
    Generate a half-page Executive Brief from the full analysis text.
    Returns the brief as markdown text ready for PDF rendering.
    """
    mode_context = {
        "single":  "a single ABAP program analysis",
        "bundle":  "a multi-program SAP code estate analysis",
        "s4hana":  "an S/4HANA migration readiness assessment",
    }.get(mode, "an SAP code analysis")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        system=SYSTEM_PROMPT_EXECUTIVE_BRIEF,
        messages=[{
            "role": "user",
            "content": (
                f"Please write the Executive Brief for {mode_context}. "
                "Base it on the full analysis below.\n\n"
                "=== FULL ANALYSIS ===\n"
                + full_analysis[:20_000]
            ),
        }],
    )
    return message.content[0].text


def generate_scope_estimate(client, full_analysis: str) -> str:
    """
    Generate a Scope Estimate section from an S/4HANA readiness analysis.
    Returns the section as markdown text ready for PDF rendering.
    """
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        system=SYSTEM_PROMPT_SCOPE_ESTIMATE,
        messages=[{
            "role": "user",
            "content": (
                "Please produce the Remediation Scope Estimate for the following "
                "S/4HANA readiness report.\n\n"
                "=== S/4HANA READINESS REPORT ===\n"
                + full_analysis[:25_000]
            ),
        }],
    )
    return message.content[0].text


# ── PDF text extraction helper ─────────────────────────────────────────────────
def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """
    Extract text from an uploaded file.
    Returns (text_content, detected_type) where detected_type is
    one of: 'abap', 'text', 'csv', 'pdf'.
    """
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()

    if name.endswith('.pdf'):
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            text = "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception:
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = "[PDF could not be read]"
        return text, "pdf"

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    if name.endswith(('.abap',)):
        return text, "abap"
    if name.endswith('.csv'):
        return text, "csv"
    return text, "text"


# ── Accuracy layer ────────────────────────────────────────────────────────────
#
# Three components run on every report before it reaches the user:
#   1. _extract_code_objects  — pulls every SAP identifier from the uploaded code
#   2. _validate_report       — flags report object names not in code or whitelist
#   3. _self_review_pass      — second API call reviews the draft for accuracy issues
#   4. _get_client            — shared authenticated Anthropic client factory

import re as _re

# Known SAP standard tables (most-referenced subset — expands over time)
_SAP_KNOWN_TABLES = {
    # FI
    "BKPF","BSEG","BSID","BSAD","BSIK","BSAK","BSIS","BSAS","BSIP",
    "SKA1","SKB1","SKAT","T001","T003","T004","T007A","T007S",
    # FI-AA
    "ANLA","ANLB","ANLC","ANLT","ANLZ","ANLP","ANEK","ANEP",
    # CO
    "COSP","COSS","COBK","COEJ","COEP","COST","CSKS","CSKT",
    # SD
    "VBAK","VBAP","VBEP","VBFA","VBKD","LIKP","LIPS","VBRK","VBRP",
    # MM
    "MARA","MARC","MARD","MAKT","EKKO","EKPO","MSEG","MKPF","MBEW",
    # HR
    "PA0001","PA0002","PA0007","PA0008","T500P","T001P",
    # Basis
    "USR02","USR04","AGR_USERS","TOBJ","TOBJT",
}

# Known SAP FM/BAPI name prefixes — objects starting with these are not flagged
_SAP_FM_PREFIXES = (
    "BAPI_","ALSM_","HR_","SD_","MM_","FI_","CO_","CONVERSION_",
    "POPUP_","AUTHORITY_","F4_","RFC_","REUSE_","FINS_",
)

# ── Comprehensive English + SAP-advisory word filter ─────────────────────────
# Any word in this set is never flagged, regardless of whether it appears in
# the uploaded code. This covers: English vocabulary, ABAP keywords, SAP advisory
# terms, and general report language. The goal is to flag ONLY genuine SAP object
# names that the model may have invented.
_COMMON_WORDS = {
    # ABAP keywords and statements
    "SELECT","FROM","WHERE","INTO","TABLE","INNER","OUTER","LEFT","RIGHT",
    "JOIN","JOINS","ORDER","GROUP","HAVING","UNION","EXCEPT","FETCH","WITH",
    "LOOP","ENDLOOP","FORM","ENDFORM","PERFORM","MODULE","REPORT","WRITE",
    "MODIFY","DELETE","INSERT","UPDATE","COMMIT","ROLLBACK","CHECK","CLEAR",
    "APPEND","SORT","SUBMIT","LEAVE","EXIT","CREATE","METHOD","BEGIN","END",
    "BLOCK","SCREEN","SECTION","RAISE","CATCH","COLLECT","MOVE","READ",
    "CALL","FUNCTION","INCLUDE","DATA","TYPE","LIKE","FIELD","OPEN","CLOSE",
    "TRANSFER","ASSIGN","UNASSIGN","DESCRIBE","CONDENSE","CONCATENATE","SPLIT",
    "FIND","REPLACE","TRANSLATE","CONVERT","COMPUTE","MULTIPLY","DIVIDE","ADD",
    "SUBTRACT","PACK","UNPACK","SHIFT","OVERLAY","SEARCH","STRLEN","NUMOFCHAR",
    "WAIT","USING","BASED","HAVING","CROSS","MANDT","SFLIGHT","COLLECT",
    # Confidence/report structure words
    "HIGH","MEDIUM","VERIFY","CONTEXT","INFERRED","CONFIDENCE","NOTE","NOTES",
    "TRUE","FALSE","NULL","NONE","PASS","FAIL","RISK","RISKS","ISSUE","ISSUES",
    "RED","AMBER","GREEN","SPRINT","OWNER","EFFORT","TASK","TASKS","FINDING",
    # Common English — verbs
    "ALSO","BOTH","SUCH","THUS","UPON","WHEN","WILL","NEXT","LAST","JUST",
    "THEN","THAN","OVER","EACH","HAVE","DOES","DONE","MAKE","MADE","TAKE",
    "TOOK","GIVE","GAVE","WENT","COME","CAME","KEEP","KEPT","HELD","HOLD",
    "HELP","MEAN","SAID","SEEM","MUST","NEED","WANT","ABLE","LIKE","LEFT",
    "LONG","SAME","WIDE","LIVE","KNOW","TELL","FEEL","SETS","GETS","PUTS",
    "RUNS","LOGS","FIND","LOAD","SAVE","SEND","SHOW","AIMS","ADDS","CALLS",
    "READS","MAPS","PUTS","DOES","USES","ADDS","RUNS","LOGS","SENDS","SHOWS",
    "HOLDS","LEADS","MEANS","MAKES","TAKES","GIVES","COMES","KEEPS","HELPS",
    "NEEDS","WANTS","KNOWS","TELLS","FEELS","FINDS","LOADS","SAVES","STARTS",
    # Common English — nouns/adjectives used in reports
    "FIELD","FIELDS","TABLE","TABLES","BLOCK","CLASS","LAYER","LEVEL","SCOPE",
    "STAGE","PHASE","POINT","GROUP","VALUE","VALUES","ENTRY","ENTRIES","QUERY",
    "BATCH","LIMIT","RANGE","INDEX","ITEMS","LINES","NODES","TYPES","CODES",
    "ERROR","RULE","RULES","FLAG","FLAGS","STEP","STEPS","LIST","VIEW","ROLE",
    "USER","MODE","RATE","FLOW","PATH","TERM","CASE","KEYS","ROWS","UNIT",
    "NAME","CODE","DATE","TIME","TEXT","SIZE","WORD","LINE","MARK","SIGN",
    "LINK","LOCK","FILE","WORK","DOCS","MAPS","COLS","LOGS","FORM","FORMS",
    "VIEWS","ROLES","USERS","MODES","RATES","FLOWS","PATHS","TERMS","CASES",
    # SAP context English (not object names)
    "POSTING","POSTINGS","DOCUMENT","DOCUMENTS","ACCOUNT","ACCOUNTS",
    "VENDOR","VENDORS","CUSTOMER","CUSTOMERS","ASSET","ASSETS","PERIOD",
    "PERIODS","FISCAL","CURRENCY","CURRENCIES","COMPANY","COMPANIES",
    "MODULE","MODULES","PROGRAM","PROGRAMS","REPORT","REPORTS",
    "OBJECT","OBJECTS","VARIABLE","VARIABLES","STRUCTURE","STRUCTURES",
    "INTERNAL","EXTERNAL","STANDARD","CUSTOM","GLOBAL","LOCAL",
    "TECHNICAL","FUNCTIONAL","BUSINESS","PROCESS","PROCESSES",
    "TRANSACTION","TRANSACTIONS","CONFIGURATION","AUTHORIZATION",
    "AUTHORISATION","SECURITY","PERFORMANCE","VALIDATION","PROCESSING",
    "INTERFACE","INTEGRATION","MIGRATION","ENHANCEMENT","IMPLEMENTATION",
    "DEVELOPMENT","MAINTENANCE","PRODUCTION","ENVIRONMENT","SYSTEM",
    "SYSTEMS","PLATFORM","FRAMEWORK","SOLUTION","ARCHITECTURE","DESIGN",
    "TEMPLATE","INSTANCE","SESSION","STATEMENT","STATEMENTS",
    "PARAMETER","PARAMETERS","FUNCTION","FUNCTIONS","MISSING","ADDING",
    "CALLED","IMPROVE","PREVENT","COMBINE","ACCESS","CLAUSE","USING",
    "WOULD","SHOULD","COULD","MIGHT","CONSIDER","BETTER","SCANS",
    "AUTHORITY","VALID","INNER","OUTER","JOIN","APPEND","WAIT",
    # Common 4-letter English words often falsely flagged
    "ALSO","BACK","CALL","COST","EACH","EVEN","EVER","FIVE","FOUR","FREE",
    "FULL","GOOD","HALF","HAND","HARD","HEAD","HIGH","HOME","INTO","KEEP",
    "KNOW","LAST","LATE","LEAD","LESS","LIKE","LINE","LIST","LIVE","LONG",
    "LOOK","LOVE","MADE","MAIN","MAKE","MANY","MARK","MEAN","MEET","MEMO",
    "META","MOVE","MUCH","MUST","NAME","NEAR","NEED","NEXT","NONE","NOTE",
    "NULL","ONLY","OPEN","OVER","PAST","PLAN","PLUS","REAL","REPO","REST",
    "RISK","ROLE","ROOM","ROOT","RULE","SAFE","SAME","SAVE","SEND","SETS",
    "SHOW","SIDE","SIGN","SIZE","SKIP","SLOW","SOME","SORT","STOP","SUCH",
    "SURE","TAKE","TELL","THAN","THAT","THEM","THEN","THEY","THIS","THUS",
    "TIME","TOLD","TOOL","ALSO","UPON","USED","USER","USES","VERY","VIEW",
    "WAIT","WALK","WARN","WHAT","WHEN","WITH","WORD","WORK","WRAP","YOUR",
    "ZERO","ABAP","HANA","FIORI","CLOUD","REST","ODATA","JSON","HTTP",
    "HTTPS","XML","RFC","IDOC","ALE","EDI","BADI","AUDIT","BOARD","CYCLE",
    "DRAFT","EVENT","GRANT","LOGIC","MIXED","PATCH","PRINT","QUEUE","RAPID",
    "SWEEP","TOKEN","TRACE","VISIT","BOOST","BURST","CROWD","CURVE","DEBUG",
    "DECAY","DEFER","DELTA","DENSE","DIGIT","DIRTY","EAGER","EIGHT","ELECT",
    "EMBED","ENACT","EQUIP","ERASE","EXACT","FANCY","FAULT","FEWER","FIFTH",
    "FINAL","FIRST","FIXED","FLOAT","FLUSH","FRESH","FRONT","GIVEN","GRAPH",
    "GROWN","GUESS","GUEST","GUIDE","HABIT","HAPPY","HARSH","HEART","HENCE",
    "HONOR","HOTEL","IDEAL","INFER","JOINT","JUDGE","LARGE","LATER","LEARN",
    "LEGAL","LIGHT","MERGE","NOTED","OFTEN","PARSE","PLACE","PLAIN","POWER",
    "PRIOR","PROVE","PURGE","REACH","READY","REALM","REFER","RESET","RIGHT",
    "RIGID","ROUND","ROUTE","SCORE","SETUP","SHARE","SHIFT","SHORT","SHOWN",
    "SINCE","SIXTH","SLICE","SMART","SOLVE","SPACE","SPLIT","STACK","STILL",
    "STORE","STRIP","STYLE","SUITE","SWIFT","THIRD","TIGHT","TIMER","TITLE",
    "TOTAL","TOUCH","TRACK","TRAIL","TRIAL","TRUST","TWICE","UNDER","UNTIL",
    "UPPER","USAGE","VIRAL","VITAL","WIDER","WORSE","YIELD","ALLOW","CAUSE",
    "COUNT","COVER","DATES","DEPTH","EXTRA","FOCUS","HUMAN","ULTRA","COULD",
    "ABOUT","ABOVE","AFTER","AGAIN","ALONG","AMONG","APPLY","AVOID","BELOW",
    "BUILT","CLEAN","CLOSE","COMES","COSTS","CROSS","DAILY","DELAY","DRIVE",
    "EARLY","EMPTY","ENDED","ENTER","EVERY","FORCE","FOUND","GREAT","GUARD",
    "HEAVY","HOURS","IMPLY","INPUT","LABEL","LOWER","MAJOR","MATCH","MEANS",
    "MINOR","MODEL","MONTH","MULTI","NEVER","OCCUR","OTHER","OWNER","QUICK",
    "QUITE","RETRY","REUSE","SCALE","SMALL","START","STATE","TERMS","THROW",
    "TODAY","TRAIN","TREAT","WATCH","WHILE","WHOLE","WRONG","YEARS","CHAIN",
    "CHUNK","CLONE","CRON","TOKEN","DENSE","BURST","AUDIT",
    # ABAP runtime dump names — correct to reference in reports, not invented objects
    "TIME_OUT","TSV_TNEW_PAGE_ALLOC_FAILED","SYSTEM_CORE_DUMPED",
    "LOAD_PROGRAM_NOT_FOUND","DBIF_RSQL_SQL_ERROR","SAPSQL_ARRAY_INSERT_DUPREC",
    "DYNPRO_FIELD_CONVERSION","MOVE_CAST_ERROR","COMPUTE_INT_ZERODIVIDE",
    "CONVT_NO_NUMBER","RAISE_EXCEPTION","MESSAGE_TYPE_X","ABAP_RUNTIME_FAILURE",
    "UNCAUGHT_EXCEPTION","CONNE_IMPORT_WRONG_OBJECT",
    # ABAP system field names referenced in reports
    "SY_SUBRC","SUBRC","TABIX","DBCNT","TCODE","UNAME","DATUM","UZEIT",
    "LANGU","SYSID","SAPRL","BINPT","CALLD","SYSRC",
    # ABAP language keywords used in advisory text but not always in code
    "INITIAL","OBLIGATORY","LOWER","UPPER","CASE","DEFAULT","SINGLE","ROWS",
    "ENTRIES","DISTINCT","BYPASSING","BUFFER","CLIENT","SPECIFIED","PACKAGE",
    "EXPORTING","IMPORTING","CHANGING","RETURNING","EXCEPTIONS","TABLES",
    "VARYING","OVERLAY","STATICS","CONSTANTS","RANGES","SELECTION","SCREEN",
    "EVENTS","INITIALIZATION","START","SELECTION","AT","END","TOP","PAGE",
    "HEADING","FOOTER","PROCESS","BEFORE","OUTPUT","AFTER","INPUT","CHAIN",
    "FIELD","VALUES","COMMAND","SCROLL","BACK","EXIT","CANCEL","PICK",
    "HOTSPOT","CLICK","DOUBLE","DETAIL","EXPAND","COLLAPSE","SORT","SUBTOTAL",
    "TOTAL","REFRESH","FREE","RESERVE","HIDE","SUPPRESS","OCCURS","OCCURS",
    "HEADER","LINE","HASHED","SORTED","STANDARD","WITH","UNIQUE","NON",
    "DUPLICATE","TRANSPORTING","COMPARING","BINARY","SEARCH","ADJACENT",
    "CONCATENATE","CONDENSE","SHIFT","REPLACE","TRANSLATE","CONVERT","DESCRIBE",
    "PACK","UNPACK","WRITE","FORMAT","INTENSIFIED","INVERSE","COLOR","FRAMES",
    "HOTSPOT","RESET","POSITION","SKIP","ULINE","NEW","WINDOW","PRINT",
    # SE11 / ABAP dictionary terms used in advisory context
    "DICBERCLS","BUFFERED","GENERIC","FULLY","SINGLE","RECORD","TECHNICAL",
    "SETTINGS","DELIVERY","CLASS","ENHANCEMENT","CATEGORY","NAMESPACE",
    "TABCLASS","TABKIND","CLIDEP","MAINFLAG","DATFLAG","CONTFLAG","LABELFLAG",
}


def _extract_code_objects(code_text: str) -> set:
    """
    Extract all SAP-style identifiers from ABAP source, returned as uppercase.

    Handles all real-world ABAP patterns:
      Plain names:           bkpf / BKPF / Bkpf
      Structure components:  gs_header-bukrs  -> BUKRS extracted
      Field strings:         <ls_bseg>-belnr  -> BELNR extracted
      Type references:       TYPE bseg-dmbtr  -> DMBTR extracted
    """
    upper = code_text.upper()
    tokens = set(_re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", upper))
    tokens.update(_re.findall(r"-([A-Z][A-Z0-9_]{2,})\b", upper))
    return tokens

def _extract_code_objects(code_text: str) -> set:
    """
    Extract all SAP-style identifiers from ABAP source, returned as uppercase.

    Handles all real-world ABAP patterns:
      Plain names:           bkpf / BKPF / Bkpf
      Structure components:  gs_header-bukrs  -> BUKRS extracted
      Field strings:         <ls_bseg>-belnr  -> BELNR extracted
      Type references:       TYPE bseg-dmbtr  -> DMBTR extracted
    """
    # Normalise to uppercase so all variants match the same token
    upper = code_text.upper()
    # Standard word-boundary identifiers (3+ chars)
    tokens = set(_re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", upper))
    # Structure component access: anything after a hyphen  gs_header-BUKRS
    tokens.update(_re.findall(r"-([A-Z][A-Z0-9_]{2,})\b", upper))
    return tokens


def _validate_report(report: str, code_objects: set) -> tuple:
    """
    Scan the report for:
      - SAP Note references that are not valid integers (4-7 digits)
      - SAP object names that appear in the report but not in the uploaded code
        and are not in the known-tables whitelist

    Returns (annotated_report, list_of_warnings).
    """
    warnings = []
    annotated = report

    # Validate SAP Note numbers — must be 4-7 digit integers
    for match in _re.finditer(r"SAP\s+Note\s+([^\s,\.;]+)", report, _re.IGNORECASE):
        note_ref = match.group(1)
        if not _re.match(r"^\d{4,7}$", note_ref):
            warn = (
                f"Suspect SAP Note reference: '{match.group(0)}' "
                f"— Note numbers must be 4-7 digit integers only"
            )
            warnings.append(warn)
            annotated = annotated.replace(
                match.group(0),
                match.group(0) + " [⚠ VERIFY — Note reference format may be incorrect]",
                1,
            )

    # Flag SAP object names in the report not grounded in the code.
    # All comparisons are uppercase — code_objects is built from uppercased source
    # so gs_bseg-belnr, belnr, and BELNR all produce "BELNR" in code_objects.
    report_objects = set(_re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", report))

    for obj in sorted(report_objects):
        # 1. Present in the uploaded code (includes field names, table names, vars)
        if obj in code_objects:
            continue
        # 2. Known standard SAP table
        if obj in _SAP_KNOWN_TABLES:
            continue
        # 3. Known FM/BAPI name prefix
        if obj.startswith(_SAP_FM_PREFIXES):
            continue
        # 4. Common English word or ABAP keyword or SAP advisory term
        if obj in _COMMON_WORDS:
            continue
        # 5. Custom Z/Y objects — we cannot validate these from a reference list
        if obj.startswith(("Z", "Y")):
            continue
        # 6. Too short to be a meaningful SAP object name
        if len(obj) < 4:
            continue
        # 7. SAP transaction code pattern: 1-4 alpha + 0-2 digits, max 6 chars,
        #    no underscore (OBA7, SE16, SPRO, MIGO, VF01, ME21N, FB01)
        if not "_" in obj and len(obj) <= 6 and _re.match(r"^[A-Z][A-Z0-9]{1,5}$", obj):
            continue
        # 8. Authorisation / check object pattern: F_*, S_*, P_*, M_*, C_*
        #    These are legitimate to mention in advisory context
        if _re.match(r"^[FSPMCE]_[A-Z]", obj):
            continue
        # 9. Local/global variable prefixes used in explanatory text
        #    LV_, GS_, GT_, LS_, LT_, GV_, WA_, IT_, IS_, IV_, EV_, ES_, ET_ etc.
        if _re.match(r"^[GL][VSTIE][_]", obj) or _re.match(r"^[WI][AT]_", obj):
            continue
        # Passed all filters — this looks like it could be an invented SAP object
        warnings.append(
            f"SAP object '{obj}' appears in the report but not in the uploaded "
            f"code — verify this name is correct"
        )

    return annotated, warnings


SYSTEM_PROMPT_REVIEWER = (
    "You are a senior SAP quality assurance reviewer checking an AI-generated "
    "SAP code analysis report for accuracy before it reaches a customer.\n\n"
    "Your job is to identify and correct:\n"
    "1. SAP object names (tables, FMs, BAPIs, transaction codes, field names) "
    "that do not appear in the uploaded code and may be hallucinated\n"
    "2. SAP Note numbers that are not valid integers (4-7 digits)\n"
    "3. [HIGH CONFIDENCE] findings that lack a quoted Evidence line\n"
    "4. Statements that conflate what the code does with SAP standard behaviour\n"
    "5. Statements that say a BAPI 'ensures', 'guarantees', or 'enforces' authorisations\n"
    "6. Overstatements — claiming something is definitely wrong when it is only "
    "possibly wrong given what can be seen in the code\n"
    "7. Absolute compliance claims: 'SOX violation', 'GDPR violation', "
    "'compliance violation', 'guaranteed', 'will definitely', 'inevitably'\n"
    "8. Absolute security claims: 'complete bypass', 'full bypass', "
    "'unauthorized access will occur', 'bypasses all controls'\n"
    "   Security outcomes depend on role design and system config — not confirmable from code.\n\n"
    "For each issue found, output:\n"
    "ISSUE [N]: [brief description]\n"
    "LOCATION: [quote the problematic sentence]\n"
    "CORRECTION: [corrected version, or REMOVE if the statement should be deleted]\n\n"
    "If no issues are found, output exactly: REVIEW PASSED — no accuracy issues detected.\n\n"
    "Be thorough but do not manufacture issues. Leave accurate, well-evidenced "
    "statements alone. The goal is accuracy, not excessive caution."
)


def _self_review_pass(client, report: str, code_context: str) -> tuple:
    """
    Send the draft report and original code to a reviewer model.
    Returns (review_notes, cleaned_report).
    If the reviewer finds issues, a correction pass applies them.
    """
    review_msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT_REVIEWER,
        messages=[{
            "role": "user",
            "content": (
                "Please review the following SAP analysis report for accuracy.\n\n"
                "=== UPLOADED CODE ===\n"
                + code_context[:30_000]
                + "\n\n=== DRAFT REPORT ===\n"
                + report
            ),
        }],
    )
    review_notes = review_msg.content[0].text

    if "REVIEW PASSED" in review_notes:
        return review_notes, report

    # Apply corrections
    correction_msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=5000,
        system=(
            "You are correcting an SAP analysis report based on reviewer feedback. "
            "Apply every CORRECTION listed in the review notes to the report. "
            "Where the correction says REMOVE, delete that sentence. "
            "Output only the complete corrected report — no preamble, no explanation."
        ),
        messages=[{
            "role": "user",
            "content": (
                "=== REVIEW NOTES ===\n"
                + review_notes
                + "\n\n=== ORIGINAL REPORT ===\n"
                + report
            ),
        }],
    )
    return review_notes, correction_msg.content[0].text


def _get_client():
    """Return an authenticated Anthropic client."""
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except KeyError:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not found in Streamlit secrets. "
            "Create .streamlit/secrets.toml and add:\n"
            "    ANTHROPIC_API_KEY = \"sk-ant-your-key-here\""
        )
    return anthropic.Anthropic(api_key=api_key)


# ── API call: Single Program ───────────────────────────────────────────────────
def analyse_single(code_text: str) -> str:
    """Analyse one ABAP program with self-review and output validation."""
    client = _get_client()

    # Pass 1 — initial analysis
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT_SINGLE,
        messages=[{
            "role": "user",
            "content": (
                "Please analyse the following SAP ABAP code and produce the "
                "structured report described in your instructions.\n\n"
                "```abap\n" + code_text + "\n```"
            ),
        }],
    )
    draft = message.content[0].text

    # Pass 2 — self-review and correction
    _, cleaned = _self_review_pass(client, draft, code_text)

    # Pass 3 — output validation
    code_objects = _extract_code_objects(code_text)
    validated, warnings = _validate_report(cleaned, code_objects)

    if warnings:
        warning_lines = "\n".join(f"- {w}" for w in warnings[:10])
        validated += (
            "\n\n---\n"
            "**⚠ Accuracy Review Notes** "
            "*(for analyst review before sharing with client)*\n"
            + warning_lines
        )

    # Pass 4 — executive brief (prepended for PDF renderer)
    brief = generate_executive_brief(client, validated, "single")
    return f"__EXECUTIVE_BRIEF__\n{brief}\n__END_BRIEF__\n\n{validated}"



# ── Configuration injection ────────────────────────────────────────────────────
def _extract_config_facts(files: list) -> str:
    """
    Scan uploaded files labelled as configuration data and extract verified
    key-value facts to inject into the prompt as ground truth.

    Handles: tab-delimited SE16/SM30 exports, CSV, pipe-delimited,
    functional specifications, and transport logs.
    Returns a formatted string ready to prepend to the API user message,
    or an empty string if no config files are present.
    """
    CONFIG_LABELS = {
        "Configuration Data (SE16/SM30)",
        "Functional Specification",
        "Transport Log",
        "Org Structure / SPRO Export",
    }

    TRANSPORT_PREFIXES = (
        "PROG", "FUNC", "TABD", "TOBJ", "DTEL", "DOMA", "VIEW",
        "R3TR", "LIMU", "CLAS", "INTF", "ENQU", "AUTH",
    )

    facts = []

    for f in files:
        label   = f.get("label", "")
        content = f["content"].strip()
        name    = f["name"]

        if label not in CONFIG_LABELS:
            continue

        if label == "Functional Specification":
            snippet = content[:3000].replace("\n", " ").replace("\r", "")
            facts.append(
                f"FUNCTIONAL SPECIFICATION ({name}):\n{snippet}\n"
                "[End of spec excerpt]"
            )
            continue

        if label == "Transport Log":
            lines = content.splitlines()
            obj_lines = [
                l.strip() for l in lines
                if any(l.strip().startswith(p) for p in TRANSPORT_PREFIXES)
            ]
            if obj_lines:
                facts.append(
                    f"TRANSPORT LOG ({name}) — objects included:\n"
                    + "\n".join(obj_lines[:50])
                )
            continue

        # Tabular config file — detect delimiter
        first_line = content.splitlines()[0] if content.splitlines() else ""
        if "\t" in first_line:
            delimiter = "\t"
        elif "|" in first_line:
            delimiter = "|"
        elif ";" in first_line:
            delimiter = ";"
        elif "," in first_line:
            delimiter = ","
        else:
            facts.append(
                f"CONFIGURATION DATA ({name}):\n" + content[:2000]
            )
            continue

        import csv as _csv, io as _io
        try:
            reader = _csv.reader(_io.StringIO(content), delimiter=delimiter)
            rows   = [r for r in reader if any(c.strip() for c in r)]
        except Exception:
            facts.append(
                f"CONFIGURATION DATA ({name}): [parse error — raw text]\n"
                + content[:1000]
            )
            continue

        if not rows:
            continue

        headers    = [h.strip().upper() for h in rows[0]]
        table_name = name.replace(".txt", "").replace(".csv", "").upper()
        fact_lines = [f"TABLE/CONFIG DATA: {table_name} ({name})"]

        for row in rows[1:51]:
            cells = [c.strip() for c in row]
            if not any(cells):
                continue
            pairs = [
                f"{h}={v}"
                for h, v in zip(headers, cells)
                if h and v
            ]
            if pairs:
                fact_lines.append("  " + " | ".join(pairs))

        if len(fact_lines) > 1:
            facts.append("\n".join(fact_lines))

    if not facts:
        return ""

    separator = "=" * 51
    return (
        f"\n\n{separator}\n"
        "CUSTOMER CONFIGURATION DATA (from uploaded exports)\n"
        "Use as primary reference for this customer's system.\n"
        "IMPORTANT — state these caveats in your report:\n"
        "  - Exports may be from a test/development system, not production\n"
        "  - May be partial (not all config visible)\n"
        "  - Where config contradicts code behaviour, flag the discrepancy\n"
        "  - Prefix config-based statements with: 'Based on provided exports'\n"
        f"{separator}\n\n"
        + "\n\n".join(facts)
        + f"\n{separator}\n"
    )

# ── API call: Repository Bundle ────────────────────────────────────────────────
def analyse_bundle(files: list) -> str:
    """Analyse multiple SAP objects with self-review and config injection."""
    client = _get_client()

    # Extract verified config facts to inject as ground truth
    config_facts = _extract_config_facts(files)

    parts = []
    for i, f in enumerate(files, 1):
        label   = f["label"] or f["type"].upper()
        content = f["content"]
        if len(content) > 40_000:
            content = content[:40_000] + "\n\n[... truncated to 40,000 characters ...]"
        parts.append(f"=== OBJECT {i}: {f['name']} [{label}] ===\n{content}")
    combined = "\n\n".join(parts)

    user_content = (
        f"I have uploaded {len(files)} SAP objects from our custom code estate. "
        "Please produce the full estate analysis report as described.\n\n"
    )
    if config_facts:
        user_content += config_facts + "\n\n"
        user_content += "=== SAP CODE OBJECTS FOR ANALYSIS ===\n\n"
    user_content += combined

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        system=SYSTEM_PROMPT_BUNDLE,
        messages=[{"role": "user", "content": user_content}],
    )
    draft = message.content[0].text
    _, cleaned = _self_review_pass(client, draft, combined[:30_000])
    brief = generate_executive_brief(client, cleaned, "bundle")
    return f"__EXECUTIVE_BRIEF__\n{brief}\n__END_BRIEF__\n\n{cleaned}"


# ── API call: S/4HANA Readiness ────────────────────────────────────────────────
def analyse_s4hana(files: list) -> str:
    """S/4HANA readiness scan with self-review and config injection."""
    client = _get_client()

    # Extract verified config facts — grounds the migration assessment
    config_facts = _extract_config_facts(files)

    parts = []
    for i, f in enumerate(files, 1):
        label   = f["label"] or f["type"].upper()
        content = f["content"]
        if len(content) > 40_000:
            content = content[:40_000] + "\n\n[... truncated ...]"
        parts.append(f"=== PROGRAM {i}: {f['name']} [{label}] ===\n{content}")
    combined = "\n\n".join(parts)

    user_content = (
        f"Please perform an S/4HANA readiness assessment on the following "
        f"{len(files)} SAP program(s).\n\n"
    )
    if config_facts:
        user_content += config_facts + "\n\n"
        user_content += "=== SAP PROGRAMS TO ASSESS ===\n\n"
    user_content += combined

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        system=SYSTEM_PROMPT_S4HANA,
        messages=[{"role": "user", "content": user_content}],
    )
    draft = message.content[0].text
    _, cleaned = _self_review_pass(client, draft, combined[:30_000])

    # Scope estimate — appended before packaging
    scope = generate_scope_estimate(client, cleaned)
    full_report = cleaned + "\n\n" + scope

    # Executive brief — prepended for PDF renderer
    brief = generate_executive_brief(client, full_report, "s4hana")
    return f"__EXECUTIVE_BRIEF__\n{brief}\n__END_BRIEF__\n\n{full_report}"



# ── PDF engine ────────────────────────────────────────────────────────────────
#
# Architecture (four separated concerns):
#   VivrtaLayout   — single source of truth for every spacing/colour constant
#   VivrtaPDF      — FPDF subclass: font registration + page chrome only
#   VivrtaRenderer — all content drawing primitives; reads from VivrtaLayout
#   build_pdf()    — public entry point; orchestrates cover → metadata → body
#
# To adjust any spacing or colour, change the value in VivrtaLayout only.
# Nothing in VivrtaRenderer or VivrtaPDF contains hard-coded measurements.

# Subsetted DejaVu Sans fonts embedded as base64 — no OS fonts or downloads needed.
# Generated from DejaVu Sans 2.37 (dejavu-fonts.sourceforge.net) — Bitstream Vera licence.
_FONT_B64 = {
    "regular": "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oKa6oP386gMTAhIBeQIO/v390P4e/GnqAAECjf38A1AHiQAEAAABESMRMANQwweJ9nMJjQABALD+FANQB4kACwAAATMVEAMCAyMSExIRAo3DoJDQoMuTfweJ6vzN/dv+Ev67AZsB7AGpA1sAAAEAsP38A1AHbQAFAAABIxEhFSEBc8MCoP4j/fwJccMAAQCw/fwBcweJAAMAABMzESOww8MHifZzAAABALD+FANQB4kABQAAAREhFSERAXMB3f1gB4n3TsMJdQAAAQCw/fwDUAdtAAUAAAERITUhEQKN/iMCoP38CK7D9o8AAAECjf38A1AHegADAAABMxEjAo3Dwwd69oIAAQCw/hQDUAd6AAUAAAEzESE1IQKNw/1gAd0HevaawwABAqP96gVYB20ADQAAASMRNDc2MyEVISIHBhUDXbpveboBE/7nZUQ5/eoHdd+RnrBmV5kAAQCo/fwDXQeGABgAAAEWFxYZASMRECcmJSc1MyA3NhkBMxEQBwYClDoqZbpuS/77PT0BA01uumUoAsEgPZP+Q/3oAgwBt19BBAG7RWMBswIM/ej+SJg8AAECo/4UBVgHhgANAAABERQXFjMhFSEiJyY1EQNdOURlARn+7bh7bweG+JSaVmawno/hB2QAAAECo/30A10HjAADAAABIxEzA126uv30CZgAAQCo/eoDXQdtAA0AAAERNCcmIyE1ITIXFhURAqM5RGX+5wETunlv/eoHfZlXZrCekd/4iwAAAQKj/fwFWAeGABgAAAEmJyYZATMREBcWITMVBwQHBhkBIxEQNzYDbDwoZbpuTQEDPT3++0tuumUqAsEhPJgBuAIY/fT+TWNFuwEEQV/+Sf30AhgBvZM9AAEAqP4UA10HhgANAAABMxEUBwYjITUhMjc2NQKjum97uP7tARllRDkHhvic4Y+esGZWmgABAC8AAAWqBhQAJABIQBMmAAcJBQgMIRgNHggRDCEQFEwlEPw8xDLE/DzEEDz8PMTExDEAQBEJDRGpEgIahwAYlwYfErwLDy885jIy/jzuMhDuMjIwARUjIgYdASEVIREjESERIxEjNTM1NDY7ARUjIgcGHQEhNTQ2MwWqsGNNAS/+0bn+B7mwsK69rrBjJyYB+a69BhSZUGhjj/wvA9H8LwPRj067q5koKGhjTrurAAIALwAABEoGFAAVABkAUkAR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Ay4tCQUuEAMtCQMsMgMrKiUFK2QDKikSBSolAykSAygnJQUoQQMnJQMmJQsFJg8DJQsDJP4DI/4DIg8DIQEQBSESAyBkAx/6Ax4dDQUeZAMdDQMcEUIFHP4DG/oDGkIDGRFCBRn+AxhkAxcWGQUX/gMWARAFFhkDFf4DFP4DE/4DEhFCBRL+AxECLQURQgMQfQMPZAMO/gMNDBYFDf4DDAEQBQwWAwv+AwoQAwn+AwgCLQUI/gMHFAMGZAMEARAFBP4DQBUDAi0FA/4DAgEQBQItAwEQAwD+AwG4AWSFjQErKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysAKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKx0BNQC4AMsAywDBAKoAnAGmALgAZgAAAHEAywCgArIAhQB1ALgAwwHLAYkCLQDLAKYA8ADTAKoAhwDLA6oEAAFKADMAywAAANkFAgD0AVQAtACcATkBFAE5BwYEAAROBLQEUgS4BOcEzQA3BHMEzQRgBHMBMwOiBVYFpgVWBTkDxQISAMkAHwC4Ad8AcwC6A+kDMwO8BEQEDgDfA80DqgDlA6oEBAAAAMsAjwCkAHsAuAAUAW8AfwJ7AlIAjwDHBc0AmgCaAG8AywDNAZ4B0wDwALoBgwDVAJgDBAJIAJ4B1QDBAMsA9gCDA1QCfwAAAzMCZgDTAMcApADNAI8AmgBzBAAF1QEKAP4CKwCkALQAnAAAAGIAnAAAAB0DLQXVBdUF1QXwAH8AewBUAKQGuAYUByMB0wC4AMsApgHDAewGkwCgANMDXANxA9sBhQQjBKgESACPATkBFAE5A2AAjwXVAZoGFAcjBmYBeQRgBGAEYAR7AJwAAAJ3BGABqgDpBGAHYgB7AMUAfwJ7AAAAtAJSBc0AZgC8AGYAdwYQAM0BOwGFA4kAjwB7AAAAHQDNB0oELwCcAJwAAAd9AG8AAABvAzUAagBvAHsArgCyAC0DlgCPAnsA9gCDA1QGNwX2AI8AnAThAmYAjwGNAvYAzQNEACkAZgTuAHMAABQAAJYAAAAAAAcAWgADAAEECQAAATAAAAADAAEECQABABYBMAADAAEECQACAAgBRgADAAEECQADABYBMAADAAEECQAEABYBMAADAAEECQAFABgBTgADAAEECQAGABQBZgBDAG8AcAB5AHIAaQBnAGgAdAAgACgAYwApACAAMgAwADAAMwAgAGIAeQAgAEIAaQB0AHMAdAByAGUAYQBtACwAIABJAG4AYwAuACAAQQBsAGwAIABSAGkAZwBoAHQAcwAgAFIAZQBzAGUAcgB2AGUAZAAuAAoAQwBvAHAAeQByAGkAZwBoAHQAIAAoAGMAKQAgADIAMAAwADYAIABiAHkAIABUAGEAdgBtAGoAbwBuAGcAIABCAGEAaAAuACAAQQBsAGwAIABSAGkAZwBoAHQAcwAgAFIAZQBzAGUAcgB2AGUAZAAuAAoARABlAGoAYQBWAHUAIABjAGgAYQBuAGcAZQBzACAAYQByAGUAIABpAG4AIABwAHUAYgBsAGkAYwAgAGQAbwBtAGEAaQBuAAoARABlAGoAYQBWAHUAIABTAGEAbgBzAEIAbwBvAGsAVgBlAHIAcwBpAG8AbgAgADIALgAzADUARABlAGoAYQBWAHUAUwBhAG4AcwADAAAAAAAA/34AWgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAIAAL//wADAAEAAAAMAAAAAAAAAAIABQABAGEAAQBiAGwAAgBtAH8AAQCAAIUAAgCGAIkAAQAAAAEAAAAKAC4APAACREZMVAAObGF0bgAYAAQAAAAA//8AAAAEAAAAAP//AAEAAAABa2VybgAIAAAAAQAAAAEABAACAAAAAQAIAAIKHgAEAAAKXgrQACEAJwAAAAAAAAAA/9P/twAAAAAAAABLAHIAOQBLAAD/RAAA/4j/rf+a/w0AAAAAAAAAAAAAAAAAAAAAAAAAAAAmAAAAAAAAAAD/yQAAAAD/3AAA/9P/3P/cADkAAP/cAAAAAP/cAAD/3P/cAAD/YQAA/33/kAAA/2EAAAAA/9z/3P/c/7cAAAAAAAAAAP/cAAAAAP/cAAD/iP+tAAD/dQAAAAAAAAAAAAAAAP/cAAAAAP/cAAD/3AAA/9wAAAAA/8H/twAA/5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9wAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9wAAAAA/5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD+t/9h/0QAAAAAAAAAAAAAAAAAAAAA/9z/3AAAAAAAAAAAAAAAAP9EAAAAAP+QAAAAAP9rAAAAAP+3/2sAAAAA/5AAAAAAAAD/RAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/twAAAAAAAAAA/5oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/3AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/7cAAAAA/9wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/ykAAAAA/9wAAP+QAAAAAAAAAAD/kAAAAAD/Yf/JAAD/twAA/7cAAP/cAAAAAP+aAAAAAAAAAAAAAP+aAAAAAAAA/5oAAAAAAAD/awAA/9wAAAAAAC8AAAAAAAAAAAAAAAD/twAAAAD+5v+a/x//RAAA/vAAAAAAAAAAAP/cAAAAAAAAAAAAAP/cAAAAAAAA/9wAAAAAAAD/RAAAADn/rf/c/9wAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9wAAP99/5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9P+wQAA/30AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9MAAP+kAAAAAP+3AAAAAP/T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",
    "bold":    "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gv4Dgf4DgBkDfwoDfv4Dff4DfP4De/oDevoDef4Dd3amBXf+A3amA3V0GwV1+gN0GwNz+gNyfQNx/gNwbywFbywDbvoDbfoDbPoDa/4Dav4Daf4DaGMMBWgyA2f+A2YyA2VkCgVl/gNkCgNkQARjYgoFYwwDYgoDYWAVBWGWA2ABEQVgFQNfCgNe/gNd/gNcAREFXP4DW1obBVv+A1oBEQVaGwNZ/gNY+gNX/gNWAREFQP9W/gNV/gNUHgNTFANSURkFUvoDUQERBVEZA1BPGQVQ+gNPThEFTxkDThEDTR4DTEsUBUwVA0tKEQVLFANKSQ4FShEDSQ4DSPoDR0YUBUcVA0YUA0X6A0RDDgVEDwNDDgNCQSUFQvoDQQERBUElA0A/DwVA/gM/Pg4FPw8DPg4DPTwNBT0WAzwNAztkAzr+AzkUAzj+AzcTAzY1GgU2JQM1NBQFNRoDNcAENAoNBTQUAzSABDMyDAUzFAMzQAQyDAMxMKYFMf4DMAERBTCmAy8MAy4TAy0sOgUt+gMsFSUFLDoDK2QDKmQDKf4DKBUDJxcRBSceAyYgAyUeAyQjEQVAKyQeAyMRAyIADQUi+gMhDwMhQAQgFAMfCgMeHgMdHBkFHSUDHA8TBRwZAxy4AQBAkQQbDQMaGUsFGn0DGQERBRlLAxj+AxcRAxYVJQUW+gMVAREFFSUDFGQDExEDEv4DEQERBRH+AxBkAw8OEAUPEwMPwAQOEAMOgAQNAREFDfoDDDIDCwoNBQsWAwuABAoNAwpABAn+Awj+Awf+AwYFCgUG/gMFCgMFQAQE+gMDZAMCAREFAv4DAQANBQERAwANAwG4AWSFjQErKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrACsrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKx0AAWYBMwFmALwA6QAAAT0AogD6Ax8AAgACAGYBZgACAAIArAFUAOwAvABiAWYBgQSFAVQBZgFtBKQAAgFmAH8EzQAAAAIBMwBiAHEAAAAlBKQBvAC6AOUAZgGBAY0FSAVaAWYBbQAAAAAAAgACAPYFwwHwBTkCOQBYBG0EPQSyBIEEsgFmAXUEZgSBALAEZgQ5AtEEnAR7BM8EewBYATMBZgFMAWYBTAACAKwAmgFKASMAmgKaAUQBGQFEAs0AwQAAAWYBPwGaATsFywXLANUA1QFQAKwArAB3AgoBxwHyAS8BWAGyASMA9gD2AR8BLwE1AjUB7gHnATMAmADRA1gFCgCaAI8BEgCYALwAzQDlAOUA8gBzBAABZgCPBdUCKwXVAMMA4QDXAOUAAABqAQIAAAAdAy0F1QXVBfAAqABqAOwA4QECBdUGFAchBGYC+ADsAYMCpgL4ASMBAgECARIBHwMfAF4DzQRgBMcEiQDsAbwAugECAzMDHwNCAzMDXAESAR8F1QGaAJoA4QZmAXkEYARgBGAEewAAAOwCwwK4As0AvgDdANUAAABqAlwCewKaAN0BrgG6ARIAAACFAa4EYAdiBBsAmgaaBFgA7gCaApoA0QLNAZoBUAXLBcsAiwCLBjEA9gQGAPADTAFgBKgAwQAAACUFwQEAASEHSgYSAJYBSgeDAKgAAAM3AHsAFAAAAMkBAAXBBcEFwQXBAQABCAYdAJYEJwOeAOwBAgJ9ATMAmADRA1gBeQDNAjkDYgCcAJwAnACTAbgAkwC4AHMAABQAAyYAAAAHAFoAAwABBAkAAAEwAAAAAwABBAkAAQAWATAAAwABBAkAAgAIAUYAAwABBAkAAwAgAU4AAwABBAkABAAgAU4AAwABBAkABQAYAW4AAwABBAkABgAeAYYAQwBvAHAAeQByAGkAZwBoAHQAIAAoAGMAKQAgADIAMAAwADMAIABiAHkAIABCAGkAdABzAHQAcgBl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",
    "oblique": "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BQIYAwEKAwFABAAcAwG4AWSFjQErKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKwArKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKx0AAAEjAS8AuADLALgAwQCqAMcCxwCgADcANwBSAL4BiQItAMsApgCHANkFAgC0AJwBOQEUATkANwDTBhQGeQWFBagAywBcALgASAEvANkAkwAAAMsAuAC4AH8CewJQAGYAxwXNAJoAmgBvAMsAuADwALoBgwDVAJgAywJIAPYAgwNUAI8AjwCaAHMEAAXVAQoA/gIrAKQAtACcAJwAAABiAAAAHQMtBdUF1QXVBfAAfwB7AFQApAa4BhQB0wC4AMsApgHDAewA6QCgANMDXANxAGIAnACoAYUEIwSoBEgAjwE5ARQBOQNgAI8CgwGaBGAEYARgBHsAAAJ3AJwEYAGqBhQAxQB/AnsAAAJQBc0AZgC8AGYAdwDNATsBhQOJAI8AewAAAB0F1QDNB0oELwCcAJwAAAd9AzUAbwAAAG8ArgCyAC0DlgJ7APYAgwNUBmYAnAJmAI8C9gNxAM0DRAApAGYAcwAAFAAAlgAVAAAABwBaAAMAAQQJAAABMAAAAAMAAQQJAAEAFgEwAAMAAQQJAAIADgFGAAMAAQQJAAMAJgFUAAMAAQQJAAQAJgFUAAMAAQQJAAUAGAF6AAMAAQQJAAYAJAGSAEMAbwBwAHkAcgBpAGcAaAB0ACAAKABjACkAIAAyADAAMAAzACAAYgB5ACAAQgBpAHQAcwB0AHIAZQBhAG0ALAAgAEkAbgBjAC4AIABBAGwAbAAgAFIAaQBnAGgAdABzACAAUgBlAHMAZQByAHYAZQBkAC4ACgBDAG8AcAB5AHIAaQBnAGgAdAAgACgAYwApACAAMgAwADAANgAgAGIAeQAgAFQAYQB2AG0AagBvAG4AZwAgAEIAYQBo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",
}


def _resolve_fonts() -> dict[str, str]:
    """
    Write the embedded font bytes to temp files and return their paths.
    Uses only the Python standard library — no OS fonts, no downloads.
    """
    import base64, tempfile, pathlib, atexit

    paths = {}
    for key, b64 in _FONT_B64.items():
        tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
        tmp.write(base64.b64decode(b64))
        tmp.close()
        paths[key] = tmp.name
        atexit.register(lambda p=tmp.name: pathlib.Path(p).unlink(missing_ok=True))
    return paths


_FONTS = _resolve_fonts()


# ─────────────────────────────────────────────────────────────────────────────
# 1. LAYOUT SPEC — single source of truth for every measurement and colour
# ─────────────────────────────────────────────────────────────────────────────
class VivrtaLayout:
    """
    All spacing, colour, and typography constants in one place.
    Nothing in the rendering layer hard-codes a number; it reads from here.
    To change any visual property, edit this class only.
    """

    # ── Page geometry (mm) ────────────────────────────────────────────────────
    PAGE_W          = 210           # A4 width
    PAGE_H          = 297           # A4 height
    MARGIN_LEFT     = 18
    MARGIN_RIGHT    = 18
    MARGIN_BOTTOM   = 20            # fpdf auto-page-break margin
    BODY_W          = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT   # 174 mm

    # ── Header bar ────────────────────────────────────────────────────────────
    HEADER_H        = 10            # height of indigo top bar
    HEADER_TEXT_Y   = 2             # text baseline inside bar
    HEADER_FONT_SZ  = 9
    HEADER_FIRST_Y  = 14            # where body starts on every page (after bar)

    # ── Footer ────────────────────────────────────────────────────────────────
    FOOTER_LINE_Y   = -14           # rule: mm from bottom of page
    FOOTER_TEXT_Y   = -12           # text: mm from bottom of page
    FOOTER_FONT_SZ  = 7.5

    # ── Cover block (first page only) ─────────────────────────────────────────
    COVER_H         = 32            # height of dark title rectangle
    COVER_PAD_X     = 6             # left inset inside cover rectangle
    COVER_PAD_Y     = 7             # top inset inside cover rectangle
    COVER_TITLE_SZ  = 15
    COVER_TITLE_LH  = 9
    COVER_SUB_SZ    = 8.5
    COVER_SUB_LH    = 5
    COVER_GAP_AFTER = 5             # gap between cover block and metadata box

    # ── Metadata box (first page only) ────────────────────────────────────────
    META_PAD_X      = 5             # inner horizontal padding
    META_PAD_Y      = 4             # inner vertical padding
    META_LABEL_W    = 36            # width of the bold label column
    META_ROW_LH     = 5             # line height for each metadata row
    META_ROW_GAP    = 1.5           # vertical gap between rows
    META_LABEL_SZ   = 8
    META_VALUE_SZ   = 8.5
    META_GAP_AFTER  = 6             # gap after metadata box before first section

    # ── Section headings ─────────────────────────────────────────────────────
    SECTION_RULE_BEFORE = 4         # gap before the horizontal rule
    SECTION_RULE_AFTER  = 3         # gap between rule and heading text
    SECTION_HEAD_SZ     = 11
    SECTION_HEAD_LH     = 7
    SECTION_HEAD_AFTER  = 2         # gap after heading before content

    # ── Body text ─────────────────────────────────────────────────────────────
    BODY_SZ         = 9.5
    BODY_LH         = 5.5
    BODY_AFTER      = 1.5

    # ── Numbered list ─────────────────────────────────────────────────────────
    NUM_INDENT      = 7
    NUM_SZ          = 9.5
    NUM_LH          = 5.5

    # ── Bullet list ──────────────────────────────────────────────────────────
    BULLET_EXTRA_X  = 3             # extra left indent beyond MARGIN_LEFT
    BULLET_COL_W    = 4
    BULLET_SZ       = 9.5
    BULLET_LH       = 5.5

    # ── Risk badge items ──────────────────────────────────────────────────────
    BADGE_PAD_X     = 2.5           # horizontal padding inside badge pill
    BADGE_SZ        = 8
    BADGE_H         = 5.5
    BADGE_GAP_X     = 2             # gap between pill and text
    BADGE_TEXT_SZ   = 9.5
    BADGE_TEXT_LH   = 5.5
    BADGE_AFTER     = 1.5

    PLAIN_RISK_SZ   = 9
    PLAIN_RISK_LH   = 5.5
    PLAIN_RISK_AFTER = 1

    # ── Glossary ─────────────────────────────────────────────────────────────
    GLOSS_TERM_SZ    = 9.5
    GLOSS_DEFN_SZ    = 9.5
    GLOSS_LH         = 5.5
    GLOSS_AFTER      = 1.5       # increased for readability
    GLOSS_MIN_TERM_W = 45        # minimum term column width (mm)

    # ── Tables ───────────────────────────────────────────────────────────────
    TBL_ROW_H          = 5.5        # base row height (single line of text)
    TBL_CELL_PAD_X     = 1.8       # horizontal padding inside each cell
    TBL_CELL_PAD_Y     = 1         # top padding inside each cell
    TBL_HEAD_SZ        = 8.5
    TBL_BODY_SZ        = 8.5
    TBL_FIRST_COL_FRAC = 0.18      # first column as fraction of BODY_W
    TBL_AFTER          = 4

    # ── Colours (R, G, B) ────────────────────────────────────────────────────
    C_BRAND_DARK   = (26,  26,  46)     # #1a1a2e — cover background
    C_BRAND_INDIGO = (79,  70, 229)     # #4f46e5 — header bar, section headings
    C_BRAND_GREY   = (107, 114, 128)    # #6b7280 — footer, muted text
    C_RULE         = (229, 231, 235)    # #e5e7eb — rules and table borders
    C_TEXT         = (17,  24,  39)     # #111827 — body copy
    C_TBL_HEAD_BG  = (238, 242, 255)    # #eef2ff — table header row fill
    C_TBL_ALT_BG   = (249, 250, 251)    # #f9fafb — alternating table row fill
    C_META_BG      = (248, 249, 255)    # light indigo tint — metadata box fill
    C_META_BORDER  = (199, 210, 254)    # #c7d2fe — metadata box border
    C_COVER_SUB    = (180, 180, 210)    # muted lavender — cover subtitle text
    C_BADGE_HIGH   = (220, 38,  38)     # red-600   — HIGH CONFIDENCE
    C_BADGE_MED    = (217, 119,  6)     # amber-600 — MEDIUM VERIFY
    C_BADGE_LOW    = (37,  99, 235)     # blue-600  — LOW NEEDS CONTEXT

    # ── Font family name (registered in VivrtaPDF) ────────────────────────────
    FONT = "DV"


# ─────────────────────────────────────────────────────────────────────────────
# 2. FPDF SUBCLASS — font registration + page chrome (header/footer) only
# ─────────────────────────────────────────────────────────────────────────────
class VivrtaPDF(FPDF):
    """
    Registers fonts and draws the indigo header bar and footer on every page.
    Contains NO content drawing logic — that lives entirely in VivrtaRenderer.
    """
    L = VivrtaLayout

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font(self.L.FONT,       fname=_FONTS["regular"])
        self.add_font(self.L.FONT, "B",  fname=_FONTS["bold"])
        self.add_font(self.L.FONT, "I",  fname=_FONTS["oblique"])

    def header(self):
        L = self.L
        # Indigo bar across full page width
        self.set_fill_color(*L.C_BRAND_INDIGO)
        self.rect(0, 0, L.PAGE_W, L.HEADER_H, "F")
        # Brand text centred vertically in bar
        self.set_xy(L.MARGIN_LEFT, L.HEADER_TEXT_Y)
        self.set_font(L.FONT, "B", L.HEADER_FONT_SZ)
        self.set_text_color(255, 255, 255)
        self.cell(0, L.HEADER_H - 2, "VIVRTA.AI  |  SAP Code Analyser",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Reset cursor to top of usable body area
        self.set_y(L.HEADER_FIRST_Y)

    def footer(self):
        L = self.L
        # Thin rule above footer text
        self.set_y(L.FOOTER_LINE_Y)
        self.set_draw_color(*L.C_RULE)
        self.set_line_width(0.3)
        self.line(L.MARGIN_LEFT, self.get_y(),
                  L.PAGE_W - L.MARGIN_RIGHT, self.get_y())
        # Legal disclaimer (centred)
        self.set_y(L.FOOTER_TEXT_Y)
        self.set_font(L.FONT, "", L.FOOTER_FONT_SZ)
        self.set_text_color(*L.C_BRAND_GREY)
        self.cell(
            0, 5,
            "Vivrta.AI  ·  vivrta.io  ·  "
            "AI-generated analysis. Review with a qualified SAP consultant "
            "before acting on this report.",
            align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        # Page number (right-aligned, same baseline as disclaimer)
        self.set_xy(L.PAGE_W - L.MARGIN_RIGHT - 20, self.get_y() - 5)
        self.cell(20, 5, f"Page {self.page_no()}", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ─────────────────────────────────────────────────────────────────────────────
# 3. RENDERER — all content drawing; every measurement from VivrtaLayout
# ─────────────────────────────────────────────────────────────────────────────
class VivrtaRenderer:
    """
    Draws all report content onto a VivrtaPDF instance.
    All spacing and colour values are read from VivrtaLayout — this class
    contains no numeric literals or colour tuples.
    """
    L = VivrtaLayout

    def __init__(self, pdf: VivrtaPDF):
        self.pdf = pdf

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _font(self, style: str = "", size: float | None = None, color: tuple | None = None):
        """Set font + optional text colour in one call."""
        self.pdf.set_font(self.L.FONT, style, size or self.L.BODY_SZ)
        if color is not None:
            self.pdf.set_text_color(*color)

    def _guard(self, needed_mm: float = 12.0):
        """Add a new page if fewer than needed_mm remain before the footer."""
        L = self.L
        if self.pdf.get_y() + needed_mm > L.PAGE_H - L.MARGIN_BOTTOM:
            self.pdf.add_page()

    # ── Cover block (first page, called once) ─────────────────────────────────
    def cover_block(self, title: str, subtitle: str) -> None:
        """Dark rectangle with large title and muted subtitle line."""
        L, pdf = self.L, self.pdf
        cy = pdf.get_y()
        pdf.set_fill_color(*L.C_BRAND_DARK)
        pdf.rect(L.MARGIN_LEFT, cy, L.BODY_W, L.COVER_H, "F")
        pdf.set_xy(L.MARGIN_LEFT + L.COVER_PAD_X, cy + L.COVER_PAD_Y)
        self._font("B", L.COVER_TITLE_SZ, (255, 255, 255))
        pdf.multi_cell(L.BODY_W - L.COVER_PAD_X * 2, L.COVER_TITLE_LH,
                       title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(L.MARGIN_LEFT + L.COVER_PAD_X)
        self._font("", L.COVER_SUB_SZ, L.C_COVER_SUB)
        pdf.multi_cell(L.BODY_W - L.COVER_PAD_X * 2, L.COVER_SUB_LH,
                       subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.COVER_GAP_AFTER)

    # ── Metadata box (first page, called once) ────────────────────────────────
    def metadata_box(self, rows: list) -> None:
        """
        Left-aligned box with a light indigo fill and border.
        rows: list of (label_str, value_str) tuples.
        """
        L, pdf = self.L, self.pdf
        row_h = L.META_ROW_LH + L.META_ROW_GAP
        box_h = (L.META_PAD_Y * 2) + (row_h * len(rows) * 1.8)  # generous for wrapping
        bx, by = L.MARGIN_LEFT, pdf.get_y()
        # Background
        pdf.set_fill_color(*L.C_META_BG)
        pdf.rect(bx, by, L.BODY_W, box_h, "F")
        # Border
        pdf.set_draw_color(*L.C_META_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(bx, by, L.BODY_W, box_h)
        # Rows — explicit Y tracking so wrapped values never desync labels
        ry = by + L.META_PAD_Y
        for label, value in rows:
            # Label: bold key at fixed X, fixed Y
            pdf.set_xy(bx + L.META_PAD_X, ry)
            self._font("B", L.META_LABEL_SZ, L.C_BRAND_GREY)
            pdf.cell(L.META_LABEL_W, L.META_ROW_LH,
                     label + ":", new_x=XPos.RIGHT, new_y=YPos.TOP)
            # Value: same Y, second column — multi_cell may wrap
            pdf.set_xy(bx + L.META_PAD_X + L.META_LABEL_W, ry)
            self._font("", L.META_VALUE_SZ, L.C_TEXT)
            pdf.multi_cell(
                L.BODY_W - L.META_PAD_X - L.META_LABEL_W, L.META_ROW_LH,
                value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Advance ry past actual cursor (handles wrapped values)
            ry = max(pdf.get_y(), ry + L.META_ROW_LH) + L.META_ROW_GAP
        pdf.set_y(ry + L.META_PAD_Y)

    # ── Section heading ───────────────────────────────────────────────────────
    def section_heading(self, text: str) -> None:
        """Horizontal rule followed by indigo bold heading."""
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=20)
        pdf.ln(L.SECTION_RULE_BEFORE)
        pdf.set_draw_color(*L.C_RULE)
        pdf.set_line_width(0.25)
        pdf.line(L.MARGIN_LEFT, pdf.get_y(),
                 L.PAGE_W - L.MARGIN_RIGHT, pdf.get_y())
        pdf.ln(L.SECTION_RULE_AFTER)
        pdf.set_x(L.MARGIN_LEFT)
        self._font("B", L.SECTION_HEAD_SZ, L.C_BRAND_INDIGO)
        pdf.multi_cell(L.BODY_W, L.SECTION_HEAD_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.SECTION_HEAD_AFTER)
        self._font("", color=L.C_TEXT)

    # ── Body paragraph ────────────────────────────────────────────────────────
    def body_text(self, text: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=8)
        pdf.set_x(L.MARGIN_LEFT)
        self._font("", L.BODY_SZ, L.C_TEXT)
        pdf.multi_cell(L.BODY_W, L.BODY_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.BODY_AFTER)

    # ── Numbered list item ────────────────────────────────────────────────────
    def numbered_item(self, number: str, text: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=8)
        pdf.set_x(L.MARGIN_LEFT)
        self._font("B", L.NUM_SZ, L.C_BRAND_INDIGO)
        pdf.cell(L.NUM_INDENT, L.NUM_LH, f"{number}.",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._font("", L.NUM_SZ, L.C_TEXT)
        pdf.multi_cell(L.BODY_W - L.NUM_INDENT, L.NUM_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Bullet list item ──────────────────────────────────────────────────────
    def bullet_item(self, text: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=8)
        pdf.set_x(L.MARGIN_LEFT + L.BULLET_EXTRA_X)
        self._font("", L.BULLET_SZ, L.C_TEXT)
        pdf.cell(L.BULLET_COL_W, L.BULLET_LH, "•",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.multi_cell(L.BODY_W - L.BULLET_COL_W - L.BULLET_EXTRA_X,
                       L.BULLET_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Risk badge item ───────────────────────────────────────────────────────
    def risk_item(self, badge_label: str, badge_color: tuple, text: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=10)
        bw = pdf.get_string_width(badge_label) + L.BADGE_PAD_X * 2
        y0 = pdf.get_y()
        pdf.set_xy(L.MARGIN_LEFT, y0)
        pdf.set_fill_color(*badge_color)
        self._font("B", L.BADGE_SZ, (255, 255, 255))
        pdf.cell(bw, L.BADGE_H, badge_label, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._font("", L.BADGE_TEXT_SZ, L.C_TEXT)
        pdf.set_x(L.MARGIN_LEFT + bw + L.BADGE_GAP_X)
        pdf.multi_cell(L.BODY_W - bw - L.BADGE_GAP_X, L.BADGE_TEXT_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.BADGE_AFTER)

    # ── Plain italic grey risk line ───────────────────────────────────────────
    def plain_risk_item(self, text: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=7)
        pdf.set_x(L.MARGIN_LEFT)
        self._font("I", L.PLAIN_RISK_SZ, L.C_BRAND_GREY)
        pdf.multi_cell(L.BODY_W, L.PLAIN_RISK_LH, text,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.PLAIN_RISK_AFTER)

    # ── Glossary entry ────────────────────────────────────────────────────────
    def glossary_item(self, term: str, definition: str) -> None:
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=8)
        pdf.set_x(L.MARGIN_LEFT)
        self._font("B", L.GLOSS_TERM_SZ, L.C_BRAND_DARK)
        # Enforce minimum term column so AUTHORITY-CHECK and similar never wrap
        tw = max(pdf.get_string_width(term) + 3, L.GLOSS_MIN_TERM_W)
        pdf.cell(tw, L.GLOSS_LH, term, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._font("", L.GLOSS_DEFN_SZ, L.C_TEXT)
        pdf.multi_cell(L.BODY_W - tw, L.GLOSS_LH, f"  —  {definition}",
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.GLOSS_AFTER)

    def executive_brief_box(self, brief_markdown: str) -> None:
        """
        Renders the Executive Brief as a styled panel immediately after the
        metadata box, before the detailed findings.

        Layout:
          • Dark indigo header bar with "EXECUTIVE BRIEF" label
          • Light lavender fill body with parsed sections:
              — "What This Code Does" as body paragraph
              — "Overall Risk Rating" with coloured rating badge
              — "Top 3 Actions" as numbered list
          • Rounded border in brand indigo
        """
        L, pdf = self.L, self.pdf

        RISK_COLORS = {
            "CRITICAL": L.C_BADGE_HIGH,
            "HIGH":     L.C_BADGE_HIGH,
            "MEDIUM":   L.C_BADGE_MED,
            "LOW":      L.C_BADGE_LOW,
        }

        # ── Parse brief sections ──────────────────────────────────────────────
        what_text    = ""
        rating_word  = ""
        rating_rest  = ""
        actions      = []

        current = None
        for raw_line in brief_markdown.split("\n"):
            line = raw_line.strip()
            if "## What This Code Does" in line:
                current = "what"
            elif "## Overall Risk Rating" in line:
                current = "rating"
            elif "## Top 3 Actions" in line:
                current = "actions"
            elif not line:
                continue
            elif current == "what":
                what_text += (" " if what_text else "") + _clean_md(line)
            elif current == "rating":
                # "HIGH — explanation text"
                parts = re.split(r"\s*[—–-]+\s*", line, maxsplit=1)
                rating_word = _clean_md(parts[0]).strip().upper()
                rating_rest = _clean_md(parts[1]).strip() if len(parts) > 1 else ""
            elif current == "actions":
                m = re.match(r"^\d+\.\s+(.*)", line)
                if m:
                    actions.append(_clean_md(m.group(1)))

        # ── Section header bar ────────────────────────────────────────────────
        self._guard(needed_mm=60)
        bx, by = L.MARGIN_LEFT, pdf.get_y()
        pdf.set_fill_color(*L.C_BRAND_DARK)
        pdf.rect(bx, by, L.BODY_W, 7, "F")
        pdf.set_xy(bx + 4, by + 1)
        self._font("B", 8, (255, 255, 255))
        pdf.cell(L.BODY_W - 8, 5, "EXECUTIVE BRIEF  —  Leadership Summary",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Light lavender body area ──────────────────────────────────────────
        body_y = pdf.get_y()
        # We'll draw the box after content so we know the height — use a scan pass
        content_start_y = body_y

        pdf.set_fill_color(248, 249, 255)   # very light indigo tint
        # Placeholder rect — we'll overdraw after measuring; use generous estimate
        est_h = 52
        pdf.rect(bx, body_y, L.BODY_W, est_h, "F")
        pdf.set_draw_color(*L.C_META_BORDER)
        pdf.set_line_width(0.35)
        pdf.rect(bx, by, L.BODY_W, est_h + 7)

        inner_x = bx + 5
        inner_w  = L.BODY_W - 10
        pdf.set_y(body_y + 4)

        # ── What This Code Does ───────────────────────────────────────────────
        pdf.set_x(inner_x)
        self._font("B", 8, L.C_BRAND_INDIGO)
        pdf.cell(inner_w, 4.5, "What This Code Does",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        pdf.set_x(inner_x)
        self._font("", 8.5, L.C_TEXT)
        pdf.multi_cell(inner_w, 4.8, what_text or "—",
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # ── Overall Risk Rating ───────────────────────────────────────────────
        pdf.set_x(inner_x)
        self._font("B", 8, L.C_BRAND_INDIGO)
        pdf.cell(inner_w, 4.5, "Overall Risk Rating",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

        # Badge + explanation on same line
        badge_color = RISK_COLORS.get(rating_word, L.C_BRAND_GREY)
        pdf.set_x(inner_x)
        bw = pdf.get_string_width(rating_word) + 6
        pdf.set_fill_color(*badge_color)
        self._font("B", 8, (255, 255, 255))
        pdf.cell(bw, 5.5, rating_word, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_x(inner_x + bw + 3)
        self._font("", 8.5, L.C_TEXT)
        pdf.multi_cell(inner_w - bw - 3, 5.5, rating_rest,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # ── Top 3 Actions ─────────────────────────────────────────────────────
        pdf.set_x(inner_x)
        self._font("B", 8, L.C_BRAND_INDIGO)
        pdf.cell(inner_w, 4.5, "Top 3 Actions for Leadership",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        for n, action in enumerate(actions[:3], 1):
            pdf.set_x(inner_x)
            self._font("B", 8.5, L.C_BRAND_INDIGO)
            pdf.cell(6, 5, f"{n}.",
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
            self._font("", 8.5, L.C_TEXT)
            pdf.multi_cell(inner_w - 6, 5, action,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)

    def finding_field(self, key: str, value: str) -> None:
        """
        Renders one field of a structured finding block.
        Bold indigo key label fixed at 38mm, normal body text for the value.
        Severity key gets an automatically coloured badge.
        """
        L, pdf = self.L, self.pdf
        self._guard(needed_mm=7)
        KEY_W = 38
        SEVERITY_COLORS = {
            "CRITICAL": L.C_BADGE_HIGH,
            "HIGH":     L.C_BADGE_HIGH,
            "MEDIUM":   L.C_BADGE_MED,
            "LOW":      L.C_BADGE_LOW,
        }
        if key.upper() == "SEVERITY":
            sev   = value.strip().upper().split()[0]
            color = SEVERITY_COLORS.get(sev, L.C_BRAND_GREY)
            bw    = pdf.get_string_width(value.strip()) + L.BADGE_PAD_X * 2
            pdf.set_x(L.MARGIN_LEFT)
            self._font("B", L.BODY_SZ, L.C_BRAND_INDIGO)
            pdf.cell(KEY_W, L.BODY_LH, key + ":",
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_fill_color(*color)
            self._font("B", L.BADGE_SZ, (255, 255, 255))
            pdf.cell(bw, L.BODY_LH, value.strip(), fill=True,
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(L.BODY_AFTER)
            return
        pdf.set_x(L.MARGIN_LEFT)
        self._font("B", L.BODY_SZ, L.C_BRAND_INDIGO)
        pdf.cell(KEY_W, L.BODY_LH, key + ":",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._font("", L.BODY_SZ, L.C_TEXT)
        pdf.multi_cell(L.BODY_W - KEY_W, L.BODY_LH, value,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(L.BODY_AFTER * 0.5)

    # ── Pipe table ────────────────────────────────────────────────────────────
    def render_table(self, rows: list) -> None:
        """
        Renders a markdown pipe table with standardised column widths,
        alternating row shading, and automatic row-height expansion for
        wrapped cell content. All measurements from VivrtaLayout.
        """
        L, pdf = self.L, self.pdf
        if not rows:
            return

        col_count = max(len(r) for r in rows)
        if col_count == 1:
            col_ws = [L.BODY_W]
        else:
            first_w = L.BODY_W * L.TBL_FIRST_COL_FRAC
            rest_w  = (L.BODY_W - first_w) / (col_count - 1)
            col_ws  = [first_w] + [rest_w] * (col_count - 1)

        first_content_row = True  # tracks first non-separator row
        for r_idx, row in enumerate(rows):
            # Skip markdown separator rows (---|---)
            if all(re.match(r"^[-: ]+$", str(c).strip())
                   for c in row if str(c).strip()):
                continue

            is_header = first_content_row
            first_content_row = False

            # Measure the tallest cell to set a uniform row height
            max_lines = 1
            for c_idx, cell in enumerate(row):
                ct    = re.sub(r"\*+", "", str(cell)).strip()
                cw    = col_ws[c_idx] if c_idx < len(col_ws) else col_ws[-1]
                chars = max(1, int(cw / 2.05))
                lines = max(1, len(textwrap.wrap(ct, chars)))
                max_lines = max(max_lines, lines)
            actual_h = max_lines * L.TBL_ROW_H

            self._guard(needed_mm=actual_h + 2)
            y_start = pdf.get_y()

            for c_idx, cell in enumerate(row):
                cw = col_ws[c_idx] if c_idx < len(col_ws) else col_ws[-1]
                ct = re.sub(r"\*+", "", str(cell)).strip()
                x  = L.MARGIN_LEFT + sum(col_ws[:c_idx])

                # Cell background
                if is_header:
                    pdf.set_fill_color(*L.C_TBL_HEAD_BG)
                    self._font("B", L.TBL_HEAD_SZ, L.C_BRAND_DARK)
                else:
                    pdf.set_fill_color(
                        *(L.C_TBL_ALT_BG if r_idx % 2 == 0 else (255, 255, 255))
                    )
                    self._font("", L.TBL_BODY_SZ, L.C_TEXT)

                pdf.set_xy(x, y_start)
                pdf.rect(x, y_start, cw, actual_h, "F")
                # Border
                pdf.set_draw_color(*L.C_RULE)
                pdf.set_line_width(0.2)
                pdf.rect(x, y_start, cw, actual_h)
                # Text (with padding)
                pdf.set_xy(x + L.TBL_CELL_PAD_X, y_start + L.TBL_CELL_PAD_Y)
                pdf.multi_cell(cw - L.TBL_CELL_PAD_X * 2, L.TBL_ROW_H, ct,
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_y(y_start + actual_h)

        pdf.ln(L.TBL_AFTER)


# ─────────────────────────────────────────────────────────────────────────────
# 4. MARKDOWN PARSER — converts AI markdown output into renderer calls
# ─────────────────────────────────────────────────────────────────────────────
_BADGE_MAP = {
    "[HIGH CONFIDENCE]":          ("HIGH CONFIDENCE",          VivrtaLayout.C_BADGE_HIGH),
    "[MEDIUM — VERIFY]":     ("MEDIUM — VERIFY",     VivrtaLayout.C_BADGE_MED),
    "[MEDIUM – VERIFY]":     ("MEDIUM — VERIFY",     VivrtaLayout.C_BADGE_MED),
    "[MEDIUM - VERIFY]":          ("MEDIUM — VERIFY",     VivrtaLayout.C_BADGE_MED),
    "[LOW — NEEDS CONTEXT]": ("LOW — NEEDS CONTEXT", VivrtaLayout.C_BADGE_LOW),
    "[LOW – NEEDS CONTEXT]": ("LOW — NEEDS CONTEXT", VivrtaLayout.C_BADGE_LOW),
    "[LOW - NEEDS CONTEXT]":      ("LOW — NEEDS CONTEXT", VivrtaLayout.C_BADGE_LOW),
}


def _clean_md(text: str) -> str:
    """Unwrap bold/italic and inline code, strip fences and stray markdown."""
    # 1. Strip triple-backtick fence markers (```lang or ```) before anything else
    text = re.sub(r"```[\w]*", "", text)
    # 2. Unwrap bold **text** → text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # 3. Unwrap italic *text* → text
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    # 4. Unwrap inline `code` → code (keep the identifier)
    text = re.sub(r"`([^`]+)`",       r"\1", text)
    # 5. Strip any residual lone backticks
    text = re.sub(r"`+",              "",     text)
    # 6. Strip leading markdown hash symbols
    text = re.sub(r"^#+\s*",         "",     text)
    return text.strip()


def _parse_and_render(renderer: VivrtaRenderer, markdown_text: str) -> None:
    """Walk the AI markdown line-by-line and call the appropriate renderer method."""
    lines      = markdown_text.split("\n")
    in_risk    = False
    table_rows: list = []
    in_table   = False

    def flush_table():
        nonlocal table_rows, in_table
        if table_rows:
            renderer.render_table(table_rows)
        table_rows.clear()
        in_table = False

    i = 0
    in_fence = False  # True while inside a ```...``` block
    while i < len(lines):
        line     = lines[i]
        stripped = line.strip()
        i += 1

        # ── Skip code fences (```...```) ─────────────────────────────────
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # ── Skip horizontal rule dividers (--- or ───────) ────────────────
        if re.match(r"^[-─]{3,}$", stripped):
            continue

        # ── Skip bare hash comment lines (# but not ##) ──────────────────
        if re.match(r"^#(?!#)", stripped):
            continue


        if stripped.startswith("## "):
            flush_table()
            heading = stripped[3:].strip()
            in_risk = "Risk" in heading or "Observation" in heading
            renderer.section_heading(heading)
            continue

        # Pipe-format table row  (| col | col |)
        if stripped.startswith("|"):
            in_table = True
            table_rows.append([c.strip() for c in stripped.strip("|").split("|")])
            continue

        # CSV-format table row  ("col","col") — AI sometimes emits this
        _csv_match = re.match(r'^\"[^\"]*\"', stripped)
        if _csv_match and stripped.count('"') >= 4:
            in_table = True
            _csv_cells = re.split(r'","', stripped.strip('"'))
            _csv_row = [c.replace('\\n',' ').replace('"','').strip() for c in _csv_cells]
            if any(_csv_row):
                table_rows.append(_csv_row)
            continue

        elif in_table:
            flush_table()

        if not stripped:
            continue

        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if m:
            renderer.numbered_item(m.group(1), _clean_md(m.group(2)))
            continue

        if in_risk and stripped.startswith("["):
            matched = False
            for key, (label, color) in _BADGE_MAP.items():
                if stripped.startswith(key):
                    rest = stripped[len(key):].lstrip(" —–-").strip()
                    renderer.risk_item(label, color, _clean_md(rest))
                    matched = True
                    break
            if not matched:
                renderer.plain_risk_item(_clean_md(stripped))
            continue

        # ── Structured finding field: **Key:** Value ──────────────────────────
        fm = re.match(r"^\*\*([^*:]{1,30}):\*\*\s*(.*)", stripped)
        if fm:
            renderer.finding_field(fm.group(1).strip(), _clean_md(fm.group(2).strip()))
            continue

        gm = re.match(r"^\*\*(.+?)\*\*\s*[—–-]+\s*(.*)", stripped)
        if gm:
            renderer.glossary_item(gm.group(1).strip(), gm.group(2).strip())
            continue

        if re.match(r"^[-*]\s+", stripped):
            renderer.bullet_item(_clean_md(re.sub(r"^[-*]\s+", "", stripped)))
            continue

        text = _clean_md(stripped)
        if in_risk:
            renderer.plain_risk_item(text)
        else:
            renderer.body_text(text)

    flush_table()


# ─────────────────────────────────────────────────────────────────────────────
# 5. PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def build_pdf(filename: str, analysis: str) -> bytes:
    """
    Renders a complete, standardised Vivrta.AI PDF report.
    Layout is fully controlled by VivrtaLayout — nothing is hard-coded
    in the rendering layer.  Safe to call with any analysis length.

    If analysis contains an __EXECUTIVE_BRIEF__ … __END_BRIEF__ sentinel block
    (injected by the analyse_* functions), it is extracted, rendered as a styled
    panel after the metadata box, and stripped from the body text before the
    detailed findings are rendered.
    """
    L   = VivrtaLayout
    now = datetime.now().strftime("%d %B %Y, %H:%M")

    # ── Extract executive brief sentinel ──────────────────────────────────────
    brief_text  = None
    body_text   = analysis
    brief_match = re.search(
        r"__EXECUTIVE_BRIEF__\n(.*?)\n__END_BRIEF__\n\n",
        analysis, re.DOTALL
    )
    if brief_match:
        brief_text = brief_match.group(1).strip()
        body_text  = analysis[brief_match.end():]

    pdf      = VivrtaPDF()
    renderer = VivrtaRenderer(pdf)
    pdf.set_auto_page_break(auto=True, margin=L.MARGIN_BOTTOM)
    pdf.add_page()

    renderer.cover_block(
        title    = "SAP Code Analysis Report",
        subtitle = "Vivrta.AI  ·  Powered by Claude AI",
    )
    renderer.metadata_box([
        ("File analysed", filename),
        ("Generated",     now),
        ("Prepared by",   "Vivrta.AI SAP Code Analyser"),
        ("Disclaimer",    "AI-generated. Verify with a qualified SAP consultant."),
    ])

    # ── Executive Brief panel (before detailed findings) ─────────────────────
    if brief_text:
        renderer.executive_brief_box(brief_text)

    _parse_and_render(renderer, body_text)

    return bytes(pdf.output())


# ── Plain-text export (kept as backup) ────────────────────────────────────────
def build_export_text(filename: str, analysis: str) -> str:
    """Create a plain-text export, stripping the brief sentinel and prepending it cleanly."""
    now     = datetime.now().strftime("%d %B %Y, %H:%M")
    divider = "=" * 70

    # Strip brief sentinel — include it as a clean text block at the top
    brief_block = ""
    body_text   = analysis
    brief_match = re.search(
        r"__EXECUTIVE_BRIEF__\n(.*?)\n__END_BRIEF__\n\n",
        analysis, re.DOTALL
    )
    if brief_match:
        brief_block = brief_match.group(1).strip() + "\n\n" + ("-" * 70) + "\n\n"
        body_text   = analysis[brief_match.end():]

    return (
        f"{divider}\n"
        f"  VIVRTA SYSTEMS \u2014 SAP CODE ANALYSIS REPORT\n"
        f"{divider}\n\n"
        f"  File analysed : {filename}\n"
        f"  Generated at  : {now}\n\n"
        f"{divider}\n\n"
        + brief_block
        + body_text
        + f"\n\n{divider}\n"
        f"  Powered by Vivrta.AI \u00b7 vivrta.io\n"
        f"{divider}\n"
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-wordmark">Vivrta<em>.AI</em></div>
        <div class="sb-tagline">SAP Intelligence Platform</div>
    </div>

    <div class="sb-sec">
        <div class="sb-sec-title">Analysis modes</div>
        <div class="sb-row"><span class="sb-icon">🔍</span><div><strong style="color:#c7d2fe">Single Program</strong><br>Deep-dive one ABAP file</div></div>
        <div class="sb-row"><span class="sb-icon">📦</span><div><strong style="color:#c7d2fe">Repository Bundle</strong><br>Cross-program estate intelligence</div></div>
        <div class="sb-row"><span class="sb-icon">🚀</span><div><strong style="color:#c7d2fe">S/4HANA Readiness</strong><br>Migration risk scorecard</div></div>
    </div>

    <hr class="sb-divider"/>

    <div class="sb-sec">
        <div class="sb-sec-title">Accepted file types</div>
        <div class="sb-row"><span class="sb-icon">📄</span>ABAP source (.abap, .txt)</div>
        <div class="sb-row"><span class="sb-icon">🗂️</span>Table definitions (.txt)</div>
        <div class="sb-row"><span class="sb-icon">📊</span>Config / SE16 exports (.csv)</div>
        <div class="sb-row"><span class="sb-icon">📋</span>Functional specs (.pdf, .txt)</div>
        <div class="sb-row"><span class="sb-icon">🚢</span>Transport logs (.txt)</div>
    </div>

    <hr class="sb-divider"/>

    <div class="sb-sec">
        <div class="sb-sec-title">How it works</div>
        <div class="sb-step"><div class="sb-num">1</div><div class="sb-step-txt">Choose your <strong>analysis mode</strong></div></div>
        <div class="sb-step"><div class="sb-num">2</div><div class="sb-step-txt">Upload your SAP objects</div></div>
        <div class="sb-step"><div class="sb-num">3</div><div class="sb-step-txt">Label each file type</div></div>
        <div class="sb-step"><div class="sb-num">4</div><div class="sb-step-txt">Click <strong>Run Analysis</strong></div></div>
        <div class="sb-step"><div class="sb-num">5</div><div class="sb-step-txt">Download branded <strong>PDF</strong></div></div>
    </div>

    <hr class="sb-divider"/>

    <div class="sb-sec">
        <div class="sb-sec-title">Supported SAP modules</div>
        <span class="sb-badge">FI</span>
        <span class="sb-badge">CO</span>
        <span class="sb-badge">SD</span>
        <span class="sb-badge">MM</span>
        <span class="sb-badge">FI-AA</span>
        <span class="sb-badge">ABAP</span>
        <span class="sb-badge">S/4HANA</span>
    </div>

    <hr class="sb-divider"/>

    <div class="sb-footer">
        Powered by Claude AI &nbsp;·&nbsp; © 2026 Vivrta.AI<br>
        AI-generated — review with a qualified SAP<br>consultant before any business decision.
    </div>
    """, unsafe_allow_html=True)


# ── Page header strip ─────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="ph-left">
        <div class="ph-wordmark">Vivrta<em>.AI</em></div>
        <div class="ph-div"></div>
        <div class="ph-stack">
            <div class="ph-sub">SAP Code Analyser</div>
            <div class="ph-tagline">Understand your custom ABAP in plain English</div>
        </div>
    </div>
    <div class="ph-pills">
        <span class="ph-pill">⚡ AI-powered</span>
        <span class="ph-pill">📄 PDF export</span>
        <span class="ph-pill">⚠️ Risk flagging</span>
        <span class="ph-pill">🚀 S/4HANA ready</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Mode selector ─────────────────────────────────────────────────────────────
st.markdown('<p class="sec-label">Select Analysis Mode</p>', unsafe_allow_html=True)

mode_col, desc_col = st.columns([2, 3], gap="large")

with mode_col:
    selected_mode = st.selectbox(
        label="Analysis mode",
        options=list(MODES.keys()),
        format_func=lambda k: MODES[k],
        label_visibility="collapsed",
    )

with desc_col:
    mode_sections = MODE_SECTIONS[selected_mode]
    pills_html = "".join(
        f'<span class="mode-pill">{s}</span>' for s in mode_sections
    )
    st.markdown(
        f'<div class="mode-desc">{MODE_DESCRIPTIONS[selected_mode]}</div>'
        f'<div class="mode-pills">{pills_html}</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="light">', unsafe_allow_html=True)


# ── File upload (adapts to mode) ──────────────────────────────────────────────
is_multi = selected_mode in ("bundle", "s4hana")

upload_col, info_col = st.columns([3, 2], gap="large")

with upload_col:
    st.markdown('<p class="sec-label">Upload SAP Objects</p>', unsafe_allow_html=True)

    hint_map = {
        "single": "Upload one .abap or .txt file",
        "bundle": "Upload 2–15 SAP objects (.abap, .txt, .csv, .pdf)",
        "s4hana": "Upload 1–15 ABAP programs to scan",
    }
    st.markdown(
        f'<div class="upload-zone"><div class="uz-hint">{hint_map[selected_mode]}</div></div>',
        unsafe_allow_html=True,
    )

    if is_multi:
        uploaded_files = st.file_uploader(
            label="Upload SAP objects",
            type=ACCEPTED_TYPES,
            accept_multiple_files=True,
            help="Select multiple files. You can label each one below.",
            label_visibility="collapsed",
        )
        uploaded_file = None
    else:
        uploaded_file  = st.file_uploader(
            label="Upload ABAP file",
            type=ACCEPTED_TYPES,
            help="Upload a .txt or .abap file containing your custom SAP ABAP code.",
            label_visibility="collapsed",
        )
        uploaded_files = [uploaded_file] if uploaded_file else []

    # File status display
    if uploaded_files:
        total_kb = sum(
            getattr(f, "size", 0) for f in uploaded_files if f
        ) / 1024
        count    = len([f for f in uploaded_files if f])
        st.markdown(
            f'<div class="file-ok">✅ <strong>{count} file{"s" if count != 1 else ""}</strong>'
            f' &nbsp;·&nbsp; {round(total_kb, 1)} KB total ready</div>',
            unsafe_allow_html=True,
        )

with info_col:
    st.markdown('<p class="sec-label">Report sections</p>', unsafe_allow_html=True)
    items_html = "".join(
        f'<div class="rp-item"><div class="rp-dot"></div>'
        f'<div class="rp-text">{s}</div></div>'
        for s in MODE_SECTIONS[selected_mode]
    )
    st.markdown(
        f'<div class="rp-card">{items_html}</div>',
        unsafe_allow_html=True,
    )


# ── File labelling for multi-file modes ───────────────────────────────────────
FILE_LABEL_OPTIONS = [
    "ABAP Program",
    "Function Module",
    "Table Definition",
    "Configuration Data (SE16/SM30)",
    "Transport Log",
    "Functional Specification",
    "Org Structure / SPRO Export",
    "Other SAP Object",
]

file_labels = {}
if is_multi and uploaded_files:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec-label">Label each file (optional but improves accuracy)</p>', unsafe_allow_html=True)
    label_cols = st.columns(min(len(uploaded_files), 3))
    for i, uf in enumerate(uploaded_files):
        if uf is None:
            continue
        col = label_cols[i % len(label_cols)]
        with col:
            file_labels[uf.name] = st.selectbox(
                label=uf.name,
                options=FILE_LABEL_OPTIONS,
                key=f"label_{i}_{uf.name}",
            )

st.markdown("<br>", unsafe_allow_html=True)


# ── Analyse button ─────────────────────────────────────────────────────────────
has_files = bool(uploaded_files and any(f for f in uploaded_files if f))

analyse_clicked = st.button(
    f"▶  Run {MODES[selected_mode].split('  ')[1]}" if has_files else "Upload files to begin",
    disabled=not has_files,
)


# ── Session state ──────────────────────────────────────────────────────────────
for key in ("analysis_result", "analysed_filename", "analysis_mode"):
    if key not in st.session_state:
        st.session_state[key] = None


# ── Run analysis ───────────────────────────────────────────────────────────────
if analyse_clicked and has_files:

    # Build the file list for multi-mode calls
    file_list = []
    for uf in uploaded_files:
        if uf is None:
            continue
        content, ftype = extract_text_from_file(uf)
        file_list.append({
            "name":    uf.name,
            "type":    ftype,
            "label":   file_labels.get(uf.name, ""),
            "content": content,
        })

    if not any(f["content"].strip() for f in file_list):
        st.warning("All uploaded files appear to be empty.")
    else:
        spinner_msgs = {
            "single": "Analysing your SAP code… usually 15–30 seconds.",
            "bundle": f"Analysing {len(file_list)} SAP objects… usually 30–60 seconds.",
            "s4hana": f"Running S/4HANA readiness scan on {len(file_list)} program(s)… usually 30–60 seconds.",
        }
        with st.spinner(spinner_msgs[selected_mode]):
            try:
                if selected_mode == "single":
                    result = analyse_single(file_list[0]["content"])
                    fname  = file_list[0]["name"]
                elif selected_mode == "bundle":
                    result = analyse_bundle(file_list)
                    fname  = f"Bundle ({len(file_list)} objects)"
                else:
                    result = analyse_s4hana(file_list)
                    fname  = f"S4HANA Scan ({len(file_list)} programs)"

                st.session_state["analysis_result"] = result
                st.session_state["analysed_filename"] = fname
                st.session_state["analysis_mode"]    = selected_mode

            except EnvironmentError as e:
                st.error(f"⚠️ Configuration error: {e}")
            except anthropic.AuthenticationError:
                st.error("⚠️ Authentication failed. Check ANTHROPIC_API_KEY in secrets.toml.")
            except anthropic.RateLimitError:
                st.error("⚠️ Rate limit reached. Please wait a moment and try again.")
            except Exception as e:
                st.error(f"⚠️ An unexpected error occurred: {e}")


# ── Result display ─────────────────────────────────────────────────────────────
if st.session_state["analysis_result"]:
    analysis = st.session_state["analysis_result"]
    fname    = st.session_state["analysed_filename"]
    mode     = st.session_state["analysis_mode"] or "single"

    # Extract brief sentinel for on-screen display
    display_brief = None
    display_body  = analysis
    _brief_m = re.search(
        r"__EXECUTIVE_BRIEF__\n(.*?)\n__END_BRIEF__\n\n",
        analysis, re.DOTALL
    )
    if _brief_m:
        display_brief = _brief_m.group(1).strip()
        display_body  = analysis[_brief_m.end():]

    mode_icon = {"single": "📋", "bundle": "📦", "s4hana": "🚀"}.get(mode, "📋")
    mode_label = MODES.get(mode, "Analysis Report").split("  ", 1)[-1]

    st.markdown('<hr class="light">', unsafe_allow_html=True)

    st.markdown(
        f'''<div class="result-hdr">
            <span class="rh-icon">{mode_icon}</span>
            <span class="rh-title">{mode_label}</span>
            <span class="rh-file">{fname}</span>
        </div>''',
        unsafe_allow_html=True,
    )

    # Executive Brief callout (on-screen)
    if display_brief:
        brief_html = display_brief.replace(chr(10), "<br>")
        st.markdown(
            f'<div style="background:#f0f4ff;border-left:4px solid #4f46e5;'
            f'border-radius:0 8px 8px 0;padding:1rem 1.3rem;margin-bottom:1rem;'
            f'font-size:0.88rem;color:#1e1b4b;">'
            f'<strong style="font-size:0.72rem;letter-spacing:0.08em;'
            f'text-transform:uppercase;color:#6366f1;">Executive Brief</strong><br><br>'
            f'{brief_html}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="result-body">{display_body.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', fname)[:40]
    ts        = datetime.now().strftime("%Y%m%d_%H%M")
    pdf_fname = f"vivrta_{mode}_{safe_stem}_{ts}.pdf"
    txt_fname = f"vivrta_{mode}_{safe_stem}_{ts}.txt"

    st.markdown('<p class="sec-label">Export report</p>', unsafe_allow_html=True)
    dl_col1, dl_col2, _ = st.columns([1.2, 1, 1.8], gap="small")

    with dl_col1:
        try:
            pdf_bytes_out = build_pdf(fname, analysis)
            st.download_button(
                label="⬇  Download PDF Report",
                data=pdf_bytes_out,
                file_name=pdf_fname,
                mime="application/pdf",
            )
        except Exception as pdf_err:
            st.warning(f"PDF generation failed: {pdf_err}")

    with dl_col2:
        st.download_button(
            label="⬇  Export as .txt",
            data=build_export_text(fname, analysis).encode("utf-8"),
            file_name=txt_fname,
            mime="text/plain",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.73rem;color:#9ca3af;">'
        "Analysis by Vivrta.AI · Review with a qualified SAP consultant before any business decision."
        '</p>',
        unsafe_allow_html=True,
    )
