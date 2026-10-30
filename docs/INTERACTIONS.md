# IMPF Surgery Hospital · interactions · 人、器械与设备的交互

In IMPF, people, instruments and devices act on each other through ClinicalCraft's world model:
every act is a world operation with an authority class, preconditions, a reach and a duration. The
learner, an AI agent and a colleague all go through the same action bus. Nothing in this pack is
code: instruments, devices and their rules are catalog data (`behavior` state machines and world
predicates), the team is facility data, and the workflows are declarative skills.

The pack needs the ClinicalCraft **hands round** ([psknlr/ClinicalCraft#7](https://github.com/psknlr/ClinicalCraft/pull/7)), which added these general
mechanics:

| mechanic | what it does |
|---|---|
| `hand_over {to}` | passes a carried item to a person within arm's reach (1.5 m, line of sight) who has a free hand |
| worn items | an equipped item (gown, gloves, lead apron) leaves the hands free; at most 2 items are *in* hand |
| `nearbyState` | an operation needs a device of a given type nearby to be in a state ("the generator fires only with the smoke evacuator running"); a refusal names the device and points at it |
| carried lifecycle | an instrument in hand is both `held` and in its own state (`sterile` → `in-use` → `used`); only whoever holds it can use it |
| "pass me …" | said to any colleague, in English or Chinese, including the bare call at the table ("Scalpel.", "纱布"): they pick it up, come over and hand it to you |
| hands in the browser | a handheld item's panel offers Pick up / Put down / Equip / Hand to …; *In your hands* (inventory, key 7) lists what you carry |
| `find_objects {room: "here"}` | skills find *this* OR's checklist, count board and wand, not the neighbouring room's |

## The team · 手术团队

Each OR has its own team at their posts (40 staff in the hospital). The learner operates; the
team passes, counts and anaesthetises.

| OR | scrub nurse · 洗手护士 | circulating nurse · 巡回护士 | anaesthetist · 麻醉医生 |
|---|---|---|---|
| OR 1 · hybrid | Nurse Müller | Nurse Pillai | Dr Sato |
| OR 2 · robotic | Nurse Tan | Nurse Fatimah | Dr Andersen |
| OR 3 · cardiac & transplant | Nurse Yamamoto | Nurse Laurent | Dr Kumar |
| OR 4 · arthroplasty & neuro | Nurse Ng | Nurse Rossi | Dr Schmidt |
| OR 5 · general & colorectal MIS | Nurse Wong | Nurse O'Connor | Dr Suzuki |
| OR 6 · urology, gynaecology & ENT | Nurse Rahman | Nurse van den Berg | Dr Lee |
| OR 7 · emergency & obstetric | Nurse Lim | Nurse Aisyah | Dr Tanaka |
| OR 8 · isolation | Nurse Takahashi | Nurse García | Dr Menon |
| simulation OR (ground floor) | sim faculty nurse | sim faculty nurse | sim faculty anaesthetist |

Talk to them by name (`@Nurse Lim`, or pick them in the conversation). Besides "pass me …" they do
what ClinicalCraft colleagues do: monitor, ECG, IV access, fetch, give within scope, come, go back,
show the way, where is ….

## Instruments and wearables · 器械与穿戴

Every OR's **sterile set-up table** is laid out to the tray list: the instrument set, counted RFID
swabs, gloves and gown at the back, the first instruments along the front edge. All are handheld
(`portable: "handheld"`), each with its own lifecycle.

| item | states | operations (who) | preconditions |
|---|---|---|---|
| Safety scalpel · 安全手术刀 | sterile → in use → used → (CSSD) sterile | incise (surgeon), finish, reprocess | **in hand; scrubbed (hand hygiene), gowned and gloved; at the patient; the WHO time-out done (checklist within 7 m); the room in operating mode (control panel within 7 m)** |
| Needle holder · 持针器 | same | load needle (scrub team), suture (surgeon), finish, reprocess | in hand, scrubbed / gowned / gloved; suture at the patient |
| Tissue forceps · 组织镊, dissecting scissors · 解剖剪, artery forceps · 止血钳 | same | grasp / dissect / clamp, finish, reprocess | in hand, scrubbed / gowned / gloved, at the patient |
| ESU pencil · 电刀笔 (single use) | sterile → in use → discarded | cut / coagulate (surgeon), discard | in hand, scrubbed / gowned / gloved, at the patient; **generator ready and smoke evacuator running within 6 m** |
| RFID swabs · RFID 纱布 | counted → in use → retrieved | pack / mop, retrieve and count | in hand, scrubbed / gowned / gloved |
| Instrument set · 硬质无菌器械盒 | sealed → verified → open → used → (CSSD) sealed | check seal, indicators and expiry; open aseptically; close and send to the CSSD; reprocess | open: hand hygiene; reprocess: **washer-disinfector cycle complete and a released steriliser load within 12 m** — the set has to travel down to the CSSD |
| RF wand · RF 检测棒 | ready → clear | scan the patient (circulating nurse or surgeon), reset | in hand, at the patient |
| Sterile gown · 无菌手术衣, sterile gloves · 无菌手套 | worn | Equip / Take off | — (the instruments require them worn) |
| Lead apron · 铅衣 (hybrid OR) | worn | Equip / Take off | — (the contrast injector requires it worn) |

Reusable instruments are **reprocessed**, not reset: *Reprocess in the CSSD* is refused until
the instrument is in the CSSD's inspection & packing room with a completed washer-disinfector
cycle and a released steriliser load nearby.

## Devices · 设备

| device | states | operations | gates |
|---|---|---|---|
| WHO checklist board · WHO 核查板 | pending → signed in → timed out → signed out | Sign in · Time out · Sign out · next case | Time out needs the **baseline count**; Sign out needs the **reconciled final count** |
| Surgical count board · 清点板 | not started → baseline → cavity → closing → reconciled (· discrepancy) | baseline count, hand-over count, cavity count, closing count, final count, report a discrepancy, resolve, next case | final count needs a **clear RF scan** (wand within 6 m); counting from the board (2.5 m) |
| Smoke evacuator · 烟雾排除器 | off ↔ running | switch on / off | — |
| Surgical pendant (generator / insufflator) · 外科吊塔 | standby → monitored → ready | place the return electrode and confirm REM/CQM (at the patient), enable output, standby, remove the electrode | enable output needs the **smoke evacuator running** within 4 m |
| OR control panel · 环境控制面板 | operating ↔ set-back | check the room, set-back, operating mode (15 min) | the scalpel needs **operating mode** |
| Laparoscopy tower · 腹腔镜系统 | off → on → balanced → insufflating | power on, white balance, start / stop insufflation, power off | start insufflation at the patient (surgeon) |
| Lead shield · 铅屏风 (hybrid) | stowed ↔ in place | position, stow | — |
| Contrast injector · 高压注射器 (hybrid) | empty → loaded → armed → empty | load (aseptic), purge and arm, inject | load: hand hygiene; inject: **lead apron worn and the shield in place** within 4 m |
| Washer-disinfector · 清洗消毒器 (CSSD) | idle → loaded → complete | load, run the cycle (10 min), unload | — |
| Steam steriliser · 压力蒸汽灭菌器 (CSSD) | idle → tested → cycle complete → released | Bowie-Dick test, 134 °C cycle (15 min), release, unload | — |

Gates are scoped so that a device in the neighbouring room never satisfies them: tools/orflow.test.ts
checks every gate in every OR resolves only to its own room's device.

## A case, start to finish

1. Change, cap and mask; **wash your hands** at the scrub bay's trough (valid 30 simulated min).
2. At the set-up table: **pick up and equip** the gown and gloves (or ask: "Pass me the gown").
3. WHO **Sign in** at the checklist board; the circulating nurse does the **baseline count**;
   **Time out**.
4. "Scalpel." — the scrub nurse picks it up, comes over and hands it to you; **incise**.
5. Energy: the electrode on and monitored, the **smoke evacuator** on, generator output enabled;
   **cut** with the pencil.
6. "Needle holder, please" → **load the needle**, **suture**.
7. **Cavity count**, **closing count**; the circulator **scans the patient** with the RF wand;
   **final count**; **Sign out**.
8. **Finish** with the instruments, close the set; take them down to the **CSSD**: washer cycle,
   steriliser test, cycle and release; **reprocess** — sterile again for the next case.

Every refusal along the way is the world's own words with "Go there" or the act to do first, for
example *"Clean your hands at a sink first."* with the button *Wash your hands at "Twin scrub
trough"*, or *"Incise (skin incision) needs the nearby "WHO Surgical Safety Checklist board" to be
timed out (before incision) or signed out (before leaving) (it is pending)."* with the way to the
board.

## Skills · 技能

`.clinicalcraft/skills/` holds three declarative workflows (`clinicalcraft/skill@1`). They run
through the caller's own tool path and succeed only when their postconditions hold in the world:

| skill | steps | postcondition |
|---|---|---|
| `impf_surgical_time_out` | to the patient's OR → find this room's checklist and board → Sign in → baseline count → Time out | the checklist timed out |
| `impf_closing_counts` | to the patient's OR → cavity and closing counts → take the RF wand → scan the patient → final count → Sign out → put the wand down | board reconciled and checklist signed out |
| `impf_cssd_cycle` | the nearest washer-disinfector: load, cycle; the nearest steriliser: Bowie-Dick, cycle, release | washer complete, load released |

Project skills load only from a **trusted** project: from a ClinicalCraft checkout, run
`npm run cc -- trust --cwd ../SurgeryCraft` once, then start sessions with `--cwd ../SurgeryCraft`
(or copy the files to `~/.clinicalcraft/skills/`). They are then `/skill
project:impf_surgical_time_out` and so on, and the clinician agent can run them.

## Words · 说法

| to a colleague | understood as |
|---|---|
| "Pass me the scalpel", "Could you hand me a swab?", "Give me the Mayo scissors" | pass |
| "Scalpel.", "Needle holder, please" | pass (only when a handheld item is called that; otherwise it is talk) |
| "把手术刀递给我", "请递一下纱布", "给我一把持针器", "组织钳。", "电刀，谢谢" | 递给我 |
| "Bring the ESU pencil" | a fetch that names a handheld item is passed the same way |
| "Give me a minute", "Yes please", "谢谢" | talk |
