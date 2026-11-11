# Public surgical video datasets · 公开手术视频数据集

Thoracoscopic and laparoscopic operations have been recorded and annotated for machine learning,
and the question comes up of what SurgeryCraft should take from those datasets. This page records
what each one is, **as its own source states it** (checked on 2026-11-11), under which terms it
may be used, and what this pack does with it — which, today, is nothing beyond its vocabulary.

> 胸腔镜与腹腔镜手术已有多个公开的标注视频数据集。本页逐一记录它们的内容、规模和**许可条件**
> （均以数据集自己的主页、仓库或论文为准，核对日期 2026-11-11），以及本内容包目前怎样使用它们：
> 只借用其中的术语（如手术阶段的名称），不下载、不收录任何视频、图像或标注。多数数据集只许
> 非商业使用，有的还要申请或签署数据使用协议——“能公开看到”不等于“可以拿来训练或再分发”。

**Nothing from these datasets is in this repository**: no video, no frame, no annotation file, and
no tool here downloads one. The pack's own `dataset/` folder is something else — published case
reports (CMCR), the source of its clinical cases.

## Thoracoscopy

| dataset | what it is | publication | access and licence | where |
|---|---|---|---|---|
| **LungRes80** | 80 thoracoscopic (VATS) segmentectomies, 269,806 frames annotated with 7 surgical phases; split 50 / 15 / 15 | Guo … Heng (CUHK), *Medical Image Analysis* 114:104237, 2026, [doi:10.1016/j.media.2026.104237](https://doi.org/10.1016/j.media.2026.104237) | application form with an institutional e-mail, academic non-commercial use; the dataset is offered under CC BY-NC-ND 4.0 with no redistribution or derivatives without written permission (the repository's code licence is CC BY-NC 4.0) | [github.com/RascalGdd/LungRes80](https://github.com/RascalGdd/LungRes80) |
| **TMVP-SurgVideo** | 57 long videos of thoracoscopic mitral valve repair, over 429,000 annotated frames; phases and instruments, recognition and anticipation | Lan, Si, Yan, Li (HKUST), *Medical Image Analysis* 105:103724, 2025, [doi:10.1016/j.media.2025.103724](https://doi.org/10.1016/j.media.2025.103724) | linked from the code repository; **no data licence stated** | [github.com/xmed-lab/SurgFormer](https://github.com/xmed-lab/SurgFormer) |
| **LungSurg** (an AI system and its data) | 222 VATS lobectomy videos from 8 centres, about 1.5 million frames at 1 fps, 14 phases, 32,027 annotated structures (anatomy and instruments) | Liang … He (Guangzhou Medical University), *MedComm* 7(2):e70613, 2026, [doi:10.1002/mco2.70613](https://doi.org/10.1002/mco2.70613) | part of the annotated validation set is shared; the full videos on request under a data-use agreement; **no data licence stated** | [PMC12820416](https://pmc.ncbi.nlm.nih.gov/articles/PMC12820416/) |

LungRes80's seven phases, as its evaluation code names them — *Fissure Dissection*, *Vein
Dissection*, *Artery Dissection*, *Bronchus Dissection*, *Lymph Node Dissection*, *Lung Segment
Resection*, *Other Operations* — name the same structures that the steps of the pack's
thoracoscopy training station divide or take: the vein, the artery, the bronchus, the fissure,
the lymph nodes ([THORACOSCOPY.md](THORACOSCOPY.md)). The station's steps were written from the
surgical technique, not from the dataset; the shared vocabulary is what would let a recognised
phase be shown beside a rehearsed step later.

## Laparoscopy

| dataset | what it is | publication | access and licence | where |
|---|---|---|---|---|
| **Cholec80** | 80 cholecystectomy videos by 13 surgeons; phases (25 fps) and tool presence (1 fps) | Twinanda et al. (CAMMA, Strasbourg), *IEEE TMI* 36(1):86–97, 2017, [doi:10.1109/TMI.2016.2593957](https://doi.org/10.1109/TMI.2016.2593957) | direct download; CC BY-NC-SA 4.0 | [camma.unistra.fr/datasets](https://camma.unistra.fr/datasets/) |
| **CholecT50** | 50 videos, 100.9 thousand frames; 100 instrument–verb–target triplet classes, phases; boxes on 5 videos | Nwoye et al. (CAMMA), *Medical Image Analysis* 78:102433, 2022, [doi:10.1016/j.media.2022.102433](https://doi.org/10.1016/j.media.2022.102433) | request form; CC BY-NC-SA 4.0 | [github.com/CAMMA-public/cholect50](https://github.com/CAMMA-public/cholect50) |
| **Endoscapes2023** | clips of the dissection phase from 201 videos (58,813 frames); critical view of safety on 11,090 frames, boxes on 1,933, segmentation masks on 493 frames from 50 videos | Mascagni et al. (CAMMA), *Scientific Data* 12:331, 2025, [doi:10.1038/s41597-025-04642-4](https://doi.org/10.1038/s41597-025-04642-4) | direct download, CC BY-NC-SA 4.0 (a PhysioNet copy needs a signed agreement) | [github.com/CAMMA-public/Endoscapes](https://github.com/CAMMA-public/Endoscapes) |
| **MultiBypass140** | 140 gastric bypass videos (Strasbourg 70, Bern 70); 12 phases, 46 steps; intra-operative adverse events (5 categories, severity 0–5) added in 2025 as a separate release | Lavanchy et al. (CAMMA), *IJCARS* 19:2249–2257, 2024, [doi:10.1007/s11548-024-03166-3](https://doi.org/10.1007/s11548-024-03166-3); adverse events: Bose et al., arXiv:2504.16749 | direct download; CC BY-NC-SA 4.0 | [github.com/CAMMA-public/MultiBypass140](https://github.com/CAMMA-public/MultiBypass140) |
| **CholecTrack20** | 20 videos, 35 thousand frames, 65 thousand tool instances; boxes, class, three track identities, operator, phase | Nwoye et al. (CAMMA), CVPR 2025, arXiv:2312.07352 | data-use agreement and a request form for an access key; CC BY-NC-SA 4.0 | [github.com/CAMMA-public/cholectrack20](https://github.com/CAMMA-public/cholectrack20) |
| **HeiChole** | 33 videos from 3 centres (24 of them downloadable for training); 7 phases, 4 actions, 21 instruments, 5 skill dimensions | Wagner et al. (Heidelberg), *Medical Image Analysis* 86:102770, 2023, [doi:10.1016/j.media.2023.102770](https://doi.org/10.1016/j.media.2023.102770) | Synapse account and registration; CC BY-NC-SA | [synapse.org syn18824884](https://www.synapse.org/Synapse:syn18824884) |
| **PhaKIR** | 8 complete videos from 3 hospitals; phases on 485,875 frames, instrument keypoints and instance masks on 19,435 frames each | Rueckert et al. (OTH Regensburg), *Data in Brief* 68:113147, 2026, [doi:10.1016/j.dib.2026.113147](https://doi.org/10.1016/j.dib.2026.113147) | restricted on Zenodo (login and a request form); CC BY-NC-SA 4.0 | [zenodo.org/records/15740620](https://zenodo.org/records/15740620) |
| **CholecSeg8k** | 8,080 frames from 17 Cholec80 clips; pixel masks in 13 classes | Hong et al., arXiv:2012.12453, 2020 | Kaggle; CC BY-NC-SA 4.0 as its paper states | [kaggle.com/datasets/newslab/cholecseg8k](https://www.kaggle.com/datasets/newslab/cholecseg8k) |
| **EndoVis 2017** (robotic instrument segmentation) | 10 porcine da Vinci Xi sequences; masks of instrument parts and types | Allan et al., arXiv:1902.06426 | challenge account and joining; **no licence stated** (the challenge's rules speak of non-commercial use) | [grand-challenge.org](https://endovissub2017-roboticinstrumentsegmentation.grand-challenge.org/) |

## Three-dimensional reconstruction

| dataset | what it is | publication | access and licence | where |
|---|---|---|---|---|
| **D4D** (Dresden Dataset for 4D Reconstruction) | over 300,000 frames and 369 point clouds across 98 curated recordings of **porcine cadaver** abdominal tissue: stereo images, stereo depth, instrument masks, camera poses; about 480 GB | Docea … Speidel (NCT/UCC Dresden), *Scientific Data* 13:1334, 2026, [doi:10.1038/s41597-026-08289-7](https://doi.org/10.1038/s41597-026-08289-7) | open download; CC BY 4.0 | [doi:10.25532/OPARA-1033](https://doi.org/10.25532/OPARA-1033) |

## What follows for this pack

* **Licences decide first.** All but one of these are non-commercial, several forbid
  redistribution or derivatives, three state no licence at all, and some are given only on
  application or under a signed agreement. The pack's own content is MIT (models) and plain
  data; nothing with those terms can be folded into it. Anyone who trains on these datasets does
  so under their own agreement with each provider, outside this repository.
* **Patients.** They are recordings of real operations. Even where frames are public, a case in
  this pack never borrows a patient from a video: a case states only what its own source records
  (ClinicalCraft's grounding rule).
* **Annotations are not actions.** A phase label says what part of an operation a frame belongs
  to; an instrument–verb–target triplet says what was seen. Neither is geometry, tissue state or
  a rule. The pack's operable anatomy (Case 126) is a state model written and checked by hand
  ([CASE_126.md](CASE_126.md)); the thoracoscopy training station is a sequence with its safety
  conditions ([THORACOSCOPY.md](THORACOSCOPY.md)). A dataset can test whether an agent
  *recognises* what such a model *does* — it cannot replace the model.
* **What could be used, and how.** Vocabularies (phases, steps, instruments) to name things the
  same way as the literature; a recognition benchmark kept apart from the pack, run by whoever
  holds the data; D4D, whose licence allows it, for work on deformable geometry — on animal
  tissue, not human anatomy.

## Sources

Each row was checked against the dataset's own repository, landing page or paper on 2026-11-11.
Two points could not be read at the source and rest on its abstract or metadata: the full text of
the LungRes80 paper, and the licence field of the CholecSeg8k page.
