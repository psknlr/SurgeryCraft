# IMPF Surgery Hospital · standards matrix · 规范对照

For every design topic, this table sets the Singaporean, European, US and Japanese requirements
side by side, then gives the **target IMPF uses: the strictest of them**. Where one jurisdiction is
silent or its figure could not be verified, the cell says so rather than guess. The targets are
written into the room and equipment descriptions the learner reads in game. Where a rule is a
procedure, it is enforced in game as an operation with preconditions; see
[INTERACTIONS.md](INTERACTIONS.md).

> **Design intent, not engineering.** ClinicalCraft does not simulate airflow, pressure,
> temperature, radiation or electrical systems. The figures were gathered from official
> publications where available and from secondary sources (marked †). Standards were not read
> in full text. Verify the current edition and the local code before using any figure for a
> real building or device.

## 1. The room

| topic | Singapore | Europe | USA | Japan | **IMPF target (strictest)** |
|---|---|---|---|---|---|
| Air changes, conventional OR | MOH *IPC Specifications for New Healthcare Buildings* (rev. 2024) §3.3.3 sets OT air-change rates (figure not verified); airflow direction and rates tested at building acceptance | UK HTM 03-01 (2021): **25 ACH** design for a conventional theatre†; verification ≥ 18 ACH | ASHRAE 170-2021: ≥ 20 total, ≥ 4 outdoor ACH | MHLW (2007, after HEAS-02): general OR ≥ 15 ACH incl. ≥ 3 outdoor | **≥ 25 total and ≥ 4 outdoor ACH** in every OR |
| Ultra-clean (implant) OR | MOH IPC Specifications ch. 3 (figures not verified) | HTM 03-01: UCV ≤ 10 CFU/m³ in use; Sweden SIS/TS 39:2025: ≤ 10 CFU/m³, **design mean ≤ 5**†; France NF S 90-351: zone 4 = **ISO 5**†; Germany DIN 1946-4:2018 class Ia: **TAV supply field ≥ 3.2 × 3.2 m**†; Switzerland SWKI VA105-01 class 1a: protected area covers the field **and the opened instrument tables**† | ASHRAE 170: Group E non-aspirating diffusers in the primary supply array, array ≥ 12 in beyond the table† | HEAS-02-2022: Class I *ultra-clean OR* (超清浄手術室), HEPA ≥ 99.97 % | **ISO 5 at the operating zone; ≤ 10 CFU/m³ in use, design mean ≤ 5; a 3.2 × 3.2 m unidirectional zone over the table and the opened instrument tables; non-aspirating supply array** (ORs 1, 3, 4) |
| Pressure | MOH: airflow direction verified at acceptance | NF S 90-351: **15 ± 5 Pa** between zones†; (China GB 50333: ≥ 5 and < 20 Pa between classes) | ASHRAE 170: positive, ≥ 2.5 Pa | positive to the corridor, doors kept closed | **OR positive; 15 ± 5 Pa between zones**; the isolation OR switchable negative behind an interlocked anteroom |
| Temperature · humidity | — | AfPP (UK): 35–60 % RH in use | ASHRAE 170: 20–24 °C, 20–60 % RH | — | **20–24 °C, 35–60 % RH** |
| Filtration | — | terminal HEPA H13/H14 | MERV-16 final filters (ASHRAE 170) | Class I HEPA ≥ 99.97 %; Class II ≥ 98 % | **MERV-16 then terminal HEPA ≥ 99.97 %** |
| Room size | — | HBN 26 room sizes† | FGI: 37.16 m² clear general OR, **55.74 m² (600 ft²) with ≥ 6.1 m minimum dimension** for large-equipment ORs | — | **≥ 55.74 m² clear in every OR** (9 × 9 m ORs ≈ 75 m² clear, the hybrid OR ≈ 92 m²) |
| Electrical | — | IEC 60364-7-710: Group 2 medical IT system with insulation monitoring | NFPA 99 / NEC 517.19: **≥ 36 receptacles** (≥ 12 on normal or another ATS); wet procedure location → isolated power or GFCI | JIS T 1022:2023: non-grounded (IT) wiring, isolation transformer ≤ 7.5 kVA, **uninterruptible supply for the surgical lights**, general emergency supply ≤ 40 s | **≥ 36 receptacles on medical IT systems with insulation monitoring; uninterruptible supply for the surgical lights** |
| Medical gases | — | ISO 7396-1:2016+A1:2017; HTM 02-01 | FGI / NFPA 99: O₂, vacuum, medical air, WAGD, instrument air | JIS T 7101:2020: O₂, N₂O, air **400 ± 40 kPa**; terminal flow **O₂ ≥ 60 NL/min**, N₂O 40, AGSS 30 | **O₂, medical air, N₂O, vacuum, AGSS/WAGD, instrument air at 400 ± 40 kPa; O₂ ≥ 60 NL/min per terminal** |
| Healthcare occupancy (fire) | SCDF Fire Code 2023: Purpose Group III (cl. 9.3) | — | — | — | Purpose Group III planning: compartmented department, escape stairs |
| Traffic and doors | — | — | AORN: restricted / semi-restricted / unrestricted zones; limit door openings | JAOM 2019: doors closed, avoid crowding | **three-zone traffic enforced by access zones; doors closed during a case** |

## 2. The team's practice

| topic | Singapore | Europe | USA | Japan | **IMPF target · in game** |
|---|---|---|---|---|---|
| Surgical safety checklist | SGH adopted the WHO checklist in 2009 | WHO checklist widely mandated | Universal Protocol / WHO | WHO checklist | **WHO Sign in → Time out → Sign out**; no incision before the time-out, no sign-out before the counts reconcile (gated) |
| Counts | — | — | AORN: **RF / barcode count adjunct, used even when the counts reconcile** | JAOM 2019: counts **before incision, before cavity closure, before skin closure and at every staff hand-over**; a discrepancy → report, search, X-ray | **all four JAOM count points, and the final count only after a clear RF scan** (gated) |
| Surgical smoke | — | — | AORN: **evacuate and filter all surgical smoke** | — | **no electrosurgical output without the smoke evacuator running** (gated) |
| Infection prevention | MOH National IPC Guidelines for Acute Healthcare Facilities (2017), National IPC Standard (2022) | EN 12791 surgical hand rub | AORN; CDC | JAOM | **hand hygiene, sterile gown and gloves before any instrument touches the patient** (gated) |
| Anaesthesia monitoring | — | — | ASA standards | **JSA 2019: SpO₂, capnography under GA, continuous ECG, NIBP ≤ 5 min, temperature, neuromuscular monitoring when NMBs are used** | the JSA set: the strictest list |
| Radiation protection | — | IEC 61331-3: aprons ≥ 0.25 / 0.35 mm Pb | NCRP 147 (shielding) | — | **0.5 mm Pb apron on and the ceiling shield in place before an injection under fluoroscopy** (gated) |
| Reprocessing | — | EN 285:2015+A1:2021, ISO 17665:2024, ISO 15883-1:2024, EN 868-8:2018, ISO 11140-1 | AAMI ST79 | — | **washer-disinfector cycle complete and a released steriliser load before a used set or instrument is sterile again** (gated) |

## 3. Instruments, apparel and devices

| item | requirement IMPF writes into the item | standards |
|---|---|---|
| Stainless instruments | martensitic / austenitic stainless steel; autoclave, corrosion and thermal resistance verified | ISO 7153-1:2016; ASTM F899-23; ISO 13402:2025 |
| Scalpels | handle-to-blade fit; retractable safety shield; sharps passed through a neutral zone | ISO 7740:1985; AORN sharps safety |
| Scissors · articulated instruments | cutting test; ratchet and joint requirements | ISO 7741:1986; ISO 7151:2024 |
| Traceability | **UDI direct-marked on every reusable instrument** (EU class I reusables by 26 May 2027) | EU MDR Annex VI Part C 4.10; 21 CFR 801.45 |
| Sterile packaging | rigid containers with filters and seals; class 5 integrator inside | EN 868-8:2018; ISO 11607-1:2019+A1:2023; ISO 11140-1 |
| Surgical gowns | **AAMI Level 4** critical zones; EN high performance | AAMI PB70:2022; EN 13795-1:2019 |
| Surgical gloves | powder-free, double-gloving with a perforation indicator | EN 455 series; ASTM D3577 |
| Masks · respirators | Type IIR / ASTM Level 3; FFP3 / N95 in the isolation OR | EN 14683:2019; ASTM F2100; EN 149; NIOSH N95 |
| Lead aprons | 0.5 mm Pb equivalent, wrap-around | IEC 61331-3:2014 |
| Electrosurgical units | return-electrode contact-quality monitoring | IEC 60601-2-2:2017+A1:2023 |
| Surgical lights | 40 000–160 000 lx central illuminance, Ra 85–100 | IEC 60601-2-41:2021 |
| Operating tables | — | IEC 60601-2-46:2023 |
| Interventional X-ray | — | IEC 60601-2-43:2022 |
| Anaesthesia workstations · gas monitors | — | ISO 80601-2-13:2022; ISO 80601-2-55:2018+A1:2023 |
| Patient monitors · pulse oximeters | — | IEC 80601-2-49:2018+A1:2024; ISO 80601-2-61 |
| Infusion pumps · patient warming | — | IEC 60601-2-24:2012; IEC 60601-2-35:2020+A1:2023 |
| Medical gas terminal units | — | ISO 9170-1:2017; ISO 7396-1 |
| Washer-disinfectors · sterilisers | A0 ≥ 3000 thermal disinfection; Bowie-Dick test daily; parametric and indicator release | ISO 15883-1:2024; EN 285:2015+A1:2021; EN 13060:2025; ISO 17665:2024 |

## Sources

Official publications where marked, otherwise secondary summaries (verify against the current
editions):

* Singapore — MOH, *Infection Prevention and Control Specifications for New Healthcare
  Buildings* (revised 2024):
  [PDF](https://isomer-user-content.by.gov.sg/18/9fee2773-9a8f-43fc-af6d-4abba3a340e1/infection-prevention-and-control-specifications-for-new-buildings-revised-2024_final.pdf);
  MOH, [IPC guidelines and standards](https://hpp.moh.gov.sg/guidelines/infection-prevention-and-control-guidelines-and-standards/);
  CDA, [IPC guidelines and standards](https://www.cda.gov.sg/professionals/ipc-guidelines-and-standards/);
  MOH, [airflow and ventilation analysis for hospitals](https://www.moh.gov.sg/newsroom/airflow-and-ventilation-analysis-for-existing-and-new-buildings-and-hospitals-to-minimise-transmission-of-covid-19-and-emerging-pathogens/);
  SCDF, [Fire Code 2023 cl. 9.3 Purpose Group III](https://www.scdf.gov.sg/fire-safety-services-listing/fire-code-2023/table-of-content/chapter-9-additional-requirements-for-each-purpose-group/clause-9.3-purpose-group-iii-occupancy);
  SingHealth, [the WHO checklist at SGH](https://www.healthxchange.sg/news/learning-from-failures-to-transform-our-surgical-safety-checklist);
  [conventional theatre ≥ 25 ACH (Singapore study)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8047336/).
* Japan — HEAJ, [HEAS-02-2022](https://www.heaj.org/book/book.html);
  [hospital air cleanliness classes (JSICM)](https://www.jsicm.org/pdf/Hospital_air_cleanliness_1.pdf);
  [MHLW 2007 (after HEAS-02-2004)](https://www.mhlw.go.jp/shingi/2007/03/dl/s0315-4f55.pdf);
  JAOM, [手術医療の実践ガイドライン 改訂第三版](http://jaom.kenkyuukai.jp/);
  JSA, [モニター指針 (2019)](https://anesth.or.jp/files/pdf/monitor3_20190509.pdf);
  [JIS T 7101:2020](https://jis.eomec.com/jist71012020); JIS T 1022:2023.
* Europe — HTM 03-01 (2021); SIS/TS 39:2025; NF S 90-351:2013; DIN 1946-4:2018-09 + A1:2025-11;
  SWKI VA105-01; CEN/TS 16244:2018; IEC 60364-7-710
  ([reinraum.de on DIN 1946-4](https://www.reinraum.de/en/news/how-much-din-en-iso-14644ff-is-currently-and-in-the-future-incorporated-into-an-operating-room-in-a-hospital-according-to-din-1946-part-4.html),
  [Normec on room classes](https://healthcare.normecgroup.com/news/which-operating-room-belongs-to-which-room-class),
  [Halton Vita OR](https://www.halton.com/app/uploads/2020/08/Halton_Vita_OR_brochure_en.pdf)).
* USA — ASHRAE 170-2021 (and 170-2025); FGI Guidelines; NFPA 99 / NEC 517.19
  ([EC&M](https://www.ecmweb.com/nec/no-room-error)); AORN guidelines (traffic, sharps safety,
  retained surgical items, surgical smoke).
* Devices and apparel — the ISO / IEC / ASTM / AAMI / EN numbers above, at the editions shown.
