# RebateM8 NSW — Backend Flow & Logic Reference

> Current-state reference for the `rebatem8_nsw_backend` (Express 5 + TypeScript + Mongoose). Covers every module's endpoints, validation, and the core logic/flow. Generated 2026-08-21 from a full read-only survey of `src/`.

---

## Contents
1. [Overview & architecture](#1-overview--architecture)
2. [Conventions (envelope, validation, pagination, infra)](#2-conventions)
3. [Authentication & sessions](#3-authentication--sessions)
4. [Authorization — the two layers](#4-authorization--the-two-layers)
5. [Companies (installers) & members](#5-companies-installers--members)
6. [Users](#6-users)
7. [Contractor groups & roles](#7-contractor-groups--roles)
8. [Products & the calculator](#8-products--the-calculator)
9. [Original equipment & the job matrix](#9-original-equipment--the-job-matrix)
10. [Job lifecycle](#10-job-lifecycle)
11. [Job create / update / list / soft-delete](#11-job-create--update--list--soft-delete)
12. [Engagement flow](#12-engagement-flow)
13. [Nomination flow](#13-nomination-flow)
14. [Site assessment — products → tasks/units/photos](#14-site-assessment--products--tasksunitsphotos)
15. [Photo capture](#15-photo-capture)
16. [Notes](#16-notes)
17. [Storage](#17-storage)
18. [Unlabel photos, CMS, activity-log, address, job-history](#18-supporting-modules)
19. [Known code-comment discrepancies](#19-known-code-comment-discrepancies)

---

## 1. Overview & architecture

RebateM8 NSW administers two NSW energy certificate schemes for the ACP **1st Energy Rebates**:

- **ESS** (Energy Savings Scheme) → **ESC** certificates.
- **PDRS** (Peak Demand Reduction Scheme) → **PRC** certificates.

Certificates are ultimately lodged into the **TESSA** portal (CSV export spec'd, not built).

**Two activity families only** (windows/glazing removed; batteries/lighting/refrigeration/pool pumps out of scope):

| Activity family (`ActivityType`) | Schemes | Certificate/activity codes |
|---|---|---|
| **Heating & Cooling** `heating_cooling` | ESS + PDRS | ESS `D16` (residential ESC), `F4` (business ESC); PDRS `HVAC1` (res PRC), `HVAC2` (biz PRC) |
| **Hot Water Heat Pump** `hot_water_heat_pump` | ESS only | ESS residential `D17`–`D20` (+ `D21` manual), business HPWH `F16`/`F17` |

**Modular layout** — every domain lives in `src/modules/<name>/` with `model / types / service / controller / routes / validation`, mounted in `src/routes.ts` under `/api/v1`. Modules: `address, auth, calculator, cms, contractor-group, customer, installer, job, job-history, job-matrix, job-task, note, original-equipment, product, role, storage, unlabel-photo, user` + the public `engagement`/`nomination` signing routes.

---

## 2. Conventions

- **Response envelope (global):** every response is wrapped by `responseFormatter` as `{ success, statusCode, message, data }`. Controllers just `res.json(data)` and set `res.locals.message = MESSAGES.X.Y` (`src/common/constants/messages.ts`). *(Streamed responses via `res.write`/`res.end` — e.g. the ZIP export — bypass the wrapper.)*
- **Errors:** thrown `AppError.notFound / .badRequest / .conflict / .forbidden / .unauthorized`; the error body carries `{ code, details }`.
- **Validation:** Zod, `.strict()` schemas, via `validate({ body | query })` middleware. `withPrunedEmpty` drops blank `""`/null optional fields before validation (so a blank field reads as "not sent") — used across user/installer/member/insurance schemas.
- **Pagination:** skip + limit (never page) → `{ items, total, skip, limit, isNext }` (`common/utils/pagination.ts`).
- **Phone numbers:** stored as entered (whitespace stripped, **leading `0` kept**); matched with a `^0?<national>$` matcher; the `0` is stripped only at the E.164/SMS boundary.
- **Infra (non-negotiable):** NO `.env` — all secrets in AWS Secrets Manager, fetched at boot via typed config (git-ignored `secrets.dev.json` is the only dev exception). NO static AWS keys (SSO / IAM roles). Private S3 + short-lived presigned PUT/GET URLs — bytes never proxied through the server. Frontend/mobile never touch AWS. Port 3000, Mongo Atlas, S3 `ap-southeast-2`.

---

## 3. Authentication & sessions

Module `src/modules/auth`. Access + refresh JWTs are delivered **only as httpOnly cookies** (`access_token` / `refresh_token`) — never in the JSON body (`withoutTokens` strips them). Protected routes also accept `Authorization: Bearer` (mobile).

| Method / path | Purpose | Guard |
|---|---|---|
| `POST /auth/admin/login` | Admin / admin_user email + password login | public, `validate(adminLoginSchema)` |
| `POST /auth/otp/request` | Send 6-digit OTP to a user's phone | public |
| `POST /auth/otp/verify` | Verify OTP, log user in | public |
| `POST /auth/select-company` | Pick active company, re-issue access token | `requireAuth` |
| `POST /auth/bypass-login` | Impersonate a company user ("login as") | staff only |
| `POST /auth/exit-impersonation` | Return to the original admin | `requireAuth` |
| `POST /auth/refresh` | Rotate the token pair | public (token from cookie/body) |
| `POST /auth/logout` | Revoke current session, clear cookies | `requireAuth` |
| `GET /auth/me` | Profile + displayRole + active company + impersonating flag | `requireAuth` |
| `GET /auth/companies` | List the user's companies (picker) | `requireAuth` |
| `GET /auth/sessions` | List the user's active devices/sessions | `requireAuth` |
| `DELETE /auth/sessions/:sessionId` | Revoke one of the user's own sessions | `requireAuth` |

**Logic**
- **Admin login:** must be active, have a passwordHash, be roleType `admin`/`admin_user`, bcrypt verify. Generic "Invalid email or password" on any failure.
- **User OTP:** code length **6**, TTL **5 min**, **max 5 attempts**, resend cooldown **30 s**, bcrypt-hashed code, TTL index cleanup. `requestUserOtp` is a **silent no-op** when no active user matches the phone (anti-enumeration). Whitelisted test numbers / a configured test code bypass real SMS. SMS via Twilio.
- **Tokens:** access ~1h, refresh ~30d. Access claims: `sub, typ, role, sid, ver(tokenVersion), cid?(selected company), plt?, imp?(impersonator)`. **`tokenVersion` revocation** — `requireAuth` loads the user each request and rejects if `tokenVersion` ≠ token's `ver`.
- **Refresh rotation + reuse detection:** a replayed/rotated refresh token **revokes the whole session** ("Refresh token reuse detected").
- **Company selection is per-session/per-device** — sets `session.selectedInstallerId` and re-issues the access token with the `cid` claim; the refresh cookie is unchanged, so web and mobile keep independent active companies.
- **Impersonation:** staff only; target must be a `user` and an active member of the installer; issues a token with `imp=adminId` + `cid`; `exit` mints a fresh admin pair.
- **displayRole:** admin→"Master Admin"; admin_user→"Master Admin User"; else by accessType (Admin→"Installer Admin", Contractor→"Installer Contractor", Sales→"Installer Salesperson", else "Installer User").

---

## 4. Authorization — the two layers

There is **no platform-wide per-user permission list**. Access = two layers:

**Layer 1 — platform `roleType`** (`RoleType`: `admin`, `admin_user`, `user`) via `requireRole(...)`. `PLATFORM_STAFF = [admin, admin_user]` short-circuits every company guard.

**Layer 2 — company membership** via `userInstallers` (the `UserInstaller` join, unique `{userId, installerId}`). Each membership carries `accessType`, company `roles[]`, and a `permissions[]` override list. A user can belong to multiple companies; the selected company is per-session (`cid` claim).

**Enums**
- `CompanyRole`: `Admin`, `Manager`, `Business Director`, `Plumber`, `Electrician`, `Refrigeration Mechanic`, `Window Installer`, `Other`.
- `CompanyAccessType`: `Admin`, `User`, `Contractor`, `Sales`.
- `SignOffResponsibility`: `No process sign-off responsibility`, `Installation sign-off`, `Job entry only`, `Electrical sign-off`, `Plumbing / gas fitting sign-off`, `Refrigerant-handling sign-off`, `Evidence / documentation QA sign-off`, `Final job / implementation sign-off`.

**Company permissions** (`common/company-permissions.ts`): `company.update`, `company.member.read`, `company.member.manage`, `company.job.create`, `company.job.read`, `company.file.upload`. Defaults by accessType — **Admin = all**; **User & Contractor** = member.read + job.create + job.read + file.upload; **Sales** = same minus file.upload. Per-membership `permissions[]` unions with the defaults.

**Middleware** (`src/common/middleware`)
- `requireAuth` — verifies the token, distinct `token_expired` code on expiry, one DB read to confirm active + tokenVersion, populates `req.user = { id, roleType, sessionId, companyId, platform, impersonatorId }`.
- `requireRole(...roles)` — platform gate (403 unless roleType matches).
- `requireCompanyMemberOrPlatform` / `requireStaffOrCompanyMember` — staff OR active member (of the target company / of *some* company).
- `requireCompanyPermission(perm)` / `requireCompanyManageOrPlatform(perm)` — active membership + company active + permission.
- `requireMemberManageOrSelf(perm)` — staff, OR member with the permission, OR the request targets the caller's own `:userId`.
- `requireJobAccess` / `resolveJobAccess` — resolves the job (id from `params.id` or `body.jobId`) **excluding soft-deleted jobs (`isDeleted: { $ne: true }`)** so deleted jobs 404 across every job-scoped route; staff reach any job, others must be an active member of the job's active company. Caches `JobScope` on `res.locals.jobScope`.

*Company-scope helper:* membership queries `populate({ path:'installerId', match:{ isActive:true } })` so an inactive/deleted company populates as `null` and those rows are dropped everywhere (picker, select-company, job access).

---

## 5. Companies (installers) & members

Module `src/modules/installer`. A **company = installer** (one collection). People = users with `userInstaller` memberships.

| Method / path | Purpose | Guard |
|---|---|---|
| `POST /installers` | Create company + head admin + membership | staff only |
| `GET /installers` | Paginated company list | staff only |
| `PUT /installers/head-admin` | Promote an existing member to head admin | `MEMBER_MANAGE` |
| `GET /installers/:id` | Company detail + members | member-or-platform |
| `PUT /installers/:id` | Update company fields | `COMPANY_UPDATE` |
| `GET /installers/:installerId/members` | List active members (+search) | `MEMBER_READ` |
| `GET /installers/:installerId/members/by-role` | Minimal `{_id,name}` by company role | member-or-platform |
| `GET /installers/:installerId/members/:userId` | Single member detail | `MEMBER_MANAGE`-or-self |
| `POST /installers/:installerId/members` | Add member (new or link existing) | `MEMBER_MANAGE` |
| `PUT /installers/:installerId/members/:userId` | Update member | `canManageMembers` |
| `DELETE /installers/:installerId/members/:userId` | Soft-remove member | `canManageMembers` |

**Company validation** — `createInstaller` requires `companyName` (1–200), `abn` (8–20), `address` (1–300), and a nested required `admin{firstName,lastName,email,countryCode,phoneNumber}`. Optional: `suburb` (1–100), `email`, `countryCode`, `phoneNumber`, `flagCode`, `logo`, `website` (url), **`activityType` (free-text ≤150 — NOT the job enum)**, `insurance` (shared `CompanyInsurance`), `rebateValues`, `status` (`InstallerStatus`). Update = same optional + `isActive`.

**Company logic**
- `createInstaller` (transactional): rejects duplicate companyName/ABN; generates `installerCode` `I01-#####`; reuses an existing user matching the admin email/phone **but rejects a platform-staff account**; creates the head-admin membership (`roles:[Admin], accessType:Admin`).
- `changeHeadAdmin` (transactional): incoming user must already be an active member; outgoing keeps Admin *access* but loses the Admin *role*; incoming gains both.

**Members**
- **Add** (transactional) — two shapes: new person with no match → create user + membership (`isNewUser:true`); new person **with** a match → never silent-link, returns **409 `USER_EXISTS_CONFIRM_REQUIRED`** carrying `matchedUser` + `matchedOn` (`email`|`phone`); the client re-POSTs with `userId` to confirm → membership-only (the person's identity/licences are NOT overwritten across companies). Already an active member → **409 `MEMBER_ALREADY_IN_COMPANY`**. Platform admins and self-add are blocked; a soft-removed membership is reactivated.
- **Add/update validation:** `roles[]` (min 1) + `accessType` required; either `userId` OR all new-user fields; optional `contractorGroupId`, `licences[]`, `trainings[]`, and RESA onboarding fields `commencementDate`, `signOffResponsibilities[]` (max 8), `essResaOnboardingCompleted`, `essResaOnboardingCompletionDate`. **No `qualifications` and no `insurance` at membership level** (insurance is company-level or per-licence, never per-person).
- **Update** — head-admin protected (cannot deactivate / drop Admin role / drop Admin access → 409 `HEAD_ADMIN_PROTECTED`; transfer via `changeHeadAdmin`). `licences`/`trainings` REPLACE semantics.
- **Remove** — soft (`isActive=false`); head admin cannot be removed.

**Per-person licences (`TradeLicence`)** — `trade` (`LicenceTrade`: Plumber / Electrician / Refrigeration Mechanic / Window Installer) + `licenceNumber` required; optional `completedDate`, `expiryDate`, `status` (always **derived server-side** from expiry, never trusted from client), `gas` (bool = gasfitting authorised on a plumber licence), ARCtick sub-licence `arctickLicenceNumber` / `arctickClass` (`LicenceClass`: RAC01 / RSS03 / Other) / `arctickClassOther` / `arctickCompletedDate` / `arctickExpiryDate` / `arctickDocumentUrl`, `qualification`, `registeredCompany{…}`, `operatesUnderInstallationCompany`, per-licence `insurance` (only when `operatesUnderInstallationCompany=false`), `documentUrl`. *Legacy `purpose`/`scheme`/`issuingBody` and membership-level `relationshipToAcp` were removed.*

`InstallerStatus`: New contact, Allocated, Sent jot form link, Received Jot Form, Onboarding booked, Onboarded, Further training needed, Not completing jobs, Dormant, Turned Inactive, Lost, TBC, TBC 2.

---

## 6. Users

Module `src/modules/user`. Users are the person identity, global and reused across companies.

| Method / path | Purpose | Guard |
|---|---|---|
| `GET /users/lookup` | Existing-user pre-check for add-member | any authed |
| `GET /users` | Paginated list enriched with companies | staff only |
| `POST /users` | Create a user | staff only |
| `GET /users/:id` | User detail + companies + membership fields | staff only |
| `PATCH /users/:id` | Update person **and** (staff) membership fields | self-or-staff |

**`PATCH /users/:id`** — the admin "Edit User" form saves in one call. Self (own id) or staff; a non-staff caller may edit only themselves and has `isActive` + all membership fields stripped. The controller **splits** the body: person fields → `userService.updateUser`; membership fields (staff only) → `memberService.updateMember` for the resolved company (`installerId` in the body, else the user's single active membership, else 400). **Company removal is a separate `DELETE /installers/:installerId/members/:userId` call.**

**Validation** — `createUser` requires `firstName`/`lastName` + `roleType`; the service enforces email+password for admin roles and countryCode+phone for `user`. `updateUser` is all-optional and uses **REPLACE-semantics arrays** `licences[]`, `trainings[]`, `qualifications[]`. `TrainingType`: `ESS`, `RESA`, `whs_induction`, `working_at_heights`, `manufacturer_installation`, `no_additional_relevant_training`, `other`. *Dropped everywhere: `dateOfBirth`, `schemeParticipantId`.*

---

## 7. Contractor groups & roles

**Contractor groups** (`src/modules/contractor-group`) — named groups of contractor members within a company. The group doc stores **no member list**; membership is derived from `UserInstaller.contractorGroupId` (single source of truth). Endpoints: `POST /` create, `GET /` list (+members, feeds the job step-3 dropdown), `GET /:id`, `PUT /:id` rename/activate, `DELETE /:id` (blocked while any active member still references the group). Unique name per installer (case-insensitive).

**Roles** (`src/modules/role`) — read-only catalogue of the three platform roles (Admin / Admin User / User), idempotently seeded; used only to stamp `roleId`. `GET /roles` (staff only).

---

## 8. Products & the calculator

### Products (`src/modules/product`, `/api/v1/products`)

Three collections keyed by `ProductCategory`, each with a unique `lookupKey = ${brand}|${model}` (recomputed server-side, never client-supplied):

| Category | Model | Serves |
|---|---|---|
| `air_conditioner` | `AcProduct` | D16, HVAC1, F4, HVAC2 (nested residential/commercial specs) |
| `heat_pump_water_heater` | `HeatPumpProduct` | F16, F17 (zone3/zone5) |
| `water_heater` | `WaterHeaterProduct` | D17–D20 (`block` heat_pump → zones, solar → specs) |

- **Imports** (staff only): `POST /products/{air-conditioners|heat-pump-water-heaters|water-heaters}/import` — multer in-memory xlsx (20 MB, never on disk), ExcelJS parse, upsert by `lookupKey` in batches; returns `{imported, updated, skipped}`.
- **Lists** (any auth, default `isActive:true`): `GET /products` (union across all three, `?category/block/isActive`), `/products/brands`, `/products/brands/:brand/models`, and the per-category lists.
- **`PATCH /products/status`** (staff) — **bulk** activate/deactivate by ids across all three collections (only the owning one touched); `{ productIds[] (1–500), isActive }`. Declared **before** `/:id` so "status" isn't parsed as an id.
- **`PATCH /products/:id`** (staff) — edit one product, body **discriminated by `category`**; on brand/model change `lookupKey` is recomputed and re-checked (409 on dup).

### Calculator (`src/modules/calculator`, `/api/v1/calculators`)

Certificate-estimation engine — ESS activities → ESCs, PDRS activities → PRCs. Resolves a product (or manual inputs), builds a flat input bag, runs one pure function per activity code. Missing data never throws — it returns `eligible:false` + a `status`. **The client-verified xlsx widgets are the source of truth; engine functions are ported verbatim.**

- `ActivityCode`: `D16, HVAC1, F4, HVAC2, F16, F17, D17, D18, D19, D20, D21`. `CertType`: `ESC, PRC`. `FuelType` (existing-unit fuel): `electric`, `gas`.
- **Category → activity:** `air_conditioner → [D16, HVAC1, F4, HVAC2]`; `heat_pump_water_heater → [F16, F17]`; `water_heater` block SOLAR → `[D18, D20]` else `[D17, D19]`. Narrowing: AC + segment (residential `[D16,HVAC1]` / business `[F4,HVAC2]`); water_heater + `oldFuel` (electric D17/D18, gas D19/D20); HPWH + installType (New F17 / Replacement F16). `D21` is manual (no product).
- **Endpoints** (all `requireAuth`): `GET /calculators/types` (catalogue of 11), `GET /calculators/original-equipment` (step-3 dropdown; activity restricted to the two families), `GET /calculators/prefill` (a product's inputs + applicable activities), `POST /calculators/estimate` (all applicable calculators for a product batch → `results`/`total`/`byProduct`), `POST /calculators/:type/estimate` (one code; `:type` validated against `ActivityCode`).

---

## 9. Original equipment & the job matrix

**Original equipment** (`src/modules/original-equipment`) — `IOriginalEquipment { label, activity(heating_cooling|hot_water_heat_pump), oldFuel?(electric|gas, selects the D-code), installType(new|replacement), order, isActive }`. It's the stable key a matrix rule is written against (one rule per equipment) and backs the step-3 "existing system" dropdown. Non-destructive seed (`CURATED`): 7 heating/cooling options + 5 hot-water options. Exposed only through the calculator + job-matrix (no dedicated router).

**Job matrix** (`src/modules/job-matrix`, `/api/v1/matrix`) — **a PHOTO/evidence template, not a trade matrix.** A rule defines which photo boxes a job task is seeded with. `IJobMatrix { ruleNo, originalEquipmentId(the only key, unique), activityCodes[], scheme?, productTypeLabel?, units: Partial<Record<UnitType, MatrixUnitTemplate>>, isBuiltIn, isActive }`. Admins author `existing/decommissioning/new/records`; `optionalExtra` is server-owned (20 fixed spare boxes) and stripped from responses / rejected on PATCH.

`deriveCertificateCodes(activity, oldFuel, installType)` (server-owned, re-derived on save):
- `heating_cooling` → `['D16','HVAC1','F4','HVAC2']`, scheme `ESS+PDRS`.
- hot water `installType='new'` → `['F17']`, `ESS`.
- hot water `oldFuel='gas'` → `['D19','D20','F16']`, `ESS`.
- hot water else (electric) → `['D17','D18','F16']`, `ESS`.

Endpoints (all staff only): `GET /matrix` (one row per original equipment, "Add" where no rule), `GET /matrix/equipment` (equipment with no rule yet), `GET /matrix/:id`, `POST /matrix` (409 if a rule already exists for that equipment; codes/scheme NOT accepted), `PATCH /matrix/:id` (equipment immutable; codes/scheme/label re-derived).

---

## 10. Job lifecycle

`JobStatus` is **ordered**; automatic (system-driven) changes are **forward-only**, manual admin changes may go anywhere.

**Ordered statuses:** `engagement_sent`(1) → `good_to_go`(2) → `site_assessment_complete`(3) → `nomination_signature_requested`(4) → `nomination_signed`(5) → `photos_started`(6) → `photos_complete`(7) → `customer_signature_requested`(8) → `installer_signature_missing`(9) → `missing_evidence`(10) → `requested_evidence_provided`(11) → `final_review`(12) → `passed_review`(13) → `failed_review`(14) → `ready_to_register`(15) → `submitted_to_tessa`(16) → `registered`(17) → `ready_to_pay`(18) → `paid`(19) → `archived`(20) → `cancelled`(21) → `ineligible`(22) → `spare`(23).

**Who drives each move**
- Create → `engagement_sent`.
- Customer signs engagement (public) → `good_to_go`.
- Products captured in site assessment → auto `site_assessment_complete` (team optional).
- Admin "Send nomination form" (only from `site_assessment_complete`) → `nomination_signature_requested`.
- Customer signs nomination (public) → `nomination_signed`.
- First mandatory photo → `photos_started`; all mandatory → `photos_complete` (excludes `optionalExtra`).
- Review → register → pay chain: auto-advances from other modules or manual admin edits. `archived`/`cancelled`/`ineligible`/`spare` are terminal buckets set manually.

**Forward-only vs manual** — `isForwardStatus(from,to)` is true only when `to`'s order is strictly greater (unknown status = blocked). `autoAdvanceStatus` / `applyAutoStatus` are the single guard for system moves (bail if not forward, else set + save + record `STATUS_CHANGED` with `metadata.auto:true`). Manual `updateJob({status})` is **not** routed through the guard — an admin may move to any status (backward included); a manual move also best-effort calls `syncNotesToJobStatus`.

---

## 11. Job create / update / list / soft-delete

Module `src/modules/job`. Routes mounted under `/jobs`.

| Method / path | Purpose | Guard |
|---|---|---|
| `POST /jobs` | Create job + customer | `requireCompanyMemberOrPlatform` |
| `GET /jobs` | Paginated list (company-scoped for non-staff) | `requireStaffOrCompanyMember` |
| `DELETE /jobs` | **Bulk soft-delete** | staff only |
| `POST /jobs/restore` | **Bulk restore** | staff only |
| `GET /jobs/:id` | Job detail (fields + team + engagement/nomination) | `requireJobAccess` |
| `GET /jobs/:id/history` | Activity timeline | `requireJobAccess` |
| `PATCH /jobs/:id` | Update job fields | `requireJobAccess` |
| `POST /jobs/:id/send-nomination` | Send nomination form + advance status | `requireJobAccess` |
| `POST /jobs/:id/engagement/resend` · `…/nomination/resend` | Resend one channel | `requireJobAccess` |
| `POST /jobs/:id/site-assessment` | Assign team + capture products | `requireJobAccess` |
| `…/tasks`, `…/photos`, `…/all-photos`, `…/export-photos`, `…/unlabel-photos`, photo attach/upload | Site-assessment & photo endpoints | `requireJobAccess` |

**Create** — verifies the installer; validates every `contractorGroupId` belongs to this active installer; **geocodes server-side** (strips any client `location`, geocodes the address string → `{type:'Point', coordinates:[lng,lat]}`; coordinates are always derived, client location ignored). In one transaction it creates a **new Customer per job** + the Job (`status=engagement_sent`, `jobNumber = M8N######` from an atomic counter), seeds a pending engagement sub-doc, records `CREATED`, and fires a **background** engagement send (fact-sheet email + engagement email + SMS) — create returns immediately.

**Update** — merge semantics; records a split `STATUS_CHANGED` + `UPDATED` history.
- **`LOCKED_AFTER_SIGN` (once the engagement is signed):** only **`activityType`, `customerType`, `equipmentQuoted`** are frozen (409 conflict). Everything else — **`address`, `customer`, `systemType`, `installationDate`**, plus workflow fields (`status`, `team`, `contractorGroupId`, `methodOfLeadGeneration`, `ownReference`, `isActive`) — stays editable. The signed engagement snapshot is immutable regardless.
- `address` MERGES onto the stored address, strips any client `location`, and **re-geocodes** the merged address. `equipmentQuoted` REPLACES the whole array. `team` MERGES. `customer` fields merge onto the separate Customer doc (email lower-cased).
- `contractorGroupId` may arrive top-level or nested in `team`; normalized (undefined=leave, null/`[]`=clear, string→`[string]`, array de-duped), validated against owned active groups, and stored on the top-level array.

**List** — non-staff callers are scoped to companies they're an active member of; a Contractor is further scoped to their own contractor group. Search matches jobNumber/ownReference/suburb/postcode + customer name/email/phone. `?deleted=true` = staff-only trash view.

**Soft delete / restore** (see also the standing rule: *never destroy job data*)
- **`DELETE /jobs` `{ jobIds[] }`** (no reason) — sets `isDeleted/deletedAt/deletedBy`. Nothing destroyed; child JobTask/TaskUnit/TaskPhoto/JobHistory left intact and unreachable through the hidden parent; **customer + S3 untouched**. Idempotent → `{ deletedCount, requested, notFound[] }` (already-deleted ids skipped via a guarded `updateMany`; `notFound` = ids matching no job).
- **`POST /jobs/restore` `{ jobIds[] }`** — clears the flags → `{ restoredCount, requested, notFound[] }`.
- **Read-path exclusion** `isDeleted:{ $ne:true }` is applied in `listJobs` (default), `getJobDetail`, `updateJob`, `applyAutoStatus`, `maybeCompleteSiteAssessment`, `sendNomination`, and — the key choke point — `resolveJobAccess` (covers every `/:id/*` sub-route). Only staff `deleted=true` shows deleted jobs.
- **Audit:** one `JobHistoryEvent.DELETED` (carries `fromStatus`) / `RESTORED` per job actually flipped.

**Key validation** — `createJobSchema`: `installerId`, `activityType`, `customerType`, `customer{name,email,phoneNumber,…}` required; optional `contractorGroupId`, `systemType`, `methodOfLeadGeneration`, `ownReference`, `installationDate`, `address`, `equipmentQuoted[]`. `updateJobSchema`: all optional. **`address.location.type` defaults to `'Point'`** (client may send just `coordinates`) — but whatever the client sends is discarded and re-derived by geocoding. `deleteJobsSchema`/`restoreJobsSchema` = `{ jobIds: string[24] (1–200) }`.

---

## 12. Engagement flow

Module `src/modules/job/engagement.service`. Public signing routes are token-gated (no login).

- **Send on create** — three channels via `ChannelDelivery`: (1) fact-sheet email (ESS/PDRS PDF pulled from S3 as an attachment), (2) engagement email (CMS `engagement_letter` merged with job data + equipment table + a tokenised sign link), (3) engagement SMS (same link, Twilio). Missing email/phone recorded as a `failed` channel. Never throws.
- **Customer signing** (`POST /engagement/sign`, token-gated) — one-time (rejects if already signed or status ≠ `engagement_sent`). Uploads the drawn image to **private S3** and stores only the **`signatureImageKey`**. Captures an **immutable `snapshot`** (letterHtml, company/customer name, activity/customer type, equipment, installationDate, address) — later job/CMS edits never change it. Advances to `good_to_go` (forward-only). Records `ENGAGEMENT_SIGNED` (customer actor). `getPublicDetail` returns `canSign` only while unsigned + `engagement_sent`, and a short-lived presigned `signatureUrl` once signed.
- **Resend** (admin, per channel, only while `engagement_sent` + unsigned) — increments that channel's own attempt counter, records `ENGAGEMENT_RESENT`.

---

## 13. Nomination flow

Module `src/modules/job/nomination.service`. NSW Energy-Saver/Capacity-holder nomination form (5 sections).

- **Send** — admin "Send nomination form" button, **only valid from `site_assessment_complete`** (else 409). Advances forward-only to `nomination_signature_requested`, then best-effort sends email + SMS (both channels recorded), records `NOMINATION_SENT`.
- **Signing** (`POST /engagement/nomination/sign`, token-gated) — guards: engagement already signed, one-time, and if `previouslyNominated` then `previousNominationReason` is required. Uploads the drawn signature to private S3 → key. Captures an **immutable 5-section snapshot** (§1 customer, §2 schemes+address+activity description, §3 ACP static, §5 declaration) and stores §4 `previouslyNominated` (+ optional reason). Advances forward-only to `nomination_signed`. Records `NOMINATION_SIGNED`.
- **Public detail** returns the 5 sections: §1 energy saver, §2 implementation (`heating_cooling` → schemes `[ESS,PDRS]`, else `[ESS]`), §3 ACP, §4 past-activity question, §5 declaration; `canSign` only while `nomination_signature_requested` + unsigned.
- **Resend** — admin, per channel, only while `nomination_signature_requested` + unsigned; records `NOMINATION_RESENT`.

---

## 14. Site assessment — products → tasks/units/photos

Module `src/modules/job-task`. **Model chain:** `Job → JobTask (jobId, one per product) → TaskUnit (taskId, one per UnitType) + TaskPhoto (taskId, one per photo box)`.

- `UnitType`: `existing | decommissioning | new | records | optionalExtra`. `TaskStatus`: `not_started | in_progress | complete`. `RecordType`: `photo | declaration | document`. `PhotoSetType`: `photoSet | additionalPhotoSet`.
- **`POST /jobs/:id/site-assessment`** `{ products?, team? }` (idempotent step-save) — order: products (`createTasks`) → team (via `updateJob({team})`) → `maybeCompleteSiteAssessment`. `createTasks` **rejects while status is `engagement_sent`** ("must be signed before adding products"); on a re-save it refuses when any photo is already captured (edit an individual product instead), else rebuilds. Per product it resolves the matrix rule (by `originalEquipmentId`, else by the `originalEquipment` label) and **seeds** the checklist if a rule exists. Records `PRODUCTS_ADDED`.
- **Seeding** (`seedUnitsAndPhotos`) — idempotent upserts (swallows dup-key). `optionalExtra` spare boxes are **job-level → seeded on the first task only**. **Multi-head expansion:** for `new` units, indoor boxes are repeated per `indoorHeadQuantity` and labelled `… MH {n}`. `additionalPhotoSet` boxes materialize only when the template's `extraPhotos` flag is on.
- **`PATCH /jobs/:id/tasks`** — unified add/edit/delete (exactly one of `isAdd|isEdit|isDelete`). Edit handles: equipment/head-count change → archive captures + re-seed; brand/model change → archive captures, clear captures, reset unit status, keep rows, relabel; field-only → persist. Delete re-parents the `optionalExtra` bucket to the next task if one remains. After each op → `ensureOptionalExtra` + `rebuildJobProducts`. Records `PRODUCT_EDITED` / `PRODUCT_DELETED`.
- **Auto-advance** — `maybeCompleteSiteAssessment` advances `good_to_go → site_assessment_complete` (forward-only) once `job.products.length > 0` (team optional).

---

## 15. Photo capture

Two variants, both funnel into `applyCapture`.

- **Variant A — presigned PUT:** `POST /jobs/photos/upload-url` → client PUTs bytes straight to S3 (client embeds EXIF) → `POST /jobs/:id/tasks/:taskId/photos/:photoId/attach` (server does no image work). Versioned filename `{unitType}-{photoIndex}-v{n}`.
- **Variant B — multipart:** `POST /jobs/:id/tasks/:taskId/photos/:photoId/upload` — server embeds EXIF (geotag + capture time) via `exiftool-vendored` (JPEG-only no-op otherwise) and uploads to S3.

**Shared semantics**
- **`captureId` offline dedupe** (required from mobile) — a re-sent capture is a no-op (checks active + `discarded[]`).
- **Retake history** — a retake pushes the current active onto `discarded[]` (newest-first, full metadata); S3 keys are versioned so nothing is overwritten.
- **Out-of-order sync guard** — an older `captureDate` arriving after a newer active is filed into `discarded[]` without demoting the active ("newest = active").
- **optionalExtra label** — a supplied `label` (≤100) is persisted **only for `unitType==='optionalExtra'`** (installer-named spare photos); fixed matrix labels on other unit types are never overwritten by the client.
- Updates unit status (Not Started → In Progress → Completed by mandatory basis) and task status, then `maybeAdvancePhotoStatus` (only while status ∈ `{nomination_signed, photos_started}`; excludes optionalExtra; first → `photos_started`, all mandatory → `photos_complete`). Records `PHOTO_CAPTURED` / `PHOTO_RECAPTURED`.

**Listing / export**
- `GET /jobs/:id/photos` — flat paginated list across tasks (captured-only by default; search over label/user/address/equipment).
- `GET /jobs/:id/all-photos` — grouped by unit type (Final + Discarded) + engagement/nomination signature URLs (`records` unit skipped).
- `GET /jobs/:id/export-photos?type=` — streamed ZIP (`archiver` v8). Default = geotagged images (EXIF written back to S3) + signatures + `photos.csv`; `type=installer` = GPS stripped from the zipped copies, no signatures/CSV. `records` excluded. 10-min timeout. *(Streams — bypasses the response envelope.)*

---

## 16. Notes

Module `src/modules/note`. Entity-scoped — keyed by `entityType` + `entityId` (currently only `job`; site/installer planned). `requireNoteEntityAccess` resolves the entity and reuses that entity's access rules (a job note is gated exactly like its job). Notes soft-delete (`isDeleted`), never physically removed.

| Method / path | Purpose |
|---|---|
| `POST /notes` | Create (comment or evidence request) |
| `GET /notes` | List a thread |
| `GET /notes/:id` · `PATCH /notes/:id` | Detail / update |
| `PATCH /notes/:id/checkbox` | Resolve / re-open an evidence request |
| `DELETE /notes/:id` | Soft delete |

- **Note text is OPTIONAL** — mobile can post an **attachment-only** note. A refine still requires **note text OR ≥1 attachment** (a fully-empty note is rejected: "Provide note text or at least one attachment"); model default `note:''`.
- **Evidence-request states** (`NoteState`): `missing_information`, `certificate_request`, `certificate_request_edit_required`, `cancel_notification`, `notification`, `no_email`. The first three are **actionable** and deliberately move the job **backward** — raise → `missing_evidence`; resolve → `requested_evidence_provided` (first two) / `final_review` (edit-required). Safety net: notes can't move a job at/after `passed_review`. Raising / resolving actionable states is **staff only**. `syncNotesToJobStatus` auto-closes matching open notes when the job advances on its own.
- **Visibility** (`NoteVisibility`): `internal` (staff-only, 404-hidden from installers) / `external` (default, shared with the company). Non-staff list is forced to external.
- **Attachments** — presigned via `POST /storage/presigned-url` (`docType:'note-attachment'`, a secret docType); max 10, 25 MB each; presented with 1h presigned view URLs.

---

## 17. Storage

Module `src/modules/storage`. Private S3, all access via presigned URLs.

| Method / path | Purpose |
|---|---|
| `POST /storage/presigned-url` | Presigned PUT → `{presigned_url, public_link, filename}` (TTL 5 min) |
| `POST /storage/view-url` | Presigned GET (inline) |
| `POST /storage/download-url` | Presigned GET (attachment) |
| `POST /storage/download/image` | Fetch one image, per-audience geo handling, base64 data URI |
| `DELETE /storage/object` | Delete an object |

- **`download/image`** — non-installer + lat/long → embed geotag, write back to S3, return tagged bytes; `type=installer` → strip GPS from the returned copy (S3 original untouched); non-JPEG passthrough. The `url` field accepts up to 8192 chars (NSW SSO presigned URLs carry a long security token).
- **Key layout:** public `nsw/{env}/{scope}/{refId}/{docType}/{docType}-{ts}-{rand}{ext}`; secret `nsw/{env}/document/{scope}/…`. `StorageScope`: `USER/JOB/INSTALLER/MISC` (MISC needs no refId).
- **Secret prefix** = `document`; any `installer`-scope upload or a `SECRET_DOC_TYPES` docType (incl. `engagement-signature`, `nomination-signature`, `note-attachment`, `certificate`, `invoice`, `electricity-bill`, …) is private. `profile-photo`/`logo` are always public.

---

## 18. Supporting modules

**Unlabel photos** (`src/modules/unlabel-photo`) — when a task's original equipment or indoor-head count changes (or on brand/model change / product delete), captured photos (active + each `discarded[]`) are copied into `UnlabelPhoto` (never deleted; S3 objects stay). `clearTaskPhotoCaptures` then blanks the captures on the TaskPhoto rows without deleting them (keeps the checklist shape). `GET /jobs/:id/unlabel-photos` — paginated, newest-first, `?taskId=`, presigned URLs.

**CMS** (`src/modules/cms`) — versioned content blocks. `CmsCategory`: declaration / legal / help / engagement. `CmsAudience`: installer / customer / public. Seeded blocks include `engagement_letter` (with `{{customerName}}`/`{{equipmentTable}}`/`{{signLink}}` placeholders), `installer_declaration`, `customer_declaration`, `terms_and_conditions`, `privacy_policy`, and help blocks. `GET /cms/by-key/:key` is public (published only); create/update/delete are staff only; a content change bumps `version` and archives the prior state.

**Activity-log** (`common/services/activity-log.service` + `src/modules/activity-log`) — **entity types `User` and `Installer` ONLY, not Job.** Records create/update/delete with field-level `changes` for user + installer + member changes. Job auditing lives entirely in **job-history**. `GET /` is staff only.

**Address** (`src/modules/address`) — Google-Maps-backed, restricted to **Australia + NSW only**; used to geocode the job address. `GET /address/autocomplete?search=` (NSW-filtered predictions) and `GET /address/details?placeId=|address=` (rejects non-NSW; returns the flattened NSW address form + lat/lng).

**Job history** (`src/modules/job-history`) — the job's audit trail. Events: `created, updated, status_changed, engagement_resent, engagement_signed, nomination_sent, nomination_resent, nomination_signed, products_added, product_edited, product_deleted, photo_captured, photo_recaptured, note_added, note_deleted, deleted, restored`. Actor types: `user | customer | system`. `record()` is best-effort (never breaks the job op) and drops no-op updates. `GET /jobs/:id/history` renders each event display-ready (human summary, labelled field changes, actor).

---

## 19. Known code-comment discrepancies

- `nomination.service.ts` — the `sign` docstring says it moves the job to `good_to_go`, but the code correctly advances to `nomination_signed` (documented behaviour above is correct).

*(The earlier `DELETE /jobs` route/validation comments that mentioned a `reason` have been corrected — the endpoint takes only `{ jobIds }`.)*
