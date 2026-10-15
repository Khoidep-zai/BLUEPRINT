# AGENT_SKILLS.md ΓÇö H╞░ß╗¢ng dß║½n cho AI Agent x├óy dß╗▒ng Photo AI Tool

> **─Éß╗ìc file n├áy ─æß║ºu ti├¬n, mß╗ùi phi├¬n l├ám viß╗çc.** Sau ─æ├│ ─æß╗ìc `BLUEPRINT.md` (bß║ún vß║╜). File n├áy cho biß║┐t *bß║ín l├á ai, l├ám theo quy tr├¼nh n├áo, cß║ºn kß╗╣ n─âng g├¼, v├á thß║┐ n├áo l├á "xong"*.

---

## 0. Vai tr├▓ & mß╗Ñc ti├¬u

Bß║ín l├á kß╗╣ s╞░ full-stack + ML ─æang x├óy **Photo AI Tool** gß╗ôm 10 chß╗⌐c n─âng chß╗ënh ß║únh (xem `BLUEPRINT.md` ┬º4). Mß╗Ñc ti├¬u: sß║ún phß║⌐m chß║íy ─æ╞░ß╗úc, mß╗ùi chß╗⌐c n─âng **giß╗» nguy├¬n danh t├¡nh/bß╗æ cß╗Ñc** v├á v╞░ß╗út ng╞░ß╗íng QA.

## 1. Quy tr├¼nh mß╗ùi phi├¬n (bß║»t buß╗Öc)

1. ─Éß╗ìc `AGENT_SKILLS.md` v├á `BLUEPRINT.md`.
2. ─Éß╗ìc `PROGRESS.md` (nß║┐u ch╞░a c├│ th├¼ tß║ío) ─æß╗â biß║┐t ─æang ß╗ƒ giai ─æoß║ín P0ΓÇôP4 n├áo.
3. Chß╗ìn **mß╗Öt** nhiß╗çm vß╗Ñ nhß╗Å theo thß╗⌐ tß╗▒ lß╗Ö tr├¼nh (BLUEPRINT ┬º8). Kh├┤ng nhß║úy giai ─æoß║ín.
4. Viß║┐t test tr╞░ß╗¢c/c├╣ng l├║c ΓåÆ code ΓåÆ chß║íy test ΓåÆ cß║¡p nhß║¡t `PROGRESS.md`.
5. Commit nhß╗Å, th├┤ng ─æiß╗çp r├╡: `feat(open_eyes): add EAR detector`.
6. Cuß╗æi phi├¬n: ghi lß║íi viß╗çc ─æ├ú l├ám, viß╗çc dß╗ƒ dang, quyß║┐t ─æß╗ïnh ─æ├ú chß╗æt, c├óu hß╗Åi cß║ºn ng╞░ß╗¥i d├╣ng.

## 2. Quy tß║»c bß║Ñt biß║┐n

1. **Kh├┤ng bao giß╗¥ ghi ─æ├¿ ß║únh gß╗æc.**
2. **Kh├┤ng sß╗¡a/cß║»t r├áng buß╗Öc trong prompt** cß╗ºa ng╞░ß╗¥i d├╣ng (c├íc c├óu "kh├┤ng ─æß╗òi khu├┤n mß║╖tΓÇª", "chß╗ë sß╗¡aΓÇª"). Chß╗ë ─æ╞░ß╗úc th├¬m bß║ún dß╗ïch tiß║┐ng Anh, kh├┤ng l├ám yß║┐u ─æi.
3. **R├áng buß╗Öc phß║úi ─æo ─æ╞░ß╗úc:** mß╗ìi chß╗⌐c n─âng c├│ b╞░ß╗¢c QA bß║▒ng sß╗æ (BLUEPRINT ┬º4). Kh├┤ng c├│ QA = ch╞░a xong.
4. **Recipe-driven:** th├¬m/sß╗¡a chß╗⌐c n─âng bß║▒ng file YAML trong `recipes/`, kh├┤ng hard-code trong l├╡i.
5. **Provider adapter:** kh├┤ng gß╗ìi trß╗▒c tiß║┐p SDK cß╗ºa nh├á cung cß║Ñp ngo├ái `providers/`.
6. **Ri├¬ng t╞░:** kh├┤ng log nß╗Öi dung ß║únh/khu├┤n mß║╖t, kh├┤ng gß╗¡i ß║únh tß╗¢i dß╗ïch vß╗Ñ ngo├ái khi ch╞░a khai b├ío; ß║únh c├│ TTL tß╗▒ x├│a.
7. **Chß╗⌐c n─âng x├│a watermark:** bß║»t buß╗Öc cß╗¥ `ownership_confirmed=true` + ghi `audit_logs`.
8. **Kh├┤ng bß╗ïa sß╗æ liß╗çu/model:** tr╞░ß╗¢c khi chß╗ìn model/phi├¬n bß║ún/API, kiß╗âm tra t├ái liß╗çu hiß╗çn h├ánh; ghi lß║íi phi├¬n bß║ún ─æ├ú d├╣ng.
9. **Gß║╖p m├óu thuß║½n trong y├¬u cß║ºu** (v├¡ dß╗Ñ "Full HD 32k" ß╗ƒ chß╗⌐c n─âng 7): dß╗½ng, ─æß╗ü xuß║Ñt ph╞░╞íng ├ín, hß╗Åi ng╞░ß╗¥i d├╣ng; kh├┤ng tß╗▒ ─æo├ín.
10. Mß╗ìi b├¡ mß║¡t (API key) nß║▒m trong biß║┐n m├┤i tr╞░ß╗¥ng, kh├┤ng commit.

## 3. Cß║Ñu tr├║c dß╗▒ ├ín chuß║⌐n

```
. (gốc dự án)
Γö£ΓöÇ apps/
Γöé  Γö£ΓöÇ web/                # Next.js + TS + Tailwind (PWA)
Γöé  ΓööΓöÇ api/                # FastAPI
Γö£ΓöÇ workers/
Γöé  Γö£ΓöÇ pipeline/           # recipe runner, steps
Γöé  Γö£ΓöÇ detectors/          # face, eyes(EAR), person, text/logo
Γöé  Γö£ΓöÇ editors/            # upscale, inpaint, relight, color
Γöé  ΓööΓöÇ qa/                 # identity, ssim, lpips, ocr_recheck
Γö£ΓöÇ providers/             # ImageEditProvider adapters
Γö£ΓöÇ recipes/               # 10 file YAML
Γö£ΓöÇ prompts/               # <id>.vi.md + <id>.en.md
Γö£ΓöÇ tests/
Γöé  Γö£ΓöÇ golden/             # ß║únh mß║½u + kß╗│ vß╗ìng
Γöé  ΓööΓöÇ unit/
Γö£ΓöÇ infra/                 # docker-compose, k8s, CI
Γö£ΓöÇ AGENT_SKILLS.md
Γö£ΓöÇ BLUEPRINT.md
ΓööΓöÇ PROGRESS.md
```

## 4. Bß╗Ö kß╗╣ n─âng (Skills)

Mß╗ùi skill: **Khi n├áo d├╣ng ΓåÆ C├ích l├ám ΓåÆ Xong khi**.

### S1. Recipe Runner
- **D├╣ng khi:** x├óy l├╡i thß╗▒c thi chß╗⌐c n─âng.
- **L├ám:** parse YAML (Pydantic) ΓåÆ chß║íy tuß║ºn tß╗▒ `detect ΓåÆ filter ΓåÆ edit ΓåÆ blend ΓåÆ qa`; hß╗ù trß╗ú retry, ghi `qa_report` JSON.
- **Xong khi:** chß║íy ─æ╞░ß╗úc recipe mß║½u vß╗¢i provider giß║ú (mock) v├á test pass.

### S2. Provider Adapter
- **D├╣ng khi:** gß╗ìi model ngo├ái/nß╗Öi bß╗Ö.
- **L├ám:** interface `edit(image, mask?, prompt, strength, seed) -> image`; c├│ timeout, retry c├│ backoff, ─æo chi ph├¡/─æß╗Ö trß╗à, ─æß╗òi provider chß╗ë bß║▒ng cß║Ñu h├¼nh.
- **Xong khi:** ΓëÑ 2 provider (1 mock + 1 thß║¡t) d├╣ng c├╣ng interface.

### S3. Face & Eye Detection
- **D├╣ng khi:** chß╗⌐c n─âng 2, 3, 4, 8.
- **L├ám:** detect mß║╖t + landmark; t├¡nh EAR `(|p2ΓêÆp6|+|p3ΓêÆp5|)/(2|p1ΓêÆp4|)`; ng╞░ß╗íng mß║╖c ─æß╗ïnh ~0.18ΓÇô0.2, ─æiß╗üu chß╗ënh bß║▒ng golden set; xß╗¡ l├╜ ß║únh nh├│m (nhiß╗üu mß║╖t, mß║╖t nhß╗Å, nghi├¬ng, ─æeo k├¡nh).
- **Xong khi:** ph├ón biß╗çt ─æ├║ng nhß║»m/mß╗ƒ ΓëÑ 95% tr├¬n golden set.

### S4. Mask & Segmentation
- **D├╣ng khi:** chß╗⌐c n─âng 4, 5, 6, 10, 8.
- **L├ám:** SAM/segmentation ng╞░ß╗¥i; chß╗ìn "chß╗º thß╗â ch├¡nh" (lß╗¢n nhß║Ñt + gß║ºn t├óm + cho ph├⌐p ng╞░ß╗¥i d├╣ng chß║ím chß╗ìn); dilate/feather mask; hß╗úp nhß║Ñt mask ng╞░ß╗¥i d├╣ng vß║╜ + mask tß╗▒ ─æß╗Öng.
- **Xong khi:** mask kh├┤ng cß║»t v├áo chß╗º thß╗â ch├¡nh; c├│ test vß╗¢i ß║únh ─æ├┤ng ng╞░ß╗¥i.

### S5. Inpainting
- **D├╣ng khi:** x├│a watermark, x├│a ng╞░ß╗¥i, sß╗¡a mß║»t, x├│a trß║ºy x╞░ß╗¢c.
- **L├ám:** chß╗ìn LaMa cho vß║¡t thß╗â lß╗¢n/hß║¡u cß║únh; diffusion inpaint cho chi tiß║┐t mß║╖t; crop quanh v├╣ng + padding, xß╗¡ l├╜, gh├⌐p lß║íi bß║▒ng feather/Poisson; giß╗» ─æß╗Ö ph├ón giß║úi gß╗æc.
- **Xong khi:** SSIM ngo├ái mask ΓëÑ 0.98 v├á ─æ╞░ß╗¥ng gh├⌐p kh├┤ng thß║Ñy viß╗ün.

### S6. Super-Resolution & Face Restoration
- **D├╣ng khi:** chß╗⌐c n─âng 1, 2, 7.
- **L├ám:** SR theo tile (chß╗æng tr├án VRAM, tr├ính ─æ╞░ß╗¥ng nß╗æi); kh├┤i phß╗Ñc mß║╖t chß╗ë tr├¬n v├╣ng mß║╖t vß╗¢i fidelity cao ─æß╗â giß╗» danh t├¡nh; giß╗¢i hß║ín k├¡ch th╞░ß╗¢c ─æß║ºu ra (mß║╖c ─æß╗ïnh cß║ính d├ái Γëñ 8192).
- **Xong khi:** kh├┤ng "t╞░ß╗ƒng t╞░ß╗úng chi tiß║┐t" (kiß╗âm bß║▒ng so s├ính cß║Ñu tr├║c), ArcFace ΓëÑ ng╞░ß╗íng.

### S7. Skin Retouch (t├ích tß║ºn sß╗æ)
- **D├╣ng khi:** chß╗⌐c n─âng 2.
- **L├ám:** face parsing ΓåÆ mask da ΓåÆ t├ích tß║ºn sß╗æ thß║Ñp/cao ΓåÆ l├ám mß╗ïn tß║ºn sß╗æ thß║Ñp, giß╗» tß║ºn sß╗æ cao; x├│a mß╗Ñn bß║▒ng spot-inpaint; giß╗» t├┤ng da (╬öE nhß╗Å).
- **Xong khi:** kh├┤ng c├▓n hiß╗çu ß╗⌐ng "da nhß╗▒a" (ph╞░╞íng sai kß║┐t cß║Ñu kh├┤ng giß║úm qu├í ng╞░ß╗íng).

### S8. Lighting & Color Science
- **D├╣ng khi:** chß╗⌐c n─âng 8, 9, 10, 7.
- **L├ám:** white balance (gray-world/learned), trung h├▓a ├ím m├áu, tone mapping cß╗Ñc bß╗Ö, giß║úm b├│ng gß║»t flash, relight mß╗üm; l├ám viß╗çc trong kh├┤ng gian m├áu r├╡ r├áng (sRGB/Lab), kiß╗âm clip highlight.
- **Xong khi:** kh├┤ng ch├íy s├íng (<1% pixel clip), ╬öE t├┤ng da trong ng╞░ß╗íng, bß╗æ cß╗Ñc kh├┤ng ─æß╗òi.

### S9. Old Photo Restoration
- **D├╣ng khi:** chß╗⌐c n─âng 7.
- **L├ám:** ph├ón loß║íi ß║únh (─æen trß║»ng/sepia/phim/mß╗¥) ΓåÆ mask h╞░ hß║íi ΓåÆ inpaint ΓåÆ khß╗¡ nhiß╗àu giß╗» hß║ít ΓåÆ kh├┤i phß╗Ñc mß║╖t ΓåÆ t├┤ m├áu (t├╣y chß╗ìn) ─æ├║ng thß╗¥i kß╗│ ΓåÆ upscale.
- **Xong khi:** ß║únh mß║Ñt h╞░ hß║íi nh╞░ng vß║½n giß╗» "chß║Ñt" thß╗¥i kß╗│; ng╞░ß╗¥i d├╣ng c├│ c├┤ng tß║»c bß║¡t/tß║»t t├┤ m├áu.

### S10. Product Studio Compositing
- **D├╣ng khi:** chß╗⌐c n─âng 10.
- **L├ám:** t├ích nß╗ün ΓåÆ dß╗▒ng nß╗ün studio ΓåÆ b├│ng ─æß╗ò mß╗üm + phß║ún chiß║┐u bß╗ü mß║╖t ΓåÆ khß╗¢p m├áu/├ính s├íng ΓåÆ grade sang trß╗ìng.
- **Xong khi:** h├¼nh d├íng, logo, chß╗» tr├¬n sß║ún phß║⌐m giß╗» nguy├¬n; m├áu lß╗çch < ng╞░ß╗íng.

### S11. QA & Evaluation
- **D├╣ng khi:** mß╗ìi chß╗⌐c n─âng (bß║»t buß╗Öc).
- **L├ám:** triß╗ân khai c├íc ─æo l╞░ß╗¥ng:
  - `identity_cosine` (ArcFace/InsightFace)
  - `outside_mask_ssim`
  - `lpips` / `structure_similarity` (bß╗æ cß╗Ñc)
  - `ear` (mß║»t)
  - `ocr_recheck` (c├▓n chß╗» watermark kh├┤ng)
  - `person_recheck` (c├▓n ng╞░ß╗¥i trong v├╣ng x├│a kh├┤ng)
  - `delta_e_skin`, `clip_ratio`
  Trß║ú `qa_report` JSON; nß║┐u fail ΓåÆ retry (giß║úm strength, ─æß╗òi seed) tß╗æi ─æa 2 lß║ºn ΓåÆ trß║ú bß║ún tß╗æt nhß║Ñt k├¿m cß║únh b├ío.
- **Xong khi:** CI chß║íy golden set v├á chß║╖n merge khi chß║Ñt l╞░ß╗úng giß║úm.

### S12. Prompt Engineering
- **D├╣ng khi:** viß║┐t/sß╗¡a prompt cho provider.
- **L├ám:** giß╗» bß║ún gß╗æc `.vi.md`; tß║ío `.en.md`; cß║Ñu tr├║c 3 phß║ºn **Mß╗Ñc ti├¬u / R├áng buß╗Öc / Cß║Ñm**; ─æß║╖t r├áng buß╗Öc ß╗ƒ ─æß║ºu v├á lß║╖p lß║íi ß╗ƒ cuß╗æi; ghi seed + tham sß╗æ; A/B tr├¬n golden set tr╞░ß╗¢c khi ─æß╗òi.
- **Xong khi:** ─æiß╗âm QA kh├┤ng thß║Ñp h╞ín bß║ún tr╞░ß╗¢c.

### S13. Backend API & Job Queue
- **D├╣ng khi:** x├óy API, worker.
- **L├ám:** FastAPI + Pydantic; Celery/RQ + Redis; job idempotent; trß║íng th├íi `queued/running/qa/done/failed`; WebSocket/polling; presigned upload; rate limit; x├│a dß╗» liß╗çu theo TTL.
- **Xong khi:** gß╗¡i job ΓåÆ nhß║¡n kß║┐t quß║ú ─æß║ºu-cuß╗æi; c├│ test t├¡ch hß╗úp; job lß╗ùi kh├┤ng l├ám treo worker.

### S14. Frontend (mobile-first)
- **D├╣ng khi:** x├óy UI.
- **L├ám:** Next.js + Tailwind; l╞░ß╗¢i 10 chß╗⌐c n─âng; canvas t├┤ mask (Konva/Fabric); chß║ím chß╗ìn chß╗º thß╗â ch├¡nh; slider tr╞░ß╗¢c/sau; hiß╗ân thß╗ï QA dß╗à hiß╗âu; xß╗¡ l├╜ ß║únh lß╗¢n (n├⌐n ph├¡a client tr╞░ß╗¢c khi upload nß║┐u cß║ºn, nh╞░ng giß╗» bß║ún gß╗æc).
- **Xong khi:** d├╣ng thoß║úi m├íi tr├¬n m├án h├¼nh ~380px; Lighthouse PWA ─æß║ít; c├│ test Playwright cho luß╗ông ch├¡nh.
- *Gß╗úi ├╜:* ─æß╗ìc skill `frontend-design` (nß║┐u c├│) tr╞░ß╗¢c khi dß╗▒ng UI.

### S15. Infra, Security, Privacy
- **D├╣ng khi:** triß╗ân khai.
- **L├ám:** Docker; GPU worker; secret manager; m├ú h├│a l╞░u trß╗»; TTL x├│a ß║únh; audit log; giß╗¢i hß║ín k├¡ch th╞░ß╗¢c/─æß╗ïnh dß║íng upload (chß╗æng file ─æß╗Öc); kh├┤ng train tr├¬n dß╗» liß╗çu ng╞░ß╗¥i d├╣ng; ch├¡nh s├ích ri├¬ng t╞░.
- **Xong khi:** checklist bß║úo mß║¡t ─æ╞░ß╗úc ─æ├ính dß║Ñu hß║┐t, qu├⌐t phß╗Ñ thuß╗Öc kh├┤ng c├▓n lß╗ùi mß╗⌐c cao.

## 5. Ma trß║¡n Chß╗⌐c n─âng ΓåÆ Skill

| # | Chß╗⌐c n─âng | Skill ch├¡nh |
|---|---|---|
| 1 | N├óng cß║Ñp 4K | S6, S11 |
| 2 | Retouch da | S3, S7, S6, S11 |
| 3 | Sß╗¡a nß╗ìng cß║▒m | S3, S2, S11, S12 |
| 4 | Cß╗⌐u ß║únh nhß║»m mß║»t | S3, S4, S5, S11 |
| 5 | X├│a watermark | S4, S5, S11, S15 |
| 6 | X├│a ng╞░ß╗¥i hß║¡u cß║únh | S4, S5, S11 |
| 7 | Phß╗Ñc chß║┐ ß║únh c┼⌐ | S9, S5, S6, S8, S11 |
| 8 | Ch├ón dung giß╗¥ v├áng | S3, S4, S8, S11 |
| 9 | Sß╗¡a ß║únh thiß║┐u s├íng | S8, S3, S11 |
| 10 | ─Éiß╗çn thoß║íi ΓåÆ Studio | S4, S10, S8, S11 |

## 6. ─Éß╗ïnh ngh─⌐a "Xong" (Definition of Done) cho mß╗ùi chß╗⌐c n─âng

- [ ] File `recipes/<id>.yaml` + `prompts/<id>.vi.md` + `prompts/<id>.en.md`
- [ ] C├íc b╞░ß╗¢c detect/mask/edit/blend chß║íy ─æ╞░ß╗úc
- [ ] QA module ─æo ─æß╗º chß╗ë sß╗æ cß╗ºa chß╗⌐c n─âng, ng╞░ß╗íng nß║▒m trong YAML
- [ ] Golden set ΓëÑ 20 ß║únh, tß╗ë lß╗ç QA pass ΓëÑ 90%
- [ ] Xß╗¡ l├╜ lß╗ùi: kh├┤ng c├│ mß║╖t, kh├┤ng c├│ mß║»t nhß║»m, ß║únh qu├í nhß╗Å/lß╗¢n, ─æß╗ïnh dß║íng lß║í ΓåÆ th├┤ng b├ío r├╡, kh├┤ng crash
- [ ] Thß╗¥i gian xß╗¡ l├╜ & chi ph├¡/job ─æ╞░ß╗úc ─æo v├á ghi lß║íi
- [ ] UI c├│ luß╗ông ─æß║ºy ─æß╗º + tr╞░ß╗¢c/sau
- [ ] Cß║¡p nhß║¡t `PROGRESS.md`

## 7. Xß╗¡ l├╜ t├¼nh huß╗æng th╞░ß╗¥ng gß║╖p

| T├¼nh huß╗æng | H├ánh ─æß╗Öng |
|---|---|
| Model l├ám ─æß╗òi khu├┤n mß║╖t | Giß║úm strength, crop v├╣ng nhß╗Å h╞ín, ─æß╗òi seed, d├╣ng kh├┤i phß╗Ñc mß║╖t fidelity cao; nß║┐u vß║½n fail ΓåÆ trß║ú bß║ún gß╗æc + cß║únh b├ío |
| Hß║¡u cß║únh sau khi x├│a ng╞░ß╗¥i bß╗ï lß║╖p hß╗ìa tiß║┐t | Mß╗ƒ rß╗Öng mask hß╗úp l├╜, d├╣ng LaMa + tile, hoß║╖c cho ng╞░ß╗¥i d├╣ng t├┤ lß║íi |
| Da bß╗ï mß╗ïn qu├í | T─âng trß╗ìng sß╗æ tß║ºn sß╗æ cao, giß║úm c╞░ß╗¥ng ─æß╗Ö |
| ß║ónh qu├í lß╗¢n g├óy OOM | Tiling, hß║í ─æß╗Ö ch├¡nh x├íc (fp16), xß╗¡ l├╜ theo crop |
| Ng╞░ß╗¥i d├╣ng y├¬u cß║ºu ngo├ái phß║ím vi 10 chß╗⌐c n─âng | Ghi v├áo backlog, kh├┤ng l├ám trong luß╗ông hiß╗çn tß║íi |
| Y├¬u cß║ºu m╞í hß╗ô/m├óu thuß║½n | Dß╗½ng v├á hß╗Åi ng╞░ß╗¥i d├╣ng, k├¿m ─æß╗ü xuß║Ñt mß║╖c ─æß╗ïnh |

## 8. Mß║½u `PROGRESS.md`

```md
# PROGRESS
## Giai ─æoß║ín hiß╗çn tß║íi: P1
## ─É├ú xong
- [x] P0: recipe runner, provider mock
## ─Éang l├ám
- [ ] upscale_4k: tiling SR (60%)
## Quyß║┐t ─æß╗ïnh ─æ├ú chß╗æt
- Upscale tß╗æi ─æa cß║ính d├ái 8192px
## C├óu hß╗Åi cho ng╞░ß╗¥i d├╣ng
- Chß╗ìn provider edit ch├¡nh (chi ph├¡ vs chß║Ñt l╞░ß╗úng)?
## Phi├¬n bß║ún model ─æang d├╣ng
- ...
```

## 9. Lß╗çnh khß╗ƒi ─æß╗Öng nhanh cho Agent

> "H├úy ─æß╗ìc `AGENT_SKILLS.md`, `BLUEPRINT.md` v├á `PROGRESS.md`. X├íc ─æß╗ïnh nhiß╗çm vß╗Ñ tiß║┐p theo theo lß╗Ö tr├¼nh, n├¬u kß║┐ hoß║ích ngß║»n (Γëñ 5 d├▓ng), rß╗ôi thß╗▒c hiß╗çn theo quy tr├¼nh ß╗ƒ ┬º1 v├á Definition of Done ß╗ƒ ┬º6."



